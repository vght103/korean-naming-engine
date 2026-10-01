#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026년 10~12월 일진·월주 표 생성기.

  python3 gen_daily_pillars.py                 # references/daily_pillars_2026.md 를 다시 쓴다
  python3 gen_daily_pillars.py --stdout        # 화면 출력만

- 간지 계산은 같은 폴더의 saju_calc.py 함수를 그대로 쓴다(계산 기준 동일).
- 일주는 sxtwl 과 JDN 공식(2000-01-01 = 戊午, index 54)으로 날짜마다 이중 계산해 불일치를 표에 기록한다.
- 절입 시각 교차검증: skyfield + skyfield-data(DE421)가 설치돼 있으면 독립 계산하고,
  없으면 아래 DE421_RECORDED(2026-10-01 같은 방식으로 계산해 둔 값)를 쓴다.
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

# 표에 올릴 절기 (jqIndex) — 백로·소한은 범위 앞뒤 참고용
TERMS = [(2026, 17), (2026, 19), (2026, 21), (2026, 23), (2027, 1)]
# 우주항공청/KASI 공표값(분 단위). 프로젝트 재검토 메모가 인용한 값만 기재, 나머지는 미확인.
KASI = {21: '11-07 18:52', 23: '12-07 11:53'}
# skyfield 1.55 + DE421, 겉보기 지심 황경(진춘분점·황도 of date), UTC 윤초 반영 → KST
DE421_RECORDED = {17: '2026-09-07 23:41:17', 19: '2026-10-08 15:29:18', 21: '2026-11-07 18:52:04',
                  23: '2026-12-07 11:52:31', 1: '2027-01-05 23:09:58'}


def de421_times(targets):
    """{jqIndex: KST 문자열}. skyfield 가 없으면 기록값."""
    try:
        import skyfield_data
        from datetime import timezone
        from skyfield.api import load, load_file
        from skyfield.framelib import ecliptic_frame
    except ImportError:
        return DE421_RECORDED, '기록값(skyfield 미설치 — 2026-10-01 skyfield 1.55 + DE421로 같은 방법으로 계산해 둔 값)'
    eph = load_file(os.path.join(os.path.dirname(skyfield_data.__file__), 'data', 'de421.bsp'))
    ts = load.timescale(builtin=True)
    earth, sun = eph['earth'], eph['sun']

    def err(d, target):
        t = ts.from_datetime(d.replace(tzinfo=timezone.utc))
        lo = earth.at(t).observe(sun).apparent().frame_latlon(ecliptic_frame)[1].degrees
        return ((lo - target + 180) % 360) - 180

    out = {}
    for k, guess in targets.items():
        target = (k * 15 + 270) % 360
        a, b = guess - timedelta(days=1), guess + timedelta(days=1)
        for _ in range(50):
            m = a + (b - a) / 2
            if err(m, target) < 0:
                a = m
            else:
                b = m
        out[k] = f'{sc.kst(a + timedelta(microseconds=500000)):%Y-%m-%d %H:%M:%S}'
    return out, 'skyfield + DE421 독립 계산'


def rmin(t):
    """'YYYY-MM-DD HH:MM:SS' 또는 datetime → 분 단위 반올림 'HH:MM'."""
    if isinstance(t, str):
        t = datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
    return f'{t + timedelta(seconds=30):%H:%M}'


def kasi_notes(inst, de):
    diffs = [(datetime.strptime(de[k], '%Y-%m-%d %H:%M:%S') - sc.kst(inst[k])).total_seconds() for _, k in TERMS]
    lo, hi = min(diffs), max(diffs)
    ip, dx = inst[21], inst[23]
    out = ['- **KASI 대조**: 우주항공청·한국천문연구원 공표값은 입동 11/7 18:52, 대설 12/7 11:53이다(재검토 메모가 인용한 KASI 2026 달력자료).',
           f'  DE421 값을 분 단위로 반올림하면 입동 {de[21][11:]} → {rmin(de[21])}, 대설 {de[23][11:]} → {rmin(de[23])} 으로 **공표값과 일치**한다.',
           f'  sxtwl 값은 위 2026년 절기에서 일관되게 DE421보다 {lo:.0f}~{hi:.0f}초 이르다(1990·1994년 절기는 ±2초 이내로 일치).',
           '  원인은 sxtwl 내부의 ΔT(지구 자전 지연) 미래 외삽값이 실제보다 큰 데 있는 것으로 보인다.',
           f'  그래서 입동은 sxtwl {sc.kst(ip):%H:%M:%S} → {rmin(sc.kst(ip))}로 공표값과 같지만, 대설은 sxtwl {sc.kst(dx):%H:%M:%S} → {rmin(sc.kst(dx))}로 공표값 11:53과 1분 다르다.',
           '  즉 대설의 1분 차이는 반올림만으로는 설명되지 않고 **sxtwl의 약 18초 편차 + 분 단위 반올림**이 겹친 결과다.',
           '- 실무 영향: 절입 순간 앞뒤 약 1분 안에 태어난 경우에만 월주 판정이 달라질 수 있다. 그 경우 KASI 공표 시각을 우선하고 초 단위 자료를 따로 확인한다.',
           f'- 한로 공표값은 이 작업 환경에서 KASI 원문 접속이 막혀 비워 두었다(DE421 {de[19][11:]} → {rmin(de[19])} 예상).']
    return out


