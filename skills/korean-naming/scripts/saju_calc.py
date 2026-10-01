#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사주 결정론 계산기 (python3 + sxtwl) — korean-naming 스킬 전용.

같은 입력이면 언제 누가 실행해도 같은 결과가 나오도록 계산 기준을 아래처럼 고정한다.

사용법
  python3 saju_calc.py --date 2026-11-15 --time 14:20
  python3 saju_calc.py --date 1990-06-27 --time 19:10 --json
  python3 saju_calc.py --date 2026-11-07 --time 18:40 --no-solar-correction
  python3 saju_calc.py --date 2026-11-20            # 시각 미상: 연·월·일주만
  python3 saju_calc.py --selftest                   # 내부 교차검증

계산 기준
1. 입력 시각 = 한국 법정시(출생증명서·벽시계 시각).
   - 시대별 표준시 (IANA tzdb Asia/Seoul 과 동일):
       ~1908-03-31 서울 지방시(UTC+8:27:52) / 1908-04-01 ~ 1911-12-31 UTC+8:30
       1912-01-01 ~ 1954-03-20 UTC+9 / 1954-03-21 ~ 1961-08-09 UTC+8:30 / 1961-08-10 ~ UTC+9
   - 서머타임(시계를 1시간 앞당김 → 입력에서 1시간 뺌). 전환 시각까지 tzdb 기준:
       1948-06-01 00:00 ~ 1948-09-12 24:00, 1949-04-03 00:00 ~ 1949-09-10 24:00,
       1950-04-01 00:00 ~ 1950-09-09 24:00, 1951-05-06 00:00 ~ 1951-09-08 24:00,
       1955-05-05 00:00 ~ 1955-09-08 24:00, 1956-05-20 00:00 ~ 1956-09-29 24:00,
       1957-05-05 00:00 ~ 1957-09-21 24:00, 1958-05-04 00:00 ~ 1958-09-20 24:00,
       1959-05-03 00:00 ~ 1959-09-19 24:00, 1960-05-01 00:00 ~ 1960-09-17 24:00,
       1987-05-10 02:00 ~ 1987-10-11 03:00, 1988-05-08 02:00 ~ 1988-10-09 03:00
     (saju-myeongri 스킬의 날짜 단위 표와 같고, 1987-10-11·1988-10-09 새벽 0~3시만 이 표가 더 정확하다.)
     전환 직후 없는 시각/두 번 있는 시각은 경고하고, 두 번 있는 시각은 서머타임 쪽을 택한다.
   - 위 표로 입력을 UTC(실제 순간)로 바꾼다.
2. 연주·월주 = '실제 순간(UTC)'과 '절입 순간(UTC)'을 비교한다.
   - 절입은 태양 황경이 315°·345°… 가 되는 천문 사건이라 지구 어디서나 같은 순간이다.
     지방시 보정은 '시계를 읽는 법'일 뿐 사건 순간을 바꾸지 않으므로, 보정 전후 어느 시각을
     쓰든 실제 순간끼리 비교해야 일관된다. 출력은 KST(UTC+9)로 표기해 KASI 발표값과 바로 대조한다.
   - 연주 경계 입춘, 월주 경계 12절(소한·입춘·경칩·청명·입하·망종·소서·입추·백로·한로·입동·대설).
   - 월간: 연간오호둔 (甲己→丙寅, 乙庚→戊寅, 丙辛→庚寅, 丁壬→壬寅, 戊癸→甲寅).
