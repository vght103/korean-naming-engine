#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사주 결정론 계산기 (python3 + pyerfa + sxtwl + korean_lunar_calendar) — korean-naming 스킬 전용.

같은 입력이면 언제 누가 실행해도 같은 결과가 나오도록 계산 기준을 아래처럼 고정한다.
의존 패키지와 버전은 같은 폴더의 requirements.txt 에 있다.

사용법
  python3 saju_calc.py --date 2026-11-15 --time 14:20
  python3 saju_calc.py --date 2026-11-07 --time 18:52:10        # 초까지 입력 가능
  python3 saju_calc.py --date 1990-06-27 --time 19:10 --json
  python3 saju_calc.py --date 2026-11-07 --time 18:40 --no-lmt-correction
  python3 saju_calc.py --date 2026-11-20            # 시각 미상: 연·월·일주만
  python3 saju_calc.py --selftest                   # 내부 교차검증
  python3 saju_calc.py --date 2026-11-07 --time 18:52 --jie-source sxtwl   # 절입 계산원 비교용

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
   - 절입은 태양 겉보기 지심 황경(그 날의 진춘분점·황도 기준)이 315°·345°… 가 되는 천문 사건이라
     지구 어디서나 같은 순간이다. 지방시 보정은 '시계를 읽는 법'일 뿐 사건 순간을 바꾸지 않으므로
     실제 순간끼리 비교한다. 출력은 KST(UTC+9)로 표기해 KASI 발표값(분 단위, 반올림)과 바로 대조한다.
   - 절입 순간 계산원(우선순위, --jie-source 로 강제 가능):
       ① pyerfa (IAU SOFA 모델: 지구 위치 epv00, 세차·장동 IAU 2006/2000A, 광행차) — 기본값.
       ② skyfield + DE421 (천체력 파일이 로컬에 있을 때만).
       ③ sxtwl — 위 둘이 없을 때만 쓰고 경고한다. sxtwl 은 ΔT(지구 자전 지연)를 미래로 외삽해
          2010년대 이후 절입을 점점 이르게 낸다(아래 SXTWL_BIAS_BY_DECADE, pyerfa 대조 실측).
   - 시간 척도: 1960년 이후는 UTC(윤초표, ERFA dat) → TAI → TT. 윤초표가 끝난 뒤의 연도는 새 윤초가
     없다고 가정한다(2026년 TT−UTC = 69.184초). 1960년 이전은 법정시의 기준이 세계시(UT)이므로
     Espenak·Meeus(2006) ΔT 다항식으로 TT = UT + ΔT 를 쓴다.
   - 정밀도: pyerfa 값과 skyfield+DE421 값의 차이는 2026년 절기에서 0.3초 이내, 1910~2050년 표본 연도
     전체에서 약 1초 이내다(--selftest [6]; 1972년 이전은 두 쪽 ΔT 모형 차이 포함).
     입동 2026-11-07 18:52:04, 대설 12-07 11:52:31 KST → 분 반올림 18:52·11:53 으로 KASI 공표값과 같다.
     절입 순간은 초 단위로 반올림해 저장·비교한다.
   - 연주 경계 입춘, 월주 경계 12절(소한·입춘·경칩·청명·입하·망종·소서·입추·백로·한로·입동·대설).
   - 월간: 연간오호둔 (甲己→丙寅, 乙庚→戊寅, 丙辛→庚寅, 丁壬→壬寅, 戊癸→甲寅).
3. 일주·시주 = 지방평균시(LMT, 경도 보정) 기준. (기본값, --no-lmt-correction 으로 끔)
   - LMT = UTC + 경도/15 시간. 기본 경도 127.5°E → UTC+8:30 → KST(UTC+9) 시대에는 '-30분'.
     법정시가 UTC+8:30 이던 시대(1908~1911, 1954-03-21~1961-08-09)는 이미 127.5°E 자오선
     기준이므로 추가 보정 0분이 자동 적용된다(서머타임 기간에는 서머타임 1시간만 빠진다).
     --longitude 로 출생지 경도를 줄 수 있다(서울 126.98).
   - --no-lmt-correction(옛 이름 --no-solar-correction): LMT 대신 '서머타임만 뺀 시대별 표준시'로
     시지·일 경계를 판단한다.
   - 균시차(진태양시 − 평균태양시)는 적용하지 않는다(통용 관행). 진태양시는 날짜에 따라 지방평균시와
     −14~+16분 다르다. 예: 11월 상·중순 127.5°E 진태양시 ≈ KST −14~16분(30분 일괄 보정과 약 14~16분 차이).
     계산기는 출생 순간의 진태양시를 pyerfa 로 계산해 '참고'로 보여 주고, 그 기준이면 시주·일주가
     달라지는 경우 대안으로 표시한다(채택하지 않음).
   - 일 경계: 정자시법 — LMT 23:00(子時 시작)에 일주가 다음 날로 바뀐다
     (KST 시대·보정 적용 시 법정시 23:30). 야자시법(LMT 23:00~23:59 = 夜子時를 당일 일주로 보는 법)은
     비채택이지만 유파가 갈리므로 해당 구간 출생이면 '대안'으로 함께 보여 준다.
   - 시지: LMT 홀수 정시 경계 (23~01 子, 01~03 丑, … 21~23 亥).
   - 시간(時干): 일간오서둔 (甲己→甲子, 乙庚→丙子, 丙辛→戊子, 丁壬→庚子, 戊癸→壬子).
4. 일주 간지는 sxtwl getDayGZ 와 JDN 공식(2000-01-01 = 戊午, 60갑자 index 54)으로 이중 계산하고
   다르면 오류로 종료한다.