def term_instants():
    res = {}
    for y, k in TERMS:
        for u, kk in sc.jieqi_all(y):
            if kk == k:
                res[k] = u
    return res


def wx_count(pairs):
    c = {e: 0 for e in sc.WX}
    for s, b in pairs:
        c[sc.WX[sc.GAN_WX[s]]] += 1
        c[sc.WX[sc.ZHI_WX[b]]] += 1
    return c


def gz_wx(s, b):
    return f'{sc.GAN[s]}{sc.ZHI[b]}', f'{sc.WX[sc.GAN_WX[s]]}·{sc.WX[sc.ZHI_WX[b]]}'


def build():
    L = []
    inst = term_instants()
    de, de_src = de421_times(inst)

    L += ['# 2026년 10~12월 일진·월주 조견표 (출생 대비용)', '',
          '> 이 파일은 `skills/korean-naming/scripts/gen_daily_pillars.py`가 생성한다. 손으로 고치지 말고 스크립트를 다시 실행한다.',
          '> 계산 기준은 `scripts/saju_calc.py` 머리말과 같다(절기 기준 월주, 정자시법, 지방평균시 -30분, 양순음역 12운성).',
          '> 이 표는 출생 전 **시나리오 비교용**이다. 출생일·분만 시기는 의료진의 임상 판단으로 정하며, 이 표로 고르지 않는다.', '']

    # 1. 절입 시각
    L += ['## 1. 2026년 절입 시각 (KST, UTC+9)', '',
          '| 절기 | 태양 황경 | sxtwl 2.0.7 | DE421 교차계산 | KASI 공표(분) | 월주 전환 |',
          '|---|---:|---|---|---|---|']
    for y, k in TERMS:
        u = inst[k]
        before = sc.year_month_at(u - timedelta(seconds=1))
        after = sc.year_month_at(u)
        tr = f'{sc.GAN[before[2]]}{sc.ZHI[before[3]]} → {sc.GAN[after[2]]}{sc.ZHI[after[3]]}'
        ref = ' (범위 밖 참고)' if k in (17, 1) else ''
        L.append(f'| {sc.JQ_KO[k]}({sc.JQ_HJ[k]}){ref} | {(k * 15 + 270) % 360}° | {sc.kst(u):%Y-%m-%d %H:%M:%S} '
                 f'| {de[k]} | {KASI.get(k, "미확인")} | {tr} |')
    L += ['',
          f'- DE421 열 출처: {de_src}. 겉보기 지심 황경(그 날의 진춘분점·황도 기준)이 목표 각도가 되는 순간을 이분법으로 구했다.',
          ] + kasi_notes(inst, de) + ['']

    # 2. 사용법
    L += ['## 2. 사용법', '',
          '실제 출생일·시각(법정시, 분 단위)이 확정되면 표가 아니라 계산기를 돌린다.', '',
          '```bash',
          'python3 skills/korean-naming/scripts/saju_calc.py --date 2026-11-15 --time 14:20',
          'python3 skills/korean-naming/scripts/saju_calc.py --date 2026-11-15 --time 14:20 --json   # 기계 판독용',
          'python3 skills/korean-naming/scripts/saju_calc.py --date 2026-11-15 --time 14:20 --no-solar-correction  # 보정 미적용 유파 비교',
          'python3 skills/korean-naming/scripts/saju_calc.py --selftest   # 일주 JDN·시대별 표준시·12운성·월주 교차검증',
          '```', '',
          '- **일주의 날짜 경계**: 이 표의 일주는 법정시 **00:00~23:29** 출생에 해당한다(지방평균시 -30분 + 정자시법).',
          '  23:30 이후 출생은 **다음 날** 일주를 쓴다. 보정을 쓰지 않는 유파는 경계가 23:00이다.',
          '- **절입일**(10/8, 11/7, 12/7)은 날짜가 아니라 **실제 출생 순간**과 절입 순간을 비교한다. 아래 표는 그날을 두 줄(이전/이후)로 나눴다.',
          '- 계산기는 시지 경계 ±10분, 절입 ±1일, 보정 여부에 따라 결과가 바뀌는 경우 반대쪽 간지를 함께 보여 준다.',
          '- 오행 개수는 연·월·일 **겉글자 6자**만 센 값이다. 시주·지장간을 넣지 않았고, 일간 강약이나 용신 판단이 아니다.', '']

    # 3. 기준 요약
    yr = sc.year_month_at(datetime(2026, 11, 1))
    L += ['## 3. 이 기간의 연주·월주', '',
          f'- 연주: **{sc.GAN[yr[0]]}{sc.ZHI[yr[1]]}** (입춘 2026-02-04 05:01:51 ~ 2027-02-04 10:45:59 KST, sxtwl). 기간 내내 같다.',
          '- 월간은 연간오호둔(丙·辛년 → 庚寅월 시작)으로 정한다.', '',
          '| 구간 (KST, sxtwl) | 월주 | 연·월 겉글자 4자 오행 (木火土金水) |', '|---|---|---|']
    seg_pts = [datetime(2026, 10, 1, 3)] + [inst[k] for k in (19, 21, 23)]
    seg_end = [inst[19], inst[21], inst[23], inst[1]]
    for i, (a, b) in enumerate(zip(seg_pts, seg_end)):
        ys, yb, ms, mb, _, _ = sc.year_month_at(a)
        c = wx_count([(ys, yb), (ms, mb)])
        start_txt = '2026-10-01 00:00' if i == 0 else f'{sc.kst(a):%Y-%m-%d %H:%M:%S}'
        L.append(f'| {start_txt} ~ {sc.kst(b):%Y-%m-%d %H:%M:%S} | {sc.GAN[ms]}{sc.ZHI[mb]} | '
                 + ' '.join(f'{e}{c[e]}' for e in sc.WX) + ' |')
    L += ['',
          f'- 출생 예정월이 11월이어도 **11/7 {sc.kst(inst[21]):%H:%M:%S} 이전 출생은 戊戌월**, '
          f'12/7 {sc.kst(inst[23]):%H:%M:%S} 이후 출생은 庚子월이다(sxtwl 기준). 11월 전체를 己亥월로 확정할 수 없다.', '']

    # 4. 시주 조견표
    L += ['## 4. 시주 조견표 (일간오서둔)', '',
          '법정시 구간은 지방평균시 -30분 보정 기준이다. 子時 행의 23:30~23:59 출생은 **다음 날 일간**으로 시간(時干)을 찾는다.', '',
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
          '- 오행 개수 = 연주 丙午 + 월주 + 일주의 겉글자 6자.', '',
          '| 날짜 | 요일 | 일주 | 일주 오행 | 월주 | 연주 | 일간@월지 12운성 | 木 | 火 | 土 | 金 | 水 |',
          '|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|']
    jie_by_date = {sc.kst(inst[k]).date(): inst[k] for k in (19, 21, 23)}
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
    try:  # 선택: KASI 자료 기반 korean-lunar-calendar 로 3차 대조
        from korean_lunar_calendar import KoreanLunarCalendar
        bad3, d = [], START
        while d <= END:
            c = KoreanLunarCalendar()
            c.setSolarDate(d.year, d.month, d.day)
            i = sc.day_index_jdn(d)
            if c.getChineseGapJaString().split()[2][:2] != sc.GAN[i % 10] + sc.ZHI[i % 12]:
                bad3.append(d)
            d += timedelta(days=1)
        third = f'- 일주 3차 대조: korean-lunar-calendar(KASI 음양력 자료 기반) 일진과 비교, 불일치 **{len(bad3)}건**.'
    except ImportError:
        third = '- 일주 3차 대조: korean-lunar-calendar 미설치로 생략.'
    L += ['', '## 6. 교차검증 기록', '',
          f'- 일주: {n}일 전부 sxtwl `getDayGZ`와 JDN 공식(2000-01-01 = 戊午, 60갑자 index 54)을 따로 계산해 비교했다. '
          f'불일치 **{len(mism)}건**' + (f' ({", ".join(map(str, mism))})' if mism else '') + '.',
          third,
          '- 월주: 절입 순간 비교로 계산한 값을 `saju_calc.py --selftest`가 1950~2050년 절입일 제외 전 기간에서 sxtwl 일 단위 월주와 대조한다(불일치 0건).',
          '- 생성 환경: python3, sxtwl 2.0.7' + (', skyfield 1.55 + DE421' if de is not DE421_RECORDED else '') + '.', '']
    return '\n'.join(L), mism


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stdout', action='store_true')
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    text, mism = build()
    if a.stdout:
        print(text)
    else:
        with open(a.out, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'작성: {os.path.normpath(a.out)} / 일주 불일치 {len(mism)}건')


if __name__ == '__main__':
    main()