3. 일주·시주 = 지방평균시(LMT) 기준. (기본값, --no-solar-correction 으로 끔)
   - LMT = UTC + 경도/15 시간. 기본 경도 127.5°E → UTC+8:30 → KST(UTC+9) 시대에는 '-30분'.
     법정시가 UTC+8:30 이던 시대(1908~1911, 1954-03-21~1961-08-09)는 이미 127.5°E 자오선
     기준이므로 추가 보정 0분이 자동 적용된다. --longitude 로 출생지 경도를 줄 수 있다(서울 126.98).
   - --no-solar-correction: LMT 대신 '서머타임만 뺀 시대별 표준시'로 시지·일 경계를 판단한다.
   - 균시차(진태양시-평균태양시, 연중 -14~+16분)는 적용하지 않는다(통용 관행).
   - 일 경계: 정자시법 — LMT 23:00(子時 시작)에 일주가 다음 날로 바뀐다
     (KST 시대·보정 적용 시 법정시 23:30). 야자시법(23시대 子時를 당일 일주로 보는 법)은 비채택.
   - 시지: LMT 홀수 정시 경계 (23~01 子, 01~03 丑, … 21~23 亥).
   - 시간(時干): 일간오서둔 (甲己→甲子, 乙庚→丙子, 丙辛→戊子, 丁壬→庚子, 戊癸→壬子).
4. 일주 간지는 sxtwl getDayGZ 와 JDN 공식(2000-01-01 = 戊午, 60갑자 index 54)으로 이중 계산하고
   다르면 오류로 종료한다.
5. 12운성: 양순음역(음생양사) 표. 장생지 甲亥 乙午 丙寅 丁酉 戊寅 己酉 庚巳 辛子 壬申 癸卯,
   양간은 순행, 음간은 역행. 출력은 일간 기준(봉법)으로 네 지지에 붙인다.
6. 지장간: 통용 여기·중기·정기표 (子·卯·酉는 중기 없음, 午 중기 己).
7. 경고: 시지 경계 ±10분, 절입 ±1일이면 반대쪽 간지를 함께 표시한다.
   진태양시 보정 여부에 따라 일주·시주가 달라지면 그 값도 표시한다.

한계
- sxtwl 의 절입 시각은 2020년대에 DE421 천체력 대비 약 18초 이르다(ΔT 외삽 차이). 1990년대는 ±2초.
  절입 ±1분 안의 출생은 우주항공청/KASI 월력요항 값으로 다시 확인한다.