5. 음력: korean_lunar_calendar(한국천문연구원 KASI 음양력 자료 기반, 1000-02-13 ~ 2050-12-31)를 쓴다.
   미설치·범위 밖이면 sxtwl(중국 음력, UTC+8 기준)로 대신하고 경고한다. 합삭이 한국 자정과 중국 자정
   사이에 들면 두 음력은 하루 다르다(예: 2026-10-10 ~ 11-08 은 sxtwl 이 하루 늦게 센다).
6. 12운성: 양순음역(음생양사) 표. 장생지 甲亥 乙午 丙寅 丁酉 戊寅 己酉 庚巳 辛子 壬申 癸卯,
   양간은 순행, 음간은 역행. 출력은 일간 기준(봉법)으로 네 지지에 붙인다.
7. 지장간: 통용 여기·중기·정기표 (子·卯·酉는 중기 없음, 午 중기 己).
8. 경고: 시지 경계 ±10분, 절입 ±1일이면 반대쪽 간지를 함께 표시한다.
   지방평균시(경도) 보정 여부, 야자시법, 진태양시(참고)에 따라 일주·시주가 달라지면 그 값도 표시한다.

한계
- 절입 ±2초 안의 출생은 계산 모델·시간 척도 차이로 판정이 갈릴 수 있다. KASI 공표값은 분 단위
  반올림이라 같은 분 안의 출생은 초 단위 계산값으로 판정한다.
