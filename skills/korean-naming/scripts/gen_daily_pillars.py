#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026년 10~12월 일진·월주 표 생성기.

  python3 gen_daily_pillars.py                 # references/daily_pillars_2026.md 를 다시 쓴다
  python3 gen_daily_pillars.py --stdout        # 화면 출력만

- 간지·절입 계산은 같은 폴더의 saju_calc.py 함수를 그대로 쓴다(계산 기준 동일).
  절입 순간은 saju_calc 의 정밀 계산원(기본 pyerfa)을 쓰고, 월주 구간 경계도 이 값으로 자른다.
- 일주는 sxtwl 과 JDN 공식(2000-01-01 = 戊午, index 54)으로 날짜마다 이중 계산해 불일치를 표에 기록한다.
  korean_lunar_calendar(KASI 자료)가 있으면 일진을 3차 대조한다.
- 절입 시각 교차검증: skyfield + skyfield-data(DE421)가 설치돼 있으면 독립 계산하고,
  없으면 아래 DE421_RECORDED(2026-10-01 같은 방식으로 계산해 둔 값)를 쓴다.
- 입춘(연주 경계) 범위, sxtwl 편차, 진태양시 차이 등 본문 수치는 모두 실행 때 계산한다.
"""
import argparse
import os
import sys
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import saju_calc as sc  # noqa: E402

START, END = date(2026, 10, 1), date(2026, 12, 31)
OUT = os.path.join(HERE, '..', 'references', 'daily_pillars_2026.md')

# 표에 올릴 절기 (양력 연도, jqIndex). 입춘은 연주 경계, 백로·소한은 범위 앞뒤 참고용
TERMS = [(2026, 3), (2026, 17), (2026, 19), (2026, 21), (2026, 23), (2027, 1), (2027, 3)]
IN_RANGE = {(2026, 19), (2026, 21), (2026, 23)}
# 우주항공청/KASI 공표값(분 단위). 프로젝트 재검토 메모·facts.md 가 출처를 확인한 값만 기재, 나머지는 미확인.
KASI = {(2026, 21): '18:52', (2026, 23): '11:53'}
# skyfield 1.55 + DE421, 겉보기 지심 황경(진춘분점·황도 of date), UTC 윤초 반영 → KST(0.1초)
DE421_RECORDED = {(2026, 3): '2026-02-04 05:02:07.9', (2026, 17): '2026-09-07 23:41:17.2',
                  (2026, 19): '2026-10-08 15:29:17.5', (2026, 21): '2026-11-07 18:52:04.3',
                  (2026, 23): '2026-12-07 11:52:31.5', (2027, 1): '2027-01-05 23:09:57.9',
                  (2027, 3): '2027-02-04 10:46:18.3'}


def pkg_version(name):
    try:
        from importlib.metadata import version
        return version(name)
    except Exception:
        return None


def de421_times():
    """{(연도, jqIndex): KST datetime}, 출처 설명. skyfield 가 없으면 기록값."""
    if sc._skyfield_ctx() is None:
        rec = {k: datetime.strptime(v, '%Y-%m-%d %H:%M:%S.%f') for k, v in DE421_RECORDED.items()}
        return rec, '기록값(skyfield 미설치 — 2026-10-01 skyfield 1.55 + DE421로 같은 방법으로 계산해 둔 값)', False
    out = {key: sc.kst(sc.term_instant_raw(key[0], key[1], 'skyfield')) for key in TERMS}
    return out, 'skyfield + DE421 독립 계산', True


def hms1(t):
    """datetime → 'HH:MM:SS.s' (0.1초 반올림)."""
    t = t + timedelta(microseconds=50000)
    return f'{t:%H:%M:%S}.{t.microsecond // 100000}'


def wx_count(pairs):
    c = {e: 0 for e in sc.WX}
    for s, b in pairs:
        c[sc.WX[sc.GAN_WX[s]]] += 1
        c[sc.WX[sc.ZHI_WX[b]]] += 1
    return c


def gz_wx(s, b):
    return f'{sc.GAN[s]}{sc.ZHI[b]}', f'{sc.WX[sc.GAN_WX[s]]}·{sc.WX[sc.ZHI_WX[b]]}'


def tst_offsets(longitude=127.5):
    """대표 날짜 KST 정오의 (진태양시 − KST) 분. pyerfa 없으면 빈 목록."""
    out = []
    if sc.erfa is None:
        return out
    for m, d in ((10, 1), (11, 1), (11, 15), (11, 22), (11, 30), (12, 15), (12, 31)):
        u = datetime(2026, m, d, 3)
        eot = sc.equation_of_time(u)
        out.append((f'{m}/{d}', longitude * 4 - 9 * 60 + eot / 60))
    return out


def build():
    L = []
    src = sc.jie_source()
    inst = {key: sc.term_instant(*key) for key in TERMS}              # UTC, 초 반올림 — 판정에 쓰는 값
    raw = {key: sc.term_instant_raw(key[0], key[1], src) for key in TERMS}
    sx = {key: sc.sxtwl_term_instant(*key) for key in TERMS}
    de, de_src, de_live = de421_times()
    de_diff = {key: (de[key] - sc.kst(raw[key])).total_seconds() for key in TERMS}
    sx_diff = {key: (sx[key] - raw[key]).total_seconds() for key in TERMS}

    L += ['# 2026년 10~12월 일진·월주 조견표 (출생 대비용)', '',
          '> 이 파일은 `skills/korean-naming/scripts/gen_daily_pillars.py`가 생성한다. 손으로 고치지 말고 스크립트를 다시 실행한다.',
          '> 계산 기준은 `scripts/saju_calc.py` 머리말과 같다(절입 순간 기준 연·월주, 정자시법, 지방평균시(경도) -30분 보정, 양순음역 12운성).',
          f'> 절입 순간: {sc.JIE_LABEL[src]} 정밀 계산값(초 단위 반올림)으로 월주 구간을 자른다.',
          '> 이 표는 출생 전 **시나리오 비교용**이다. 출생일·분만 시기는 의료진의 임상 판단으로 정하며, 이 표로 고르지 않는다.', '']

    # 1. 절입 시각
    L += ['## 1. 2026년 절입 시각 (KST, UTC+9)', '',
          '| 절기 | 태양 황경 | 정밀 계산 (판정값) | 분 반올림 | KASI 공표(분) | DE421 교차계산 | sxtwl 2.0.7 (정밀값 대비) | 월주 전환 |',
          '|---|---:|---|---|---|---|---|---|']
    for key in TERMS:
        y, k = key
        u = inst[key]
        before = sc.year_month_at(u - timedelta(seconds=1))
        after = sc.year_month_at(u)
        tr = f'{sc.GAN[before[2]]}{sc.ZHI[before[3]]} → {sc.GAN[after[2]]}{sc.ZHI[after[3]]}'
        if (before[0], before[1]) != (after[0], after[1]):
            tr += f' (연주 {sc.GAN[before[0]]}{sc.ZHI[before[1]]} → {sc.GAN[after[0]]}{sc.ZHI[after[1]]})'
        if key in IN_RANGE:
            ref = ''
        elif k == 3:
            ref = ' (연주 경계, 참고)'
        else:
            ref = ' (범위 밖 참고)'
        L.append(f'| {sc.JQ_KO[k]}({sc.JQ_HJ[k]}){ref} | {(k * 15 + 270) % 360}° | **{sc.kst(u):%Y-%m-%d %H:%M:%S}** '
                 f'| {sc.kasi_minute(u)} | {KASI.get(key, "미확인")} | {hms1(de[key])} ({de_diff[key]:+.1f}초) '
                 f'| {sc.kst(sx[key]):%H:%M:%S} ({sx_diff[key]:+.0f}초) | {tr} |')
    kasi_ok = [key for key in KASI if sc.kasi_minute(inst[key]) == KASI[key]]
    rng26 = [sx_diff[key] for key in sorted(IN_RANGE)]
    sx_all26 = [(sc.sxtwl_term_instant(2026, k) - sc.term_instant_raw(2026, k, src)).total_seconds()
                for k in range(1, 24, 2)]
    ip, dx = (2026, 21), (2026, 23)
    L += ['',
          f'- **정밀 계산(판정값)**: {sc.JIE_LABEL[src]}. 태양 겉보기 지심 황경(그 날의 진춘분점·진황도 기준)이 '
          '목표 각도가 되는 순간을 뉴턴법으로 구하고, TT→UTC 변환은 ERFA 윤초표(2026년 TT−UTC 69.184초)를 쓴 뒤 초 단위로 반올림했다. '
          '`saju_calc.py`와 이 표의 월주 경계는 모두 이 값이다.',
          f'- **DE421 열**: {de_src}. 괄호는 정밀 계산(반올림 전)과의 차이로, 위 절기들에서 최대 '
          f'{max(abs(v) for v in de_diff.values()):.1f}초다.',
          f'- **KASI 대조**: 우주항공청·한국천문연구원 공표값은 입동 11/7 18:52, 대설 12/7 11:53이다(재검토 메모가 인용한 KASI 2026 달력자료). '
          f'정밀 계산값 입동 {sc.kst(inst[ip]):%H:%M:%S} → {sc.kasi_minute(inst[ip])}, 대설 {sc.kst(inst[dx]):%H:%M:%S} → '
          f'{sc.kasi_minute(inst[dx])} 으로 분 반올림하면 **공표값과 일치**한다({len(kasi_ok)}/{len(KASI)}건).',
          f'- **sxtwl 편차**: sxtwl 값은 2026년 12절 전체에서 정밀 계산보다 {-max(sx_all26):.0f}~{-min(sx_all26):.0f}초 이르다'
          f'(위 표의 10~12월 세 절기는 {-max(rng26):.0f}~{-min(rng26):.0f}초). 원인은 sxtwl 내부 ΔT(지구 자전 지연)의 미래 외삽이다. '
          '같은 대조에서 1900~2009년 절기는 ±3초 이내로 맞는다(`saju_calc.py --selftest` [7]). '
          f'그래서 대설은 sxtwl {sc.kst(sx[dx]):%H:%M:%S} → {sc.kasi_minute(sx[dx])}로 공표값 {KASI[dx]}과 1분 다르게 나온다. '
          '이 표의 이전 판(2026-10-01 초판)은 sxtwl 값으로 구간을 잘랐으나 지금은 정밀 계산값으로 바꿨다.',
          '- **실무 영향**: 절입 순간 앞뒤 약 1분 안에 태어난 경우에만 월주 판정이 달라질 수 있다. 공표값은 분 단위 반올림이므로 '
          '같은 분 안의 출생은 위 초 단위 정밀값으로 판정하고, 출생 기록 시각 자체의 정확도도 함께 확인한다.',
          f'- 한로·입춘·백로·소한 공표값은 이 작업 환경에서 KASI 원문 접속이 막혀 "미확인"으로 두었다'
          f'(정밀 계산 분 반올림: 한로 {sc.kasi_minute(inst[(2026, 19)])}, 입춘 2026 {sc.kasi_minute(inst[(2026, 3)])}, '
          f'입춘 2027 {sc.kasi_minute(inst[(2027, 3)])}).', '']

    # 2. 사용법
    tso = tst_offsets()
    tso_txt = ', '.join(f'{d} {v:+.0f}분' for d, v in tso)
    L += ['## 2. 사용법', '',
          '실제 출생일·시각(법정시, 분 단위 — 초를 알면 초까지)이 확정되면 표가 아니라 계산기를 돌린다.', '',
          '```bash',
          'python3 skills/korean-naming/scripts/saju_calc.py --date 2026-11-15 --time 14:20',
          'python3 skills/korean-naming/scripts/saju_calc.py --date 2026-11-07 --time 18:52:10   # 절입 부근은 초까지',
          'python3 skills/korean-naming/scripts/saju_calc.py --date 2026-11-15 --time 14:20 --json   # 기계 판독용',
          'python3 skills/korean-naming/scripts/saju_calc.py --date 2026-11-15 --time 14:20 --no-lmt-correction  # 경도 보정 미적용 유파 비교',
          'python3 skills/korean-naming/scripts/saju_calc.py --selftest   # 일주·표준시·12운성·월주·절입 정밀값·음력 교차검증',
          '```', '',
          '- **일주의 날짜 경계(정자시법)**: 이 표의 일주는 법정시 **00:00~23:29** 출생에 해당한다(지방평균시 -30분 + 子時 시작에 날짜 변경).',
          '  23:30 이후 출생은 **다음 날** 일주를 쓴다. 경도 보정을 쓰지 않는 유파는 경계가 23:00이다.',
          '- **야자시법**(子時 앞 절반 = 지방평균시 23:00~23:59, 법정시 23:30~00:29를 당일 일주로 보는 유파)도 있다. '
          '이 구간 출생이면 계산기가 "야자시법" 대안(전날 일주 유지)을 함께 보여 준다. 유파가 갈리므로 하나로 단정하지 않는다.',
          '- **균시차 미적용**: -30분은 경도(127.5°E)만 반영한 지방평균시 보정이다. 해의 실제 위치로 잰 진태양시는 날짜마다 다르며, '
          + (f'127.5°E 기준 KST 대비 {tso_txt}이다(pyerfa 계산). 11월 상·중순은 약 KST -14~16분으로 일괄 -30분과 14~16분 차이가 난다. '
             if tso else '11월 상·중순 127.5°E 기준 약 KST -14~16분이다. ')
          + '계산기는 출생 순간의 진태양시를 참고값으로 보여 주고, 그 기준이면 시주가 바뀌는 경우 대안으로 표시한다(채택하지 않음).',
          '- **절입일**(10/8, 11/7, 12/7)은 날짜가 아니라 **실제 출생 순간**과 절입 순간(초 단위)을 비교한다. 아래 표는 그날을 두 줄(이전/이후)로 나눴다.',
          '- 계산기는 시지 경계 ±10분, 절입 ±1일, 경도 보정 여부, 야자시 구간, 진태양시(참고)에 따라 결과가 바뀌는 경우 반대쪽 간지를 함께 보여 준다.',
          '- 오행 개수는 연·월·일 **겉글자 6자**만 센 값이다. 시주·지장간을 넣지 않았고, 일간 강약이나 용신 판단이 아니다.', '']

    # 3. 기준 요약
    yr = sc.year_month_at(datetime(2026, 11, 1))
    lc26, lc27 = inst[(2026, 3)], inst[(2027, 3)]
    L += ['## 3. 이 기간의 연주·월주', '',
          f'- 연주: **{sc.GAN[yr[0]]}{sc.ZHI[yr[1]]}** (입춘 {sc.kst(lc26):%Y-%m-%d %H:%M:%S} ~ {sc.kst(lc27):%Y-%m-%d %H:%M:%S} KST, '
          f'분 반올림 {sc.kst(lc26):%m-%d} {sc.kasi_minute(lc26)} ~ {sc.kst(lc27):%m-%d} {sc.kasi_minute(lc27)}, 정밀 계산). 기간 내내 같다.',
          '- 월간은 연간오호둔(丙·辛년 → 庚寅월 시작)으로 정한다.',
          '- 구간은 "시작 순간 이상 ~ 끝 순간 미만"이다. 절입 순간(초)부터 새 월주다.', '',
          '| 구간 (KST, 정밀 계산 초 단위) | 분 반올림(KASI식) | 월주 | 연·월 겉글자 4자 오행 (木火土金水) |', '|---|---|---|---|']
    seg_pts = [datetime(2026, 9, 30, 15)] + [inst[(2026, k)] for k in (19, 21, 23)]
    seg_end = [inst[(2026, 19)], inst[(2026, 21)], inst[(2026, 23)], inst[(2027, 1)]]
    for i, (a, b) in enumerate(zip(seg_pts, seg_end)):
        ys, yb, ms, mb, _, _ = sc.year_month_at(a)
        c = wx_count([(ys, yb), (ms, mb)])
        start_txt = '2026-10-01 00:00:00' if i == 0 else f'{sc.kst(a):%Y-%m-%d %H:%M:%S}'
        start_min = '10-01 00:00' if i == 0 else f'{sc.kst(a):%m-%d} {sc.kasi_minute(a)}'
        L.append(f'| {start_txt} ~ {sc.kst(b):%Y-%m-%d %H:%M:%S} | {start_min} ~ {sc.kst(b):%m-%d} {sc.kasi_minute(b)} '
                 f'| {sc.GAN[ms]}{sc.ZHI[mb]} | ' + ' '.join(f'{e}{c[e]}' for e in sc.WX) + ' |')
    L += ['',
          f'- 출생 예정월이 11월이어도 **11/7 {sc.kst(inst[ip]):%H:%M:%S} 이전 출생은 戊戌월**, '
          f'12/7 {sc.kst(inst[dx]):%H:%M:%S} 이후 출생은 庚子월이다(정밀 계산; KASI 분 단위 {KASI[ip]}·{KASI[dx]}). '
          '11월 전체를 己亥월로 확정할 수 없다.', '']

    # 4. 시주 조견표
    L += ['## 4. 시주 조견표 (일간오서둔)', '',
          '법정시 구간은 지방평균시(경도) -30분 보정 기준이다. 子時 행의 23:30~23:59 출생은 정자시법으로 **다음 날 일간**으로 시간(時干)을 찾는다'
          '(야자시법은 일주를 당일로 두며 시간 처리도 유파마다 다르다 — 계산기 대안 참조).', '',
          '| 시지 | 법정시(보정 적용) | 보정 미적용 | 甲·己일 | 乙·庚일 | 丙·辛일 | 丁·壬일 | 戊·癸일 |',
          '|---|---|---|---|---|---|---|---|']
    for hb in range(12):
        st = (hb * 2 - 1) % 24
        a1 = f'{(st) % 24:02d}:30~{(st + 2) % 24:02d}:29'
        a0 = f'{st:02d}:00~{(st + 1) % 24:02d}:59'
        cells = [f'{sc.GAN[((d % 5) * 2 + hb) % 10]}{sc.ZHI[hb]}' for d in range(5)]
        L.append(f'| {sc.ZHI[hb]} | {a1} | {a0} | ' + ' | '.join(cells) + ' |')
    L.append('')

    # 5. 일별 표
    L += ['## 5. 일별 표 (2026-10-01 ~ 2026-12-31)', '',
          '- 일주 오행 = 천간·지지 오행. 12운성 = 일간을 월지에 붙인 값(양순음역).',
          '- 오행 개수 = 연주 丙午 + 월주 + 일주의 겉글자 6자.',
          '- 절입일 두 줄의 시각은 정밀 계산 절입 순간(KST, 초)이다.', '',
          '| 날짜 | 요일 | 일주 | 일주 오행 | 월주 | 연주 | 일간@월지 12운성 | 木 | 火 | 土 | 金 | 水 |',
          '|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|']
    jie_by_date = {sc.kst(inst[(2026, k)]).date(): inst[(2026, k)] for k in (19, 21, 23)}
    mism = []
    d = START
    while d <= END:
        di_s, di_j = sc.day_index_sxtwl(d), sc.day_index_jdn(d)
        if di_s != di_j:
            mism.append(d)
        ds, db = di_s % 10, di_s % 12
        dgz, dwx = gz_wx(ds, db)
        wd = sc.WEEKDAY_KO[d.weekday()]
        if d in jie_by_date:
            j = jie_by_date[d]
            parts = [('이전', j - timedelta(seconds=1)), ('이후', j)]
            label = f'{sc.kst(j):%H:%M:%S}'
        else:
            parts = [(None, datetime(d.year, d.month, d.day, 3))]  # KST 정오
        for tag, u in parts:
            ys, yb, ms, mb, _, _ = sc.year_month_at(u)
            c = wx_count([(ys, yb), (ms, mb), (ds, db)])
            us = sc.unseong(sc.GAN[ds], sc.ZHI[mb])
            dcell = f'{d:%m-%d}' if tag is None else f'**{d:%m-%d} 절입 {label} {tag}**'
            mcell = f'{sc.GAN[ms]}{sc.ZHI[mb]}' if tag is None else f'**{sc.GAN[ms]}{sc.ZHI[mb]}**'
            L.append(f'| {dcell} | {wd} | {dgz} | {dwx} | {mcell} | {sc.GAN[ys]}{sc.ZHI[yb]} | {us} | '
                     + ' | '.join(str(c[e]) for e in sc.WX) + ' |')
        d += timedelta(days=1)
    n = (END - START).days + 1
    if sc.KoreanLunarCalendar is not None:  # KASI 자료 기반 korean-lunar-calendar 로 3차 대조
        bad3, d = [], START
        while d <= END:
            c = sc.KoreanLunarCalendar()
            c.setSolarDate(d.year, d.month, d.day)
            i = sc.day_index_jdn(d)
            if c.getChineseGapJaString().split()[2][:2] != sc.GAN[i % 10] + sc.ZHI[i % 12]:
                bad3.append(d)
            d += timedelta(days=1)
        third = f'- 일주 3차 대조: korean-lunar-calendar(KASI 음양력 자료 기반) 일진과 비교, 불일치 **{len(bad3)}건**.'
    else:
        third = '- 일주 3차 대조: korean-lunar-calendar 미설치로 생략.'
    if sc.KoreanLunarCalendar is not None:  # 한국 음력(KASI) vs sxtwl(중국 음력) 날짜 차이
        ldiff, d = [], START
        while d <= END:
            c = sc.KoreanLunarCalendar()
            c.setSolarDate(d.year, d.month, d.day)
            x = sc.sxtwl.fromSolar(d.year, d.month, d.day)
            if (c.lunarMonth, c.lunarDay, bool(c.isIntercalation)) != (x.getLunarMonth(), x.getLunarDay(), bool(x.isLunarLeap())):
                ldiff.append(d)
            d += timedelta(days=1)
        span = f'{ldiff[0]} ~ {ldiff[-1]} ({len(ldiff)}일)' if ldiff else '없음'
        lunar_note = (f'- 음력(참고): 이 기간 한국 음력(korean_lunar_calendar, KASI 자료)과 sxtwl(중국 음력, UTC+8)이 다른 날짜: {span}. '
                      '합삭 순간이 한국 자정과 중국 자정 사이에 들어 음력 초하루가 하루 갈린 결과다. `saju_calc.py`는 한국 음력을 쓴다.')
    else:
        lunar_note = '- 음력(참고): korean_lunar_calendar 미설치로 한국·중국 음력 대조 생략.'
    # 월주 경계 점검: 각 절입 순간 1초 전/정각의 월주가 바뀌는지
    seg_ok = all(sc.year_month_at(inst[key] - timedelta(seconds=1))[3] != sc.year_month_at(inst[key])[3] for key in TERMS)
    env = ', '.join(f'{p} {v}' for p, v in (('sxtwl', pkg_version('sxtwl')), ('pyerfa', pkg_version('pyerfa')),
                                             ('korean_lunar_calendar', pkg_version('korean_lunar_calendar')),
                                             ('skyfield', pkg_version('skyfield') if de_live else None)) if v)
    L += ['', '## 6. 교차검증 기록', '',
          f'- 일주: {n}일 전부 sxtwl `getDayGZ`와 JDN 공식(2000-01-01 = 戊午, 60갑자 index 54)을 따로 계산해 비교했다. '
          f'불일치 **{len(mism)}건**' + (f' ({", ".join(map(str, mism))})' if mism else '') + '.',
          third,
          f'- 절입: 정밀 계산({src})과 DE421({"독립 계산" if de_live else "기록값"})의 차이 최대 '
          f'**{max(abs(v) for v in de_diff.values()):.1f}초**({len(TERMS)}개 절기). KASI 공표(분)와 분 반올림 일치 '
          f'**{len(kasi_ok)}/{len(KASI)}건**. 월주 구간 경계는 정밀 계산 절입 순간에서 바뀐다(점검 {"통과" if seg_ok else "실패"}).',
          '- 월주: 절입 순간 비교로 계산한 값을 `saju_calc.py --selftest`가 1950~2050년 절입일 앞뒤 하루를 뺀 전 기간에서 '
          'sxtwl 일 단위 월주와 대조한다(불일치 0건). 같은 selftest가 2026 한로·입동·대설 정밀값(DE421 ±2초, 분 반올림)과 '
          'pyerfa↔DE421 차이(최대 2초 이내)를 검사한다.',
          lunar_note,
          f'- 생성 환경: python3, {env}.', '']
    return '\n'.join(L), mism


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stdout', action='store_true')
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    sc.set_jie_source('auto')
    text, mism = build()
    if a.stdout:
        print(text)
    else:
        with open(a.out, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'작성: {os.path.normpath(a.out)} / 일주 불일치 {len(mism)}건 / 절입 계산원 {sc.jie_source()}')


if __name__ == '__main__':
    main()