- 음력은 sxtwl(중국 음력, UTC+8 기준) 값이다. 합삭이 자정 무렵이면 한국 음력과 하루 다를 수 있다.
- 이 스크립트는 역법 계산만 담당한다. 용신·길흉 해석은 하지 않는다.
"""
import argparse
import json
import sys
from datetime import date, datetime, timedelta

try:
    import sxtwl
except ImportError:  # pragma: no cover
    sys.exit("sxtwl 미설치: pip install sxtwl")

# ── 기본 데이터 ────────────────────────────────────────────────
GAN = '甲乙丙丁戊己庚辛壬癸'
ZHI = '子丑寅卯辰巳午未申酉戌亥'
GAN_KO = '갑을병정무기경신임계'
ZHI_KO = '자축인묘진사오미신유술해'
WX = '木火土金水'
WX_KO = {'木': '목', '火': '화', '土': '토', '金': '금', '水': '수'}
GAN_WX = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]                 # index into WX
ZHI_WX = [4, 2, 0, 0, 2, 1, 1, 2, 3, 3, 2, 4]
ANIMAL = ['쥐', '소', '범', '토끼', '용', '뱀', '말', '양', '원숭이', '닭', '개', '돼지']
WEEKDAY_KO = '월화수목금토일'

# 지장간 (여기, 중기, 정기)
JIJANGGAN = {
    '子': ('壬', None, '癸'), '丑': ('癸', '辛', '己'), '寅': ('戊', '丙', '甲'),
    '卯': ('甲', None, '乙'), '辰': ('乙', '癸', '戊'), '巳': ('戊', '庚', '丙'),
    '午': ('丙', '己', '丁'), '未': ('丁', '乙', '己'), '申': ('戊', '壬', '庚'),
    '酉': ('庚', None, '辛'), '戌': ('辛', '丁', '戊'), '亥': ('戊', '甲', '壬'),
}

# 12운성 (양순음역)
STAGES = ['장생', '목욕', '관대', '건록', '제왕', '쇠', '병', '사', '묘', '절', '태', '양']
CHANGSAENG = {'甲': '亥', '乙': '午', '丙': '寅', '丁': '酉', '戊': '寅',
              '己': '酉', '庚': '巳', '辛': '子', '壬': '申', '癸': '卯'}

# 합·충 데이터
CHEONGAN_HAP = {frozenset('甲己'): '土', frozenset('乙庚'): '金', frozenset('丙辛'): '水',
                frozenset('丁壬'): '木', frozenset('戊癸'): '火'}
CHEONGAN_CHUNG = [frozenset('甲庚'), frozenset('乙辛'), frozenset('丙壬'), frozenset('丁癸')]
JIJI_YUKHAP = {frozenset('子丑'): '土', frozenset('寅亥'): '木', frozenset('卯戌'): '火',
               frozenset('辰酉'): '金', frozenset('巳申'): '水', frozenset('午未'): '火(일설 土)'}
JIJI_SAMHAP = [('申子辰', '水'), ('亥卯未', '木'), ('寅午戌', '火'), ('巳酉丑', '金')]  # 가운데 글자 = 왕지
JIJI_CHUNG = [frozenset(p) for p in ('子午', '丑未', '寅申', '卯酉', '辰戌', '巳亥')]

# 24절기 (sxtwl jqIndex 순서: 0=동지)
JQ_HJ = ['冬至', '小寒', '大寒', '立春', '雨水', '驚蟄', '春分', '淸明', '穀雨', '立夏', '小滿', '芒種',
         '夏至', '小暑', '大暑', '立秋', '處暑', '白露', '秋分', '寒露', '霜降', '立冬', '小雪', '大雪']
JQ_KO = ['동지', '소한', '대한', '입춘', '우수', '경칩', '춘분', '청명', '곡우', '입하', '소만', '망종',
         '하지', '소서', '대서', '입추', '처서', '백로', '추분', '한로', '상강', '입동', '소설', '대설']

# ── 한국 법정시 → UTC ───────────────────────────────────────────
H = 3600
STD_ERAS = [  # (UTC 시작, 표준시 오프셋 초)
    (datetime(1908, 3, 31, 15, 32, 8), 8 * H + 30 * 60),
    (datetime(1911, 12, 31, 15, 30), 9 * H),
    (datetime(1954, 3, 20, 15, 0), 8 * H + 30 * 60),
    (datetime(1961, 8, 9, 15, 30), 9 * H),
]
PRE_1908 = 8 * H + 27 * 60 + 52  # 서울 지방평균시
DST_UTC = [  # 서머타임 구간 [시작, 끝) — UTC
    (datetime(1948, 5, 31, 15), datetime(1948, 9, 12, 14)),
    (datetime(1949, 4, 2, 15), datetime(1949, 9, 10, 14)),
    (datetime(1950, 3, 31, 15), datetime(1950, 9, 9, 14)),
    (datetime(1951, 5, 5, 15), datetime(1951, 9, 8, 14)),
    (datetime(1955, 5, 4, 15, 30), datetime(1955, 9, 8, 14, 30)),
    (datetime(1956, 5, 19, 15, 30), datetime(1956, 9, 29, 14, 30)),
    (datetime(1957, 5, 4, 15, 30), datetime(1957, 9, 21, 14, 30)),
    (datetime(1958, 5, 3, 15, 30), datetime(1958, 9, 20, 14, 30)),
    (datetime(1959, 5, 2, 15, 30), datetime(1959, 9, 19, 14, 30)),
    (datetime(1960, 4, 30, 15, 30), datetime(1960, 9, 17, 14, 30)),
    (datetime(1987, 5, 9, 17), datetime(1987, 10, 10, 17)),
    (datetime(1988, 5, 7, 17), datetime(1988, 10, 8, 17)),
]


def offset_at(u):
    """UTC 순간 u 의 (표준시 오프셋, 서머타임 오프셋) 초."""
    std = PRE_1908
    for start, off in STD_ERAS:
        if u >= start:
            std = off
    dst = H if any(a <= u < b for a, b in DST_UTC) else 0
    return std, dst


def civil_to_utc(civil):
    """한국 법정시(naive) → (UTC, 표준오프셋, 서머타임오프셋, 경고목록)."""
    warns, cands = [], []
    for total in sorted({PRE_1908, 8 * H + 30 * 60, 9 * H, 9 * H + 30 * 60, 10 * H}):
        u = civil - timedelta(seconds=total)
        std, dst = offset_at(u)
        if std + dst == total:
            cands.append((u, std, dst))
    if not cands:  # 시계를 앞당겨 생긴 '없는 시각'
        std, dst = offset_at(civil - timedelta(hours=12))
        u = civil - timedelta(seconds=std + dst)
        warns.append(f'입력 시각은 시간대 전환으로 실제로 존재하지 않는 법정시입니다. 전환 전 시간대({fmt_off(std + dst)})로 해석했습니다.')
        return u, std, dst, warns
    if len(cands) > 1:  # 시계를 되돌려 '두 번 있는 시각'
        cands.sort(key=lambda c: c[0])
        warns.append('입력 시각은 시간대 전환으로 두 번 존재합니다. 앞쪽(전환 전) 순간으로 계산했습니다. '
                     f'뒤쪽이면 UTC {cands[-1][0]:%Y-%m-%d %H:%M} 입니다.')
    if civil < datetime(1908, 4, 1):
        warns.append('1908년 이전 입력은 서울 지방평균시(UTC+8:27:52) 시계로 간주했습니다.')
    return cands[0] + (warns,)


def fmt_off(sec):
    sign = '+' if sec >= 0 else '-'
    sec = abs(sec)
    return f'UTC{sign}{sec // H:02d}:{(sec % H) // 60:02d}' + (f':{sec % 60:02d}' if sec % 60 else '')


def kst(u):
    """UTC → KST(UTC+9) 표기용 datetime."""
    return u + timedelta(hours=9)


# ── 절입 ─────────────────────────────────────────────────────
def jd_to_utc(jd):
    """sxtwl jd(베이징시 UTC+8 기준 율리우스일) → UTC datetime(초 단위 반올림)."""
    d = datetime(2000, 1, 1, 12) + timedelta(days=jd - 2451545.0) - timedelta(hours=8)
    return (d + timedelta(microseconds=500000)).replace(microsecond=0)


_JIE_CACHE = {}


def jie_list(year):
    """year-1 ~ year+1 의 12절(節) [(UTC, jqIndex)] 정렬 목록."""
    if year not in _JIE_CACHE:
        seen = {}
        for y in (year - 1, year, year + 1):
            for j in sxtwl.getJieQiByYear(y):
                if j.jqIndex % 2 == 1:
                    seen[round(j.jd, 5)] = (jd_to_utc(j.jd), j.jqIndex)
        _JIE_CACHE[year] = sorted(seen.values())
    return _JIE_CACHE[year]


def jieqi_all(year):
    """해당 양력 연도(KST)의 24절기 전체 [(UTC, jqIndex)]."""
    seen = {}
    for y in (year - 1, year):
        for j in sxtwl.getJieQiByYear(y):
            u = jd_to_utc(j.jd)
            if kst(u).year == year:
                seen[round(j.jd, 5)] = (u, j.jqIndex)
    return sorted(seen.values())


def month_branch_of_jie(k):
    return ((k - 3) // 2 + 2) % 12


def gz_index(stem, branch):
    return (6 * stem - 5 * branch) % 60


def year_month_at(u):
    """실제 순간 u(UTC) → (연간, 연지, 월간, 월지, 직전절, 다음절)."""
    jl = jie_list(u.year)
    prev = [j for j in jl if j[0] <= u][-1]
    nxt = [j for j in jl if j[0] > u][0]
    lichun = [j for j in jl if j[1] == 3 and j[0] <= u][-1]
    y = kst(lichun[0]).year
    ys, yb = (y - 4) % 10, (y - 4) % 12
    mb = month_branch_of_jie(prev[1])
    ms = ((ys % 5) * 2 + 2 + (mb - 2) % 12) % 10
    return ys, yb, ms, mb, prev, nxt


# ── 일주 ─────────────────────────────────────────────────────
def day_index_jdn(d):
    """JDN 공식: 2000-01-01(JDN 2451545) = 戊午(54)."""
    return (54 + d.toordinal() + 1721425 - 2451545) % 60


def day_index_sxtwl(d):
    g = sxtwl.fromSolar(d.year, d.month, d.day).getDayGZ()
    return gz_index(g.tg, g.dz)


def day_index(d):
    a, b = day_index_sxtwl(d), day_index_jdn(d)
    if a != b:
        raise RuntimeError(f'일주 불일치 {d}: sxtwl={GAN[a % 10]}{ZHI[a % 12]} JDN={GAN[b % 10]}{ZHI[b % 12]}')
    return a


# ── 해석용 조회 ───────────────────────────────────────────────
def unseong(stem, branch):
    s, b, start = GAN.index(stem), ZHI.index(branch), ZHI.index(CHANGSAENG[stem])
    return STAGES[(b - start) % 12 if s % 2 == 0 else (start - b) % 12]


def sibsin(day_stem, other_stem):
    d, o = GAN.index(day_stem), GAN.index(other_stem)
    rel = (GAN_WX[o] - GAN_WX[d]) % 5
    names = [('비견', '겁재'), ('식신', '상관'), ('편재', '정재'), ('편관', '정관'), ('편인', '정인')][rel]
    return names[0] if d % 2 == o % 2 else names[1]


def relations(pillars):
    """pillars: [(이름, 천간, 지지)] → 천간합·천간충·육합·삼합(반합)·충 목록."""
    out = []
    n = len(pillars)
    for i in range(n):
        for j in range(i + 1, n):
            (a, sa, ba), (b, sb, bb) = pillars[i], pillars[j]
            ps, pb = frozenset(sa + sb), frozenset(ba + bb)
            if ps in CHEONGAN_HAP:
                out.append(f'천간합 {a}{sa}·{b}{sb} → {CHEONGAN_HAP[ps]}')
            if ps in CHEONGAN_CHUNG:
                out.append(f'천간충 {a}{sa}·{b}{sb}')
            if pb in JIJI_YUKHAP:
                out.append(f'지지육합 {a}{ba}·{b}{bb} → {JIJI_YUKHAP[pb]}')
            if pb in JIJI_CHUNG:
                out.append(f'지지충 {a}{ba}·{b}{bb}')
    branches = {p[2] for p in pillars}
    for trio, el in JIJI_SAMHAP:
        have = [c for c in trio if c in branches]
        if len(have) == 3:
            out.append(f'삼합 {trio} → {el}국')
        elif len(have) == 2 and trio[1] in have:
            out.append(f'반합 {"".join(have)} → {el} (삼합 {trio} 중 두 글자)')
    return out


def stem_info(s, day_stem, is_day=False):
    i = GAN.index(s)
    return {'자': s, '한글': GAN_KO[i], '오행': WX[GAN_WX[i]], '음양': '양' if i % 2 == 0 else '음',
            '십신': '일원(본인)' if is_day else sibsin(day_stem, s)}


def branch_info(b, day_stem):
    i = ZHI.index(b)
    jj = JIJANGGAN[b]
    return {'자': b, '한글': ZHI_KO[i], '오행': WX[ZHI_WX[i]], '띠': ANIMAL[i],
            '십신(정기)': sibsin(day_stem, jj[2]),
            '지장간': {k: (None if g is None else {'자': g, '오행': WX[GAN_WX[GAN.index(g)]],
                                                   '십신': sibsin(day_stem, g)})
                     for k, g in zip(('여기', '중기', '정기'), jj)},
            '12운성(일간기준)': unseong(day_stem, b)}


# ── 핵심 계산 ─────────────────────────────────────────────────
def compute_core(u, std, correction=True, longitude=127.5, time_known=True, civil_date=None):
    """실제 순간 u(UTC) → 간지 인덱스와 판단 근거. time_known=False 이면 civil_date 의 일주만."""
    ys, yb, ms, mb, prev, nxt = year_month_at(u)
    if time_known:
        lmt = u + (timedelta(hours=longitude / 15) if correction else timedelta(seconds=std))
        ref = lmt.date() + timedelta(days=1) if lmt.hour >= 23 else lmt.date()
    else:
        lmt, ref = None, civil_date
    di = day_index(ref)
    ds = di % 10
    res = {'u': u, 'lmt': lmt, 'day_ref': ref, 'prev': prev, 'next': nxt,
           'year': (ys, yb), 'month': (ms, mb), 'day': (ds, di % 12), 'hour': None}
    if time_known:
        sec = lmt.hour * H + lmt.minute * 60 + lmt.second
        hb = ((sec + H) // (2 * H)) % 12
        hs = ((ds % 5) * 2 + hb) % 10
        res['hour'] = (hs, hb)
        res['sec_into_branch'] = (sec + H) % (2 * H)
    return res


def gz(p):
    return GAN[p[0]] + ZHI[p[1]]


def pillars_str(c):
    order = [('시', c['hour']), ('일', c['day']), ('월', c['month']), ('연', c['year'])]
    return ' '.join(f'{k}{gz(v)}' for k, v in order if v is not None)


def compute(date_str, time_str=None, correction=True, longitude=127.5):
    y, m, d = map(int, date_str.split('-'))
    warns, alts = [], []
    time_known = time_str is not None
    if time_known:
        hh, mi = map(int, time_str.split(':'))
        civil = datetime(y, m, d, hh, mi)
    else:
        civil = datetime(y, m, d, 12, 0)
    u, std, dst, w = civil_to_utc(civil)
    warns += w
    core = compute_core(u, std, correction, longitude, time_known, civil.date())

    ds = GAN[core['day'][0]]
    names = [('연주', core['year']), ('월주', core['month']), ('일주', core['day']), ('시주', core['hour'])]
    saju = {}
    for nm, p in names:
        if p is None:
            continue
        s, b = GAN[p[0]], ZHI[p[1]]
        saju[nm] = {'간지': s + b, '한글': GAN_KO[p[0]] + ZHI_KO[p[1]],
                    '천간': stem_info(s, ds, nm == '일주'), '지지': branch_info(b, ds)}

    count = {e: 0 for e in WX}
    for nm, p in names:
        if p is not None:
            count[WX[GAN_WX[p[0]]]] += 1
            count[WX[ZHI_WX[p[1]]]] += 1

    rel = relations([(nm[0], GAN[p[0]], ZHI[p[1]]) for nm, p in names if p is not None])

    # 절입 ±1일
    for tag, j in (('직전', core['prev']), ('다음', core['next'])):
        delta = (u - j[0]) if tag == '직전' else (j[0] - u)
        if (not time_known and kst(j[0]).date() == civil.date()) or (time_known and delta <= timedelta(days=1)):
            other = j[0] - timedelta(seconds=1) if tag == '직전' else j[0]
            ys2, yb2, ms2, mb2, _, _ = year_month_at(other)
            h_, rem = divmod(int(delta.total_seconds()), H)
            side = '후' if tag == '직전' else '전'
            msg = (f'{JQ_KO[j[1]]}({JQ_HJ[j[1]]}) 절입 {kst(j[0]):%Y-%m-%d %H:%M:%S} KST'
                   + (f' — 출생은 절입 {h_}시간 {rem // 60}분 {rem % 60}초 {side}' if time_known else ' — 출생일이 절입일, 시각 필요')
                   + f'. 절입 반대편이면 월주 {GAN[ms2]}{ZHI[mb2]}'
                   + (f', 연주 {GAN[ys2]}{ZHI[yb2]}' if (ys2, yb2) != core['year'] else '') + '.')
            warns.append(msg)
            if time_known and delta <= timedelta(minutes=2):
                warns.append('절입 2분 이내 출생: sxtwl 절입 시각은 초 단위 오차가 있다(2020년대 DE421 대비 약 18초 이름). '
                             'KASI/우주항공청 공표 시각과 초 단위 자료로 월주를 재확인할 것.')
            alts.append({'사유': f'{JQ_KO[j[1]]} 절입 반대편', '월주': GAN[ms2] + ZHI[mb2],
                         '연주': GAN[ys2] + ZHI[yb2]})

    if time_known:
        # 시지 경계 ±10분
        r = core['sec_into_branch']
        shift = None
        if r < 600:
            shift = -(r + 60)
        elif 2 * H - r <= 600:
            shift = (2 * H - r) + 60
        if shift is not None:
            alt = compute_core(u + timedelta(seconds=shift), std, correction, longitude)
            warns.append(f'시지 경계 ±10분 이내(LMT {core["lmt"]:%H:%M:%S}). 인접 시진이면 {pillars_str(alt)}.')
            alts.append({'사유': '시지 경계 반대편', '사주': pillars_str(alt)})
        # 보정 on/off 비교
        other = compute_core(u, std, not correction, longitude)
        if (other['day'], other['hour']) != (core['day'], core['hour']):
            lab = '진태양시 보정 미적용' if correction else '진태양시 보정 적용'
            warns.append(f'{lab} 시에는 {pillars_str(other)} (시지/일 경계 기준 시계가 달라짐).')
            alts.append({'사유': lab, '사주': pillars_str(other)})
    else:
        warns.append('출생 시각 미상: 시주 없음. 법정시 23:30 이후 출생이면(보정 적용 시) 일주가 다음 날 것으로 바뀝니다.')

    lday = sxtwl.fromSolar(y, m, d)
    lunar = f'{lday.getLunarYear()}년 ' + ('윤' if lday.isLunarLeap() else '') + \
            f'{lday.getLunarMonth()}월 {lday.getLunarDay()}일'

    out = {
        '입력': {'법정시': f'{date_str} {time_str}' if time_known else f'{date_str} (시각 미상)',
               '시간대': fmt_off(std + dst) + (' (서머타임 +1h 포함)' if dst else ''),
               '진태양시보정': (f'적용 (경도 {longitude}°E, 지방평균시 = UTC{longitude / 15:+.4f}h)'
                          if correction else '미적용 (서머타임만 뺀 표준시 사용)')},
        '환산': {'UTC': f'{u:%Y-%m-%d %H:%M}', 'KST(UTC+9) 표기': f'{kst(u):%Y-%m-%d %H:%M}'},
        '음력(sxtwl)': lunar,
        '절기': {'직전 절': f'{JQ_KO[core["prev"][1]]}({JQ_HJ[core["prev"][1]]}) {kst(core["prev"][0]):%Y-%m-%d %H:%M:%S} KST',
               '다음 절': f'{JQ_KO[core["next"][1]]}({JQ_HJ[core["next"][1]]}) {kst(core["next"][0]):%Y-%m-%d %H:%M:%S} KST'},
        '사주': saju,
        '일간': stem_info(ds, ds, True),
        '겉글자 오행 개수': count,
        '합충': rel or ['없음'],
        '경고': warns,
        '대안': alts,
    }
    if time_known:
        lmt = core['lmt']
        diff = int(round((lmt - civil).total_seconds() / 60))
        out['환산']['시지·일경계 판단 시각'] = f'{lmt:%Y-%m-%d %H:%M:%S} (입력 대비 {diff:+d}분)'
        out['환산']['일주 기준 날짜'] = f'{core["day_ref"]}'
    return out


# ── 출력 ─────────────────────────────────────────────────────
def render_text(r):
    L = []
    for k, v in r['입력'].items():
        L.append(f'{k}: {v}')
    for k, v in r['환산'].items():
        L.append(f'{k}: {v}')
    L.append(f'음력(sxtwl): {r["음력(sxtwl)"]}')
    for k, v in r['절기'].items():
        L.append(f'{k}: {v}')
    L.append('')
    P = r['사주']
    for c in ('연주', '월주', '일주', '시주'):
        if c not in P:
            continue
        st, br = P[c]['천간'], P[c]['지지']
        jj = '·'.join(f"{x['자']}({x['십신']})" for x in br['지장간'].values() if x)
        L.append(f"{c} {P[c]['간지']}({P[c]['한글']}) | 천간 {st['자']} {st['오행']}{st['음양']} {st['십신']}"
                 f" | 지지 {br['자']} {br['오행']} {br['십신(정기)']} | 지장간 {jj} | 12운성 {br['12운성(일간기준)']}")
    L.append('')
    L.append('겉글자 오행: ' + ' '.join(f'{k}{v}' for k, v in r['겉글자 오행 개수'].items()))
    L.append('합충: ' + ', '.join(r['합충']))
    for wmsg in r['경고']:
        L.append('[주의] ' + wmsg)
    return '\n'.join(L)


# ── 자체 검증 ─────────────────────────────────────────────────
def selftest():
    ok = True
    # 1) JDN vs sxtwl 일주 1900~2100
    d, bad = date(1900, 1, 1), 0
    while d <= date(2100, 12, 31):
        if day_index_sxtwl(d) != day_index_jdn(d):
            bad += 1
        d += timedelta(days=1)
    print(f'[1] 일주 JDN vs sxtwl 1900-2100: 불일치 {bad}건')
    ok &= bad == 0
    # 2) 법정시 표 vs zoneinfo(Asia/Seoul)
    try:
        from zoneinfo import ZoneInfo
        from datetime import timezone
        z = ZoneInfo('Asia/Seoul')
        t, bad = datetime(1908, 4, 1), 0
        while t < datetime(2030, 1, 1):
            std, dst = offset_at(t)
            if int(t.replace(tzinfo=timezone.utc).astimezone(z).utcoffset().total_seconds()) != std + dst:
                bad += 1
            t += timedelta(minutes=30)
        print(f'[2] 시대별 오프셋 vs zoneinfo 1908-2030(30분 간격): 불일치 {bad}건')
        ok &= bad == 0
    except Exception as e:  # pragma: no cover
        print('[2] zoneinfo 비교 생략:', e)
    # 3) 12운성 표본
    samples = {('甲', '亥'): '장생', ('甲', '午'): '사', ('丙', '寅'): '장생', ('丙', '巳'): '건록',
               ('丙', '午'): '제왕', ('癸', '卯'): '장생', ('癸', '子'): '건록', ('癸', '午'): '절',
               ('乙', '午'): '장생', ('庚', '子'): '사'}
    bad = [k for k, v in samples.items() if unseong(*k) != v]
    print(f'[3] 12운성 표본 {len(samples)}건: 불일치 {bad}')
    ok &= not bad
    # 4) 월주·연주 vs sxtwl (절입일 제외, 1950~2050 정오)
    d, bad, n = date(1950, 1, 1), 0, 0
    while d <= date(2050, 12, 31):
        u = datetime(d.year, d.month, d.day, 3)  # KST 정오
        ys, yb, ms, mb, prev, nxt = year_month_at(u)
        # sxtwl 일 단위 월주는 베이징시(UTC+8) 날짜로 바뀌므로 KST·베이징 어느 쪽이든 절입일이면 제외
        jdays = {(j[0] + timedelta(hours=h)).date() for j in (prev, nxt) for h in (8, 9)}
        if d not in jdays:
            day = sxtwl.fromSolar(d.year, d.month, d.day)
            mg, yg = day.getMonthGZ(), day.getYearGZ()
            n += 1
            if (mg.tg, mg.dz) != (ms, mb) or (yg.tg, yg.dz) != (ys, yb):
                bad += 1
        d += timedelta(days=1)
    print(f'[4] 연·월주 vs sxtwl 일 단위 값(KST·베이징 절입일 제외 {n}일): 불일치 {bad}건')
    ok &= bad == 0
    print('결과:', '통과' if ok else '실패')
    return ok


def main():
    ap = argparse.ArgumentParser(description='사주 결정론 계산기 (한국 법정시 입력)')
    ap.add_argument('--date', help='양력 YYYY-MM-DD')
    ap.add_argument('--time', help='법정시 HH:MM (모르면 생략)')
    ap.add_argument('--no-solar-correction', action='store_true', help='지방평균시 보정 끔')
    ap.add_argument('--longitude', type=float, default=127.5, help='출생지 경도(기본 127.5 → -30분)')
    ap.add_argument('--json', action='store_true', help='JSON 출력')
    ap.add_argument('--selftest', action='store_true', help='내부 교차검증 실행')
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not a.date:
        ap.error('--date 필요')
    r = compute(a.date, a.time, not a.no_solar_correction, a.longitude)
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else render_text(r))


if __name__ == '__main__':
    main()