- 1960년 이전 절입은 ΔT 다항식 오차(수 초)가 더해진다.
- 이 스크립트는 역법 계산만 담당한다. 용신·길흉 해석은 하지 않는다.
"""
import argparse
import json
import math
import os
import sys
import warnings
from datetime import date, datetime, timedelta

try:
    import sxtwl
except ImportError:  # pragma: no cover
    sys.exit('sxtwl 미설치: pip install -r requirements.txt')

try:
    import erfa  # pyerfa
except ImportError:  # pragma: no cover
    erfa = None

try:
    from korean_lunar_calendar import KoreanLunarCalendar
except ImportError:  # pragma: no cover
    KoreanLunarCalendar = None

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
# 각 절기가 드는 대략의 양력 날짜(같은 해). 정밀 계산의 초기값으로만 쓴다(실제와 ±2일 이내).
JQ_APPROX = [(12, 22), (1, 6), (1, 20), (2, 4), (2, 19), (3, 6), (3, 21), (4, 5), (4, 20), (5, 6), (5, 21),
             (6, 6), (6, 21), (7, 7), (7, 23), (8, 8), (8, 23), (9, 8), (9, 23), (10, 8), (10, 23), (11, 7),
             (11, 22), (12, 7)]

# sxtwl 2.0.7 절기 시각 − pyerfa 정밀값(초), 1900~2050년 12절 전체 대조 실측(2026-10-01).
# 음수 = sxtwl 이 이르다. 2010년대부터 sxtwl 의 ΔT 미래 외삽 때문에 편차가 커진다.
SXTWL_BIAS_BY_DECADE = {
    1900: (-1.5, 2.3), 1910: (-1.6, 2.1), 1920: (-1.3, 1.4), 1930: (-2.4, 2.3), 1940: (-1.2, 2.3),
    1950: (-1.4, 2.4), 1960: (-1.4, 2.3), 1970: (-1.7, 2.5), 1980: (-1.8, 1.6), 1990: (-1.3, 2.1),
    2000: (-1.6, 2.3), 2010: (-7.7, 1.2), 2020: (-22.9, -7.1), 2030: (-39.6, -22.9),
    2040: (-56.5, -38.3), 2050: (-58.7, -54.4),
}

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


def fmt_hms(sec):
    """하루 안의 초 → 'HH:MM' 또는 'HH:MM:SS'."""
    sec = int(round(sec)) % (24 * H)
    h, rem = divmod(sec, H)
    m, s = divmod(rem, 60)
    return f'{h:02d}:{m:02d}' + (f':{s:02d}' if s else '')


def kst(u):
    """UTC → KST(UTC+9) 표기용 datetime."""
    return u + timedelta(hours=9)


def round_sec(t):
    return (t + timedelta(microseconds=500000)).replace(microsecond=0)


def kasi_minute(u):
    """UTC 순간 → KASI 공표 방식(KST, 분 단위 반올림) 'HH:MM'."""
    return f'{kst(u) + timedelta(seconds=30):%H:%M}'


# ── 시간 척도 (UTC ↔ TT) ───────────────────────────────────────
def delta_t_poly(y):
    """Espenak & Meeus (2006) ΔT = TT − UT 다항식(초). 1960년 이전 변환에만 쓴다."""
    if y < 1800:
        u = (y - 1820) / 100
        return -20 + 32 * u * u
    if y < 1860:
        t = y - 1800
        return (13.72 - 0.332447 * t + 0.0068612 * t ** 2 + 0.0041116 * t ** 3 - 0.00037436 * t ** 4
                + 0.0000121272 * t ** 5 - 0.0000001699 * t ** 6 + 0.000000000875 * t ** 7)
    if y < 1900:
        t = y - 1860
        return 7.62 + 0.5737 * t - 0.251754 * t ** 2 + 0.01680668 * t ** 3 - 0.0004473624 * t ** 4 + t ** 5 / 233174
    if y < 1920:
        t = y - 1900
        return -2.79 + 1.494119 * t - 0.0598939 * t ** 2 + 0.0061966 * t ** 3 - 0.000197 * t ** 4
    if y < 1941:
        t = y - 1920
        return 21.20 + 0.84493 * t - 0.076100 * t ** 2 + 0.0020936 * t ** 3
    t = y - 1950
    return 29.07 + 0.407 * t - t ** 2 / 233 + t ** 3 / 2547


def _dec_year(dt):
    return dt.year + (dt.timetuple().tm_yday - 0.5) / 365.25


UTC_ERFA_FROM = datetime(1960, 1, 1)


def utc_to_tt(dt):
    """UTC(1960 이전은 UT) datetime → TT 2-part JD."""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', erfa.ErfaWarning)  # 윤초표 이후 연도의 'dubious year' 경고
        if dt >= UTC_ERFA_FROM:
            u1, u2 = erfa.dtf2d('UTC', dt.year, dt.month, dt.day, dt.hour, dt.minute,
                                dt.second + dt.microsecond / 1e6)
            return erfa.taitt(*erfa.utctai(u1, u2))
    j1, j2 = erfa.cal2jd(dt.year, dt.month, dt.day)
    frac = (dt.hour * H + dt.minute * 60 + dt.second + dt.microsecond / 1e6) / 86400
    return j1, j2 + frac + delta_t_poly(_dec_year(dt)) / 86400


def tt_to_utc(t1, t2):
    """TT 2-part JD → UTC(1960 이전은 UT) datetime(마이크로초)."""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', erfa.ErfaWarning)
        u1, u2 = erfa.taiutc(*erfa.tttai(t1, t2))
        iy, im, idd, f = erfa.d2dtf('UTC', 6, u1, u2)
    if iy >= 1960:
        hh, mm, ss, us = (int(x) for x in f)
        return datetime(int(iy), int(im), int(idd), hh, mm, ss, us)
    tt = datetime(2000, 1, 1, 12) + timedelta(days=(t1 - 2451545.0) + t2)
    ut = tt - timedelta(seconds=delta_t_poly(_dec_year(tt)))
    return tt - timedelta(seconds=delta_t_poly(_dec_year(ut)))


# ── 태양 겉보기 황경 (pyerfa) ─────────────────────────────────────
def sun_apparent(t1, t2):
    """TT → (겉보기 지심 황경°, 겉보기 적경 rad). 진춘분점·진황도(그 날) 기준.
    지구 일심·질량중심 위치 epv00, 광행차 ab(지구 질량중심 속도), 세차·장동 pn06a(IAU 2006/2000A)."""
    pvh, pvb = erfa.epv00(t1, t2)
    p = [-pvh[0][i] for i in range(3)]           # 지구→태양 (au)
    r = math.sqrt(sum(x * x for x in p))
    v = [pvb[1][i] / erfa.DC for i in range(3)]  # 지구 질량중심 속도 / c
    bm1 = math.sqrt(1 - sum(x * x for x in v))
    ppr = erfa.ab([x / r for x in p], v, r, bm1)
    _dpsi, deps, epsa, _rb, _rp, _rbp, _rn, rbpn = erfa.pn06a(t1, t2)
    q = [sum(rbpn[i][j] * ppr[j] for j in range(3)) for i in range(3)]
    eps = epsa + deps                            # 진황도 경사
    y = q[1] * math.cos(eps) + q[2] * math.sin(eps)
    return math.degrees(math.atan2(y, q[0])) % 360, math.atan2(q[1], q[0])


def _wrap180(x):
    return ((x + 180) % 360) - 180


def _erfa_crossing(target, guess_utc):
    t1, t2 = utc_to_tt(guess_utc)
    lon, _ = sun_apparent(t1, t2)
    lon_b, _ = sun_apparent(t1, t2 + 0.01)
    rate = _wrap180(lon_b - lon) / 0.01           # °/일
    for _ in range(30):
        f = _wrap180(lon - target)
        step = -f / rate
        t2 += step
        if abs(step) < 1e-9:                     # 약 0.1 ms
            break
        lon, _ = sun_apparent(t1, t2)
    return tt_to_utc(t1, t2)


_SF = {}


def _skyfield_ctx():
    """skyfield + 로컬 DE421 이 있으면 (ts, earth, sun, ecliptic_frame). 없으면 None. 내려받지 않는다."""
    if 'ctx' in _SF:
        return _SF['ctx']
    ctx = None
    try:
        from skyfield.api import load, load_file
        from skyfield.framelib import ecliptic_frame
        paths = []
        try:
            import skyfield_data
            paths.append(os.path.join(os.path.dirname(skyfield_data.__file__), 'data', 'de421.bsp'))
        except ImportError:
            pass
        paths += [os.path.join(os.getcwd(), 'de421.bsp'), os.path.expanduser('~/.skyfield/de421.bsp')]
        path = next((p for p in paths if os.path.exists(p)), None)
        if path:
            eph = load_file(path)
            ctx = (load.timescale(builtin=True), eph['earth'], eph['sun'], ecliptic_frame)
    except Exception:  # pragma: no cover
        ctx = None
    _SF['ctx'] = ctx
    return ctx


def skyfield_sun_lon(u):
    """UTC(1972 이전은 UT로 간주) datetime → skyfield+DE421 겉보기 황경°. 없으면 None."""
    ctx = _skyfield_ctx()
    if ctx is None:
        return None
    ts, earth, sun, ecl = ctx
    sec = u.second + u.microsecond / 1e6
    t = (ts.utc if u.year >= 1972 else ts.ut1)(u.year, u.month, u.day, u.hour, u.minute, sec)
    return earth.at(t).observe(sun).apparent().frame_latlon(ecl)[1].degrees


def _skyfield_crossing(target, guess_utc):
    u = guess_utc
    lon = skyfield_sun_lon(u)
    rate = _wrap180(skyfield_sun_lon(u + timedelta(minutes=15)) - lon) / 900  # °/초
    for _ in range(30):
        step = -_wrap180(lon - target) / rate
        u += timedelta(seconds=step)
        if abs(step) < 1e-3:
            break
        lon = skyfield_sun_lon(u)
    return u


def _sxtwl_jd_to_utc(jd):
    """sxtwl jd(베이징시 UTC+8 기준 율리우스일) → UTC datetime."""
    return datetime(2000, 1, 1, 12) + timedelta(days=jd - 2451545.0) - timedelta(hours=8)


_SXTWL_YEAR = {}


def sxtwl_term_instant(year, k):
    """sxtwl 값 그대로의 절기 순간(UTC, 초 반올림). 비교·대체용."""
    guess = datetime(year, *JQ_APPROX[k])
    best = None
    for y in (year - 1, year):
        if y not in _SXTWL_YEAR:
            _SXTWL_YEAR[y] = [(_sxtwl_jd_to_utc(j.jd), j.jqIndex) for j in sxtwl.getJieQiByYear(y)]
        for u, kk in _SXTWL_YEAR[y]:
            if kk == k and abs((u - guess).days) < 20:
                best = u
    return round_sec(best)


# ── 절입 계산원 선택 ─────────────────────────────────────────────
JIE_LABEL = {
    'pyerfa': 'pyerfa(IAU SOFA: epv00 + IAU 2006/2000A 세차·장동 + 광행차)',
    'skyfield': 'skyfield + DE421',
    'sxtwl': 'sxtwl 2.0.7 (ΔT 외삽 오차 있음)',
}
_JIE = {'source': None}


def jie_source_ok(name):
    if name == 'pyerfa':
        return erfa is not None
    if name == 'skyfield':
        return _skyfield_ctx() is not None
    return name == 'sxtwl'


def set_jie_source(name='auto'):
    if name in (None, 'auto'):
        name = next(n for n in ('pyerfa', 'skyfield', 'sxtwl') if jie_source_ok(n))
    elif not jie_source_ok(name):
        raise SystemExit(f'절입 계산원 {name} 을(를) 쓸 수 없습니다(pyerfa 또는 skyfield+로컬 DE421 필요).')
    if name != _JIE['source']:
        _JIE['source'] = name
        _TERM_CACHE.clear()
        _JIE_CACHE.clear()
    return name


def jie_source():
    return _JIE['source'] or set_jie_source('auto')


_TERM_CACHE = {}


def term_instant_raw(year, k, source):
    """반올림 전 절기 순간(UTC, 마이크로초). source = 'pyerfa' | 'skyfield' | 'sxtwl'."""
    if source == 'sxtwl':
        return sxtwl_term_instant(year, k)
    target = (k * 15 + 270) % 360
    if source == 'skyfield':
        return _skyfield_crossing(target, sxtwl_term_instant(year, k))
    return _erfa_crossing(target, datetime(year, *JQ_APPROX[k]))


def term_instant(year, k, source=None):
    """year 년(양력)에 드는 절기 k(0=동지 … 23=대설)의 순간. UTC datetime, 초 반올림."""
    src = source or jie_source()
    key = (src, year, k)
    if key not in _TERM_CACHE:
        _TERM_CACHE[key] = round_sec(term_instant_raw(year, k, src))
    return _TERM_CACHE[key]


_JIE_CACHE = {}


def jie_list(year):
    """year-1 ~ year+1 의 12절(節) [(UTC, jqIndex)] 정렬 목록."""
    if year not in _JIE_CACHE:
        _JIE_CACHE[year] = sorted((term_instant(y, k), k) for y in (year - 1, year, year + 1)
                                  for k in range(1, 24, 2))
    return _JIE_CACHE[year]


def jieqi_all(year):
    """해당 양력 연도(KST)의 24절기 전체 [(UTC, jqIndex)]."""
    out = [(term_instant(y, k), k) for y in (year - 1, year, year + 1) for k in range(24)]
    return sorted(x for x in out if kst(x[0]).year == year)


def sxtwl_bias_text(year):
    """연대별 sxtwl 편차 설명(실측표 기반)."""
    dec = max(min((year // 10) * 10, 2050), 1900)
    lo, hi = SXTWL_BIAS_BY_DECADE[dec]
    era = f'{dec}년대' if 1900 <= year <= 2059 else f'{dec}년대(가장 가까운 실측 구간)'
    if hi <= 0:
        return f'sxtwl 절입 시각은 {era}에 정밀 계산보다 약 {-hi:.0f}~{-lo:.0f}초 이르다(ΔT 미래 외삽, pyerfa 대조 실측).'
    return f'sxtwl 절입 시각은 {era}에 정밀 계산과 {lo:+.0f}~{hi:+.0f}초 범위에서 맞는다(pyerfa 대조 실측).'


def term_uncertainty_text(year, src, k=None):
    """절입 2분 이내 경고용: 계산원·연대에 맞춘 절입 시각 오차 설명."""
    if src == 'sxtwl':
        if erfa is not None and k is not None:   # 정밀 계산원이 있으면 이 절기의 실제 편차를 잰다
            d = (sxtwl_term_instant(year, k) - term_instant(year, k, 'pyerfa')).total_seconds()
            return (f'절입 순간은 sxtwl 값이며, 이 절기는 pyerfa 정밀 계산보다 {abs(d):.0f}초 '
                    + ('이르다' if d < 0 else '늦다') + '. --jie-source auto 로 다시 계산할 것.')
        return '절입 순간은 sxtwl 값이다. ' + sxtwl_bias_text(year)
    if year >= 1960:
        return (f'절입 순간은 {JIE_LABEL[src]} 계산값이며 오차는 약 ±1~2초로 본다'
                + ('(윤초표 이후 연도는 새 윤초가 없다고 가정)' if year > 2026 else '') + '.')
    return f'절입 순간은 {JIE_LABEL[src]} 계산값이며 1960년 이전은 ΔT 다항식 오차가 더해져 수 초 오차가 있을 수 있다.'


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


# ── 진태양시 (참고용, pyerfa) ─────────────────────────────────────
def equation_of_time(u):
    """UTC 순간 → 균시차(진태양시 − 평균태양시) 초. pyerfa 없으면 None. UT1≈UTC(±0.9초)로 둔다."""
    if erfa is None:
        return None
    t1, t2 = utc_to_tt(u)
    _, ra = sun_apparent(t1, t2)
    j1, j2 = erfa.cal2jd(u.year, u.month, u.day)
    ut_sec = u.hour * H + u.minute * 60 + u.second + u.microsecond / 1e6
    gast = erfa.gst06a(j1, j2 + ut_sec / 86400, t1, t2)
    ast = ((gast - ra) / (2 * math.pi) * 86400 + 43200) % 86400  # 그리니치 진태양시
    return ((ast - ut_sec + 43200) % 86400) - 43200


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


# ── 음력 ─────────────────────────────────────────────────────
def lunar_date(y, m, d):
    """양력 → (음력 문자열, 출처, 경고 또는 None). 한국 음력(KASI 자료) 우선."""
    if KoreanLunarCalendar is not None:
        c = KoreanLunarCalendar()
        if c.setSolarDate(y, m, d):
            s = f'{c.lunarYear}년 ' + ('윤' if c.isIntercalation else '') + f'{c.lunarMonth}월 {c.lunarDay}일'
            return s, 'korean_lunar_calendar (KASI 음양력 자료 기반)', None
        why = '범위(1000-02-13 ~ 2050-12-31) 밖'
    else:
        why = '미설치'
    ld = sxtwl.fromSolar(y, m, d)
    s = f'{ld.getLunarYear()}년 ' + ('윤' if ld.isLunarLeap() else '') + f'{ld.getLunarMonth()}월 {ld.getLunarDay()}일'
    w = (f'한국 음력 자료(korean_lunar_calendar) {why}: sxtwl(중국 음력, UTC+8 기준) 값으로 대신했습니다. '
         '합삭이 한국·중국 자정 사이에 들면 하루 다를 수 있습니다(예: 2026-10-10~11-08은 sxtwl이 하루 늦음).')
    print('[경고] ' + w, file=sys.stderr)
    return s, 'sxtwl (중국 음력 — 대체값)', w


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
def judge_clock(u, std, correction=True, longitude=127.5):
    """시지·일 경계를 판단하는 시계: 지방평균시(경도 보정) 또는 서머타임만 뺀 표준시."""
    return u + (timedelta(seconds=longitude * 240) if correction else timedelta(seconds=std))


def compute_core(u, std, correction=True, longitude=127.5, time_known=True, civil_date=None, clock=None):
    """실제 순간 u(UTC) → 간지 인덱스와 판단 근거. time_known=False 이면 civil_date 의 일주만.
    clock 을 주면 그 시각(예: 진태양시)으로 시지·일 경계를 판단한다."""
    ys, yb, ms, mb, prev, nxt = year_month_at(u)
    if time_known:
        lmt = clock if clock is not None else judge_clock(u, std, correction, longitude)
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


def day_boundary_text(u_noon, correction=True, longitude=127.5):
    """시각 미상일 때: 그 날짜의 시대별 표준시·서머타임·경도로 일 경계(법정시)를 계산해 설명한다."""
    std, dst = offset_at(u_noon)
    judge_off = longitude * 240 if correction else std
    delta = std + dst - judge_off                      # 법정시 − 판단시계 (초)
    zone = fmt_off(std + dst) + (' 서머타임' if dst else '')
    how = (f'지방평균시({longitude}°E) 보정' if correction else '보정 미적용(서머타임만 뺌)')
    b = 23 * H + delta                                  # 판단시계 23:00 의 법정시
    if abs(b - 24 * H) < 1:
        s = f'이 날짜는 {zone}이라 {how} 기준 일 경계(子時 시작)가 법정시 자정(00:00)과 같다. 이 날짜 전체가 위 일주다'
    elif b < 24 * H:
        s = f'{zone}, {how} 기준 일 경계는 법정시 {fmt_hms(b)} — 이 시각 이후 출생이면 일주가 다음 날 것으로 바뀐다'
    else:
        s = (f'{zone}, {how} 기준 일 경계는 법정시 (다음 날) {fmt_hms(b - 24 * H)} — 이 날짜 {fmt_hms(b - 24 * H)} '
             '이전 출생이면 일주가 전날 것이다')
    yb = 24 * H + delta                                 # 야자시법: 판단시계 24:00 에 날짜 변경
    if abs(yb - 24 * H) < 1:
        ys = '법정시 자정(00:00)'
    elif yb < 24 * H:
        ys = f'법정시 {fmt_hms(yb)}(이 시각 이후 출생은 다음 날 일주)'
    else:
        ys = f'법정시 {fmt_hms(yb - 24 * H)}(이 날짜 {fmt_hms(yb - 24 * H)} 이전 출생은 전날 일주)'
    return s + f'. 야자시법(子時 앞 절반을 당일로 봄)이면 날짜 변경 시각은 {ys}이다.'


def compute(date_str, time_str=None, correction=True, longitude=127.5):
    y, m, d = map(int, date_str.split('-'))
    warns, alts = [], []
    time_known = time_str is not None
    if time_known:
        parts = list(map(int, time_str.split(':')))
        hh, mi, ss = (parts + [0])[:3]
        civil = datetime(y, m, d, hh, mi, ss)
    else:
        civil = datetime(y, m, d, 12, 0)
    u, std, dst, w = civil_to_utc(civil)
    warns += w
    src = jie_source()
    if src == 'sxtwl':
        warns.append('절입 시각을 sxtwl 값으로 계산했습니다(정밀 계산원 없음 또는 --jie-source sxtwl 지정). '
                     + sxtwl_bias_text(u.year) + ' pip install -r requirements.txt 후 --jie-source auto 로 다시 계산할 것.')
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
            msg = (f'{JQ_KO[j[1]]}({JQ_HJ[j[1]]}) 절입 {kst(j[0]):%Y-%m-%d %H:%M:%S} KST (분 반올림 {kasi_minute(j[0])})'
                   + (f' — 출생은 절입 {h_}시간 {rem // 60}분 {rem % 60}초 {side}' if time_known else ' — 출생일이 절입일, 시각 필요')
                   + f'. 절입 반대편이면 월주 {GAN[ms2]}{ZHI[mb2]}'
                   + (f', 연주 {GAN[ys2]}{ZHI[yb2]}' if (ys2, yb2) != core['year'] else '') + '.')
            warns.append(msg)
            if time_known and delta <= timedelta(minutes=2):
                warns.append('절입 2분 이내 출생: ' + term_uncertainty_text(kst(j[0]).year, src, j[1])
                             + ' KASI/우주항공청 공표 시각은 분 단위 반올림이라 같은 분 안에서는 초 단위 계산값으로 갈린다. '
                             '출생 기록 시각 자체의 정확도(초·분)도 함께 확인할 것.')
            alts.append({'사유': f'{JQ_KO[j[1]]} 절입 반대편', '월주': GAN[ms2] + ZHI[mb2],
                         '연주': GAN[ys2] + ZHI[yb2]})

    tst_txt = None
    if time_known:
        lmt = core['lmt']
        # 시지 경계 ±10분
        r = core['sec_into_branch']
        shift = None
        if r < 600:
            shift = -(r + 60)
        elif 2 * H - r <= 600:
            shift = (2 * H - r) + 60
        if shift is not None:
            alt = compute_core(u + timedelta(seconds=shift), std, correction, longitude)
            warns.append(f'시지 경계 ±10분 이내(판단 시각 {lmt:%H:%M:%S}). 인접 시진이면 {pillars_str(alt)}.')
            alts.append({'사유': '시지 경계 반대편', '사주': pillars_str(alt)})
        # 야자시법 (판단 시각 23:00~23:59)
        if lmt.hour == 23:
            dprev = day_index(lmt.date())
            hs_same = ((dprev % 10 % 5) * 2) % 10
            yaja_next = f'시{gz(core["hour"])} 일{GAN[dprev % 10]}{ZHI[dprev % 12]} 월{gz(core["month"])} 연{gz(core["year"])}'
            yaja_same = f'시{GAN[hs_same]}子 일{GAN[dprev % 10]}{ZHI[dprev % 12]} 월{gz(core["month"])} 연{gz(core["year"])}'
            warns.append(f'야자시 구간(판단 시각 {lmt:%H:%M}, 子時 앞 절반). 이 계산은 정자시법(子時 시작에 날짜 변경)이다. '
                         f'야자시법이면 일주는 {lmt.date()} 일주 {GAN[dprev % 10]}{ZHI[dprev % 12]} 유지 — '
                         f'시주는 다음 날 일간 기준 {gz(core["hour"])}(흔한 처리) 또는 당일 일간 기준 {GAN[hs_same]}子(일부 유파).')
            alts.append({'사유': '야자시법(일주 당일 유지, 시주 다음 날 일간 기준)', '사주': yaja_next})
            if yaja_same != yaja_next:
                alts.append({'사유': '야자시법(일주 당일 유지, 시주 당일 일간 기준)', '사주': yaja_same})
        # 보정 on/off 비교
        other = compute_core(u, std, not correction, longitude)
        if (other['day'], other['hour']) != (core['day'], core['hour']):
            lab = '지방평균시(경도) 보정 미적용' if correction else '지방평균시(경도) 보정 적용'
            warns.append(f'{lab} 시에는 {pillars_str(other)} (시지/일 경계 기준 시계가 달라짐).')
            alts.append({'사유': lab, '사주': pillars_str(other)})
        # 진태양시(참고)
        eot = equation_of_time(u)
        if eot is not None:
            tst = judge_clock(u, std, True, longitude) + timedelta(seconds=eot)
            tst_txt = (f'{tst:%Y-%m-%d %H:%M:%S} (경도 {longitude}°E, 균시차 {eot / 60:+.1f}분, '
                       f'법정시 대비 {(tst - civil).total_seconds() / 60:+.0f}분) — 참고값, 판단에 쓰지 않음')
            tc = compute_core(u, std, True, longitude, clock=tst)
            if (tc['day'], tc['hour']) != (core['day'], core['hour']):
                warns.append(f'참고: 균시차까지 넣은 진태양시({tst:%H:%M:%S}) 기준이면 {pillars_str(tc)}. '
                             '이 계산기는 균시차를 쓰지 않는다(통용 관행).')
                alts.append({'사유': '진태양시(균시차 포함) 기준 — 참고, 비채택', '사주': pillars_str(tc)})
    else:
        warns.append('출생 시각 미상: 시주 없음. ' + day_boundary_text(u, correction, longitude))

    lunar, lunar_src, lw = lunar_date(y, m, d)
    if lw:
        warns.append(lw)

    out = {
        '입력': {'법정시': f'{date_str} {time_str}' if time_known else f'{date_str} (시각 미상)',
               '시간대': fmt_off(std + dst) + (' (서머타임 +1h 포함)' if dst else ''),
               '지방평균시(경도) 보정': (f'적용 (경도 {longitude}°E, 지방평균시 = UTC{longitude / 15:+.4f}h)'
                                  if correction else '미적용 (서머타임만 뺀 표준시 사용)'),
               '균시차(진태양시)': '미적용 (통용 관행' + ('; 진태양시는 아래 참고값)' if tst_txt else
                                                      '; pyerfa 없어 진태양시 참고값 생략)' if time_known and erfa is None else ')')},
        '환산': {'UTC': f'{u:%Y-%m-%d %H:%M:%S}', 'KST(UTC+9) 표기': f'{kst(u):%Y-%m-%d %H:%M:%S}'},
        '음력': lunar,
        '음력 출처': lunar_src,
        '절기': {'직전 절': f'{JQ_KO[core["prev"][1]]}({JQ_HJ[core["prev"][1]]}) {kst(core["prev"][0]):%Y-%m-%d %H:%M:%S} KST'
                         f' (분 반올림 {kasi_minute(core["prev"][0])})',
               '다음 절': f'{JQ_KO[core["next"][1]]}({JQ_HJ[core["next"][1]]}) {kst(core["next"][0]):%Y-%m-%d %H:%M:%S} KST'
                         f' (분 반올림 {kasi_minute(core["next"][0])})',
               '절입 계산': JIE_LABEL[src]},
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
        if tst_txt:
            out['환산']['진태양시(참고)'] = tst_txt
    return out


# ── 출력 ─────────────────────────────────────────────────────
def render_text(r):
    L = []
    for k, v in r['입력'].items():
        L.append(f'{k}: {v}')
    for k, v in r['환산'].items():
        L.append(f'{k}: {v}')
    L.append(f'음력: {r["음력"]}  [{r["음력 출처"]}]')
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
    for a in r['대안']:
        L.append('[대안] ' + a['사유'] + ': ' + (a.get('사주') or f"연주 {a['연주']} 월주 {a['월주']}"))
    return '\n'.join(L)


# ── 자체 검증 ─────────────────────────────────────────────────
def selftest():
    ok = True
    src = jie_source()
    print(f'절입 계산원: {JIE_LABEL[src]}')
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
               ('乙', '午'): '장생', ('庚', '子'): '사', ('癸', '亥'): '제왕'}
    bad = [k for k, v in samples.items() if unseong(*k) != v]
    print(f'[3] 12운성 표본 {len(samples)}건: 불일치 {bad}')
    ok &= not bad
    # 4) 월주·연주 vs sxtwl (절입일 ±1일 제외, 1950~2050 KST 정오)
    d, bad, n = date(1950, 1, 1), 0, 0
    while d <= date(2050, 12, 31):
        u = datetime(d.year, d.month, d.day, 3)  # KST 정오
        ys, yb, ms, mb, prev, nxt = year_month_at(u)
        # sxtwl 일 단위 월주는 베이징시(UTC+8) 날짜·자체 절입 시각으로 바뀌므로 절입일 앞뒤 하루를 제외
        jdays = {(j[0] + timedelta(hours=8, days=dd)).date() for j in (prev, nxt) for dd in (-1, 0, 1)}
        if d not in jdays:
            day = sxtwl.fromSolar(d.year, d.month, d.day)
            mg, yg = day.getMonthGZ(), day.getYearGZ()
            n += 1
            if (mg.tg, mg.dz) != (ms, mb) or (yg.tg, yg.dz) != (ys, yb):
                bad += 1
        d += timedelta(days=1)
    print(f'[4] 연·월주 vs sxtwl 일 단위 값(절입일 ±1일 제외 {n}일): 불일치 {bad}건')
    ok &= bad == 0
    # 5) 2026 절입 정밀값 — DE421 계산·KASI 공표(분)와 대조
    exp = {19: ('2026-10-08 15:29:17', '15:29', None), 21: ('2026-11-07 18:52:04', '18:52', '18:52'),
           23: ('2026-12-07 11:52:31', '11:53', '11:53')}
    bad = []
    for k, (ref, mins, kasi) in exp.items():
        u = term_instant(2026, k)
        dd = (kst(u) - datetime.strptime(ref, '%Y-%m-%d %H:%M:%S')).total_seconds()
        tol = 2 if src != 'sxtwl' else 25
        good = abs(dd) <= tol and (src == 'sxtwl' or kasi_minute(u) == mins)
        print(f'    {JQ_KO[k]} {kst(u):%Y-%m-%d %H:%M:%S} KST (DE421 기록 {ref[11:]}, 차 {dd:+.0f}초) '
              f'분 반올림 {kasi_minute(u)} / KASI {kasi or "미확인"}')
        if not good:
            bad.append(JQ_KO[k])
    print(f'[5] 2026 한로·입동·대설 정밀값(±2초)·분 반올림 대조: 불일치 {bad}')
    ok &= not bad
    # 6) pyerfa vs skyfield+DE421 (둘 다 있을 때)
    if src == 'pyerfa' and _skyfield_ctx() is not None:
        worst = 0.0
        years = [1910, 1935, 1955, 1965, 1975, 1990, 1994, 2000, 2015, 2026, 2027, 2040, 2050]
        for yy in years:
            for k in range(1, 24, 2):
                u = term_instant(yy, k)
                lo = skyfield_sun_lon(u)
                rate = _wrap180(skyfield_sun_lon(u + timedelta(minutes=15)) - lo) / 900
                worst = max(worst, abs(_wrap180(lo - (k * 15 + 270) % 360) / rate))
        print(f'[6] pyerfa vs skyfield+DE421 12절 {len(years)}개 연도: 최대 차 {worst:.2f}초 (허용 2초, 초 반올림 포함)')
        ok &= worst <= 2.0
    else:
        print('[6] pyerfa vs skyfield 대조 생략(둘 중 하나 없음 또는 계산원 강제)')
    # 7) sxtwl 편차 (참고 + 1900~2009 ±3초 확인)
    if src != 'sxtwl':
        worst, d26 = 0.0, []
        for yy in range(1900, 2010):
            for k in range(1, 24, 2):
                worst = max(worst, abs((sxtwl_term_instant(yy, k) - term_instant(yy, k)).total_seconds()))
        for k in range(1, 24, 2):
            d26.append((sxtwl_term_instant(2026, k) - term_instant(2026, k)).total_seconds())
        print(f'[7] sxtwl − 정밀값: 1900~2009 12절 최대 |차| {worst:.0f}초 (허용 4초, 초 반올림 포함) / '
              f'2026년 12절 {min(d26):+.0f}~{max(d26):+.0f}초 (참고: ΔT 외삽)')
        ok &= worst <= 4
    # 8) 음력 (KASI 자료)
    if KoreanLunarCalendar is not None:
        cases = {(1990, 6, 27): '1990년 윤5월 5일', (1994, 6, 17): '1994년 5월 9일',
                 (2026, 10, 10): '2026년 8월 30일', (2026, 11, 8): '2026년 9월 29일', (2026, 11, 9): '2026년 10월 1일'}
        bad = [k for k, v in cases.items() if lunar_date(*k)[0] != v]
        dd, diff26 = date(2026, 1, 1), []
        while dd <= date(2026, 12, 31):
            ld = sxtwl.fromSolar(dd.year, dd.month, dd.day)
            c = KoreanLunarCalendar()
            c.setSolarDate(dd.year, dd.month, dd.day)
            if (c.lunarMonth, c.lunarDay, bool(c.isIntercalation)) != (ld.getLunarMonth(), ld.getLunarDay(), bool(ld.isLunarLeap())):
                diff26.append(dd)
            dd += timedelta(days=1)
        rng = f'{diff26[0]:%m-%d}~{diff26[-1]:%m-%d} {len(diff26)}일' if diff26 else '없음'
        print(f'[8] 음력 표본 {len(cases)}건(KASI 자료): 불일치 {bad} / 참고: 2026년 한국(KASI)·중국(sxtwl) 음력 날짜 차이 {rng}')
        ok &= not bad
    else:
        print('[8] korean_lunar_calendar 미설치: 음력 검사 생략')
    # 9) 시각 미상 일 경계 문구 (시대별 표준시·서머타임)
    cases = {'1987-07-01': '(다음 날) 00:30', '1958-07-01': '자정(00:00)', '1958-01-15': '법정시 23:00',
             '2026-11-20': '법정시 23:30'}
    bad = [k for k, v in cases.items() if not any(v in w for w in compute(k)['경고'])]
    print(f'[9] 시각 미상 일 경계(1987 서머타임 00:30 / 1958 여름 00:00 / 1958 겨울 23:00 / 평시 23:30): 불일치 {bad}')
    ok &= not bad
    # 10) 절입 초 단위·야자시 표본
    spots = {('2026-11-07', '18:52:00'): '戊戌', ('2026-11-07', '18:52:10'): '己亥'}
    bad = [k for k, v in spots.items() if compute(*k)['사주']['월주']['간지'] != v]
    yj = compute('2026-11-15', '23:45')
    has_yaja = any('야자시' in a['사유'] for a in yj['대안'])
    print(f'[10] 입동 18:52:00→戊戌 / 18:52:10→己亥: 불일치 {bad}; 23:45 출생 야자시 대안 표시: {has_yaja}')
    ok &= not bad and has_yaja
    print('결과:', '통과' if ok else '실패')
    return ok


def main():
    ap = argparse.ArgumentParser(description='사주 결정론 계산기 (한국 법정시 입력)')
    ap.add_argument('--date', help='양력 YYYY-MM-DD')
    ap.add_argument('--time', help='법정시 HH:MM 또는 HH:MM:SS (모르면 생략)')
    ap.add_argument('--no-lmt-correction', '--no-solar-correction', dest='no_corr', action='store_true',
                    help='지방평균시(경도) 보정 끔 (옛 이름 --no-solar-correction)')
    ap.add_argument('--longitude', type=float, default=127.5, help='출생지 경도(기본 127.5 → -30분)')
    ap.add_argument('--jie-source', default='auto', choices=['auto', 'pyerfa', 'skyfield', 'sxtwl'],
                    help='절입 순간 계산원 (기본 auto: pyerfa → skyfield+DE421 → sxtwl)')
    ap.add_argument('--json', action='store_true', help='JSON 출력')
    ap.add_argument('--selftest', action='store_true', help='내부 교차검증 실행')
    a = ap.parse_args()
    src = set_jie_source(a.jie_source)
    if src == 'sxtwl' and a.jie_source == 'auto':
        print('[경고] pyerfa·skyfield(DE421) 모두 없어 sxtwl 절입 시각을 씁니다(최근·미래 연도는 수십 초 이를 수 있음).',
              file=sys.stderr)
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not a.date:
        ap.error('--date 필요')
    r = compute(a.date, a.time, not a.no_corr, a.longitude)
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else render_text(r))


if __name__ == '__main__':
    main()
