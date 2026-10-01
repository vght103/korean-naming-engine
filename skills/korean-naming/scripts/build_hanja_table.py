#!/usr/bin/env python3
"""인명용 한자 데이터 테이블 생성기 (build_hanja_table.py)

Unihan(@mandel59/mojidata 의 moji.db)에서 대법원 인명용 한자(kHangul 표지 N)와
교육용 기초한자(표지 E)를 모두 뽑아, 성명학 원획(原劃)·획수오행·부수 자원오행을
붙인 TSV 를 만든다. 교육용 기초한자 1,800자는 가족관계등록규칙상 인명용 한자에
포함되므로 N 과 E 를 합집합으로 취한다. 표준 라이브러리만 사용하며, 같은 입력에서는
항상 같은 출력(코드포인트 오름차순)을 낸다.

사용법
    python3 build_hanja_table.py --mojidb <moji.db> --out <inmyeong_hanja.tsv>
                                 [--hun <libhangul hanja.txt>]

입력 필드 (Unihan)
    kHangul        '연:0N 윤:N' — 읽기:표지. N=인명용 한자표, E=교육용 기초한자,
                   0/1=KS X 1001/1002 수록, X=표준 미수록 읽기.
    kKoreanName    인명용 한자표 수록 연도(2015 / 2018).
    kRSUnicode     '85.4' = 강희 부수 85 + 나머지 4획. 값이 여러 개면 첫째가 대표.
                   부수 번호 뒤 아포스트로피(85')는 간화 부수 자형.
    kTotalStrokes  유니코드 총획(여러 값이면 첫째가 zh-Hans, 둘째가 zh-Hant 기준).

원획(wonhoek) 규칙 — 강희자전식 '부수 정자 획수 + 나머지 획수'
    K = 강희 부수 정자(正字) 획수 + kRSUnicode 나머지 획수, T = kTotalStrokes.
    한국 성명학의 원획법은 강희자전 획수를 따르고, 약자로 쓰는 부수는 정자 획수로
    되돌린다. 아래 13개 부수가 그 대상이다(괄호 안은 원획).
        85 水(氵)=4  64 手(扌)=4  61 心(忄)=4  94 犬(犭)=4  96 玉(王)=5
        113 示(礻)=5 145 衣(衤)=6 140 艸(艹)=6 130 肉(月 육달월)=6
        162 辵(辶)=7 163 邑(阝 오른쪽)=7 170 阜(阝 왼쪽)=8 122 网(罒)=6
    이 13개 값은 강희 부수 자체의 획수와 같다.

    판정 순서와 wonhoek_rule 값:
      numeral-meaning        一二三四五六七八九十 은 의미수 1..10.
      override               OVERRIDES 표의 소수 예외(사유를 함께 기록).
      [위 13개 부수]
        radical-itself-check 나머지 0획이고 T < 정자 획수인 글자(王, 才)는 그 글자
                             자체가 독립 자형이므로 T 를 쓴다.
        radical-full         K > T: 약자 부수를 정자 획수로 환산한 K 를 쓴다
                             (예: 河 8→9, 道 13→16, 英 9→11).
        unicode-total        K == T: 이미 정자 부수로 쓰인 글자(예: 泉, 志, 忠).
        radical-variant-check T > K: 부수가 더 긴 변형으로 쓰인 글자(예: 求·泰의 氺).
                             T 를 유지하고 확인 표시.
      [그 밖의 부수]
        unicode-total        K == T.
        kangxi-sum           K > T: 부속 성분을 현대 자형으로 덜 센 경우(예: 權 21→22,
                             娜 9→10, 健 10→11). 강희 기준 K 를 쓴다. 단, 부수가
                             老(125)인데 耂(4획)로 쓰인 글자는 耂 를 4획으로 센다
                             (耂 는 원획 환산 관행 대상이 아니다).
        total-gt-rs-check    T > K: 대만 자형 등으로 T 가 큰 경우(예: 成, 盛, 興).
                             T 를 쓰고 확인 표시.
      강희자전 위치 보정(kKangXi): kKangXi 는 강희자전 쪽·자리 번호다. 강희자전은
      부수→나머지 획수 순으로 배열되므로, 실제 수록자(끝자리 0) 가운데 RS 값이 하나뿐인
      약 4만 자를 참조열로 삼아 앞뒤 이웃 4자씩의 최빈 부수·나머지 획수로 그 글자가
      놓인 강희 구간을 추정한다(앞뒤 값이 같을 때만 '확정').
        - kRSUnicode 값이 여럿이면 강희 구간과 맞는 후보를 고른다(예: 萬 140.9, 巡 47.4,
          睡 109.8). 맞는 후보가 둘 이상이면 원획이 큰 쪽.
        - 확정 구간의 나머지 획수가 유니코드 값보다 크면 강희 값을 쓴다(예: 城 6→7,
          誠 6→7, 著 8→9). 원획은 전통 자형 기준이라 큰 쪽이 맞는 경우가 많기 때문이다.
        - 강희 구간이 유니코드 값보다 작으면 값은 바꾸지 않고 플래그만 남긴다
          (예: 姬, 熙 — 옥편마다 9/10, 13/14 로 갈림).
      덧붙는 플래그:
        |rs-by-kangxi-pos:<RS>     대표가 아닌 RS 후보를 강희 위치로 고름
        |multi-rs:<RS>=<값>        고르지 않은 RS 후보로 계산하면 원획이 달라짐
        |kangxi-pos-residual:a>b   강희 위치로 나머지 획수를 a 에서 b 로 올림
        |kangxi-pos:<부수>.<lo>[-<hi>]  강희 위치 추정과 쓰인 나머지 획수가 다름(정보용)
        |component-kangxi-diff     약자 부수 환산분보다 K-T 가 큰 경우(성분 획수 차이)
        |total-variants:a/b        kTotalStrokes 값이 여러 개로 갈릴 때
        |simplified-radical        쓰인 부수가 간화 자형(아포스트로피)일 때
    radical_no/residual 열은 원획 계산에 실제로 쓴 값이다(플래그로 원래 값 확인).
    플래그가 붙은 행은 출생신고 전 옥편/대법원 자료로 획수를 다시 확인한다.

획수오행(hoek_ohaeng): 원획 끝자리 1,2 木 / 3,4 火 / 5,6 土 / 7,8 金 / 9,0 水.

부수 자원오행(radical_ohaeng) — 휴리스틱
    한국 작명 관행의 자원오행은 글자별 뜻까지 보고 정하는 경우가 많아 부수만으로는
    완전히 재현되지 않는다. 여기서는 원획 계산에 쓴 부수(radical_no)만 보고 아래 표를
    적용한다. 출처가 갈리는 부수는 '金/土' 처럼 두 값을 모두 적고(앞이 더 흔한 쪽),
    관행이 뚜렷하지 않은 부수는 비워 둔다. 자세한 근거는 data/README.md 참고.

훈음(hun, 선택)
    --hun 으로 libhangul data/hanja/hanja.txt (BSD-3-Clause, Choe Hwanjin)를 주면
    한 글자 항목의 '뜻 음'(예: '언덕 은, 하늘 가장자리 은')을 붙인다. 주지 않으면
    hun 열은 빈칸이다.
"""

import argparse
import bisect
import csv
import hashlib
import re
import sqlite3
import sys

# 강희 214부수의 부수 획수 (부수 번호 구간 → 획수)
_RADICAL_STROKE_RANGES = [
    (1, 6, 1), (7, 29, 2), (30, 60, 3), (61, 94, 4), (95, 117, 5),
    (118, 146, 6), (147, 166, 7), (167, 175, 8), (176, 186, 9),
    (187, 194, 10), (195, 200, 11), (201, 204, 12), (205, 208, 13),
    (209, 210, 14), (211, 211, 15), (212, 213, 16), (214, 214, 17),
]


def kangxi_radical_strokes(n):
    for lo, hi, s in _RADICAL_STROKE_RANGES:
        if lo <= n <= hi:
            return s
    raise ValueError("bad radical number %r" % n)


# 원획 환산 대상 부수: 번호 → (정자, 약자, 원획, 약자의 최소 필획)
ABBREVIATED_RADICALS = {
    85: ("水", "氵", 4, 3),
    64: ("手", "扌", 4, 3),
    61: ("心", "忄", 4, 3),
    94: ("犬", "犭", 4, 3),
    96: ("玉", "王", 5, 4),
    113: ("示", "礻", 5, 4),
    145: ("衣", "衤", 6, 5),
    140: ("艸", "艹", 6, 3),
    130: ("肉", "月", 6, 4),
    162: ("辵", "辶", 7, 3),
    163: ("邑", "阝", 7, 2),
    170: ("阜", "阝", 8, 2),
    122: ("网", "罒", 6, 5),
}

# 원획 환산 관행이 없는 축약 부수: 번호 → 실제로 쓰이는 자형의 획수
WRITTEN_SHORTER = {
    125: 4,  # 老 → 耂
}

NUMERALS = {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
}

# 규칙으로 처리되지 않는 소수 예외. 값: (원획, 사유)
OVERRIDES = {
    "延": (7, "康熙 廴部 4畫=7; Unicode 총획 8은 대만 자형"),
    "筵": (13, "竹6+延7; Unicode 총획 14는 대만 자형 延8 기준"),
    "御": (11, "康熙 彳部 8畫=11; Unicode 총획 12는 대만 자형"),
    "禦": (16, "示5+御11; Unicode 총획 17은 대만 자형 御12 기준"),
}

# 부수 자원오행 휴리스틱 (강희 부수 번호 → 오행)
RADICAL_OHAENG = {
    # 木: 나무·풀·곡식·실
    75: "木", 140: "木", 118: "木", 115: "木", 119: "木", 120: "木",
    97: "木", 179: "木", 199: "木", 200: "木", 202: "木",
    # 火: 불·해·붉음, 心 은 관행상 火
    86: "火", 72: "火", 155: "火", 61: "火",
    # 土: 흙·산·밭·언덕·마을
    32: "土", 46: "土", 102: "土", 166: "土", 170: "土", 163: "土",
    # 金: 쇠·칼·창·도끼·재물
    167: "金", 18: "金", 62: "金", 69: "金", 154: "金",
    # 출처가 갈리는 부수
    96: "金/土",   # 玉: 金(보석·귀금속) / 土(땅에서 남)
    112: "土/金",  # 石: 土(돌·흙) / 金(광물)
    # 水: 물·비·얼음·내·물고기
    85: "水", 173: "水", 15: "水", 47: "水", 195: "水",
}

HOEK_OHAENG = {1: "木", 2: "木", 3: "火", 4: "火", 5: "土",
               6: "土", 7: "金", 8: "金", 9: "水", 0: "水"}

# 검증용 원획 기준값(작명서·성씨표 관행값)
KNOWN_WONHOEK = (
    "金8 李7 朴6 崔11 鄭19 姜9 趙14 尹4 張11 林8 韓17 吳7 徐10 申5 權22 "
    "黃12 安6 宋7 劉15 洪10 瑞14 潤16 河9 沇8 昀8 垠9 尙8 忠8 炫9 娜10 延7 "
    "道16 英11 浩11 珍10 祐10 福14 裕13 育10 郁13 陽17 都16"
)

COLUMNS = [
    "hanja", "codepoint", "inmyeong_readings", "all_readings", "education",
    "koreanname_year", "radical_no", "radical_simplified", "residual",
    "unicode_total_strokes", "wonhoek", "wonhoek_rule", "hoek_ohaeng",
    "radical_ohaeng", "definition_en",
    # 추가 열
    "radical_char", "dueum_readings", "khangul_raw", "hun",
]

_RS_RE = re.compile(r"^(\d+)('*)\.(-?\d+)$")


def parse_rs(value):
    out = []
    for tok in value.split():
        m = _RS_RE.match(tok)
        if not m:
            raise ValueError("bad kRSUnicode %r" % value)
        out.append((int(m.group(1)), len(m.group(2)), int(m.group(3)), tok))
    return out


def parse_khangul(value):
    """'연:0N 윤:N' → [('연', '0N'), ('윤', 'N')]"""
    out = []
    for tok in value.split():
        reading, _, marks = tok.partition(":")
        out.append((reading, marks))
    return out


# 두음법칙(한글 맞춤법 제10~12항) 변형
_JUNG_YI = {2, 6, 7, 12, 17, 20}      # ㅑ ㅕ ㅖ ㅛ ㅠ ㅣ
_JUNG_NIEUN_YI = {6, 12, 17, 20}      # 녀 뇨 뉴 니


def dueum(reading):
    if len(reading) != 1 or not ("가" <= reading <= "힣"):
        return None
    code = ord(reading) - 0xAC00
    cho, jung, jong = code // 588, (code % 588) // 28, code % 28
    if cho == 5:  # ㄹ
        new = 11 if jung in _JUNG_YI else 2
    elif cho == 2 and jung in _JUNG_NIEUN_YI:  # ㄴ
        new = 11
    else:
        return None
    return chr(0xAC00 + new * 588 + jung * 28 + jong)


def rs_value(n, residual):
    if n in ABBREVIATED_RADICALS:
        return ABBREVIATED_RADICALS[n][2] + residual
    if residual > 0 and n in WRITTEN_SHORTER:
        return WRITTEN_SHORTER[n] + residual
    return kangxi_radical_strokes(n) + residual


class KangxiIndex:
    """강희자전 위치(kKangXi)로 부수·나머지 획수 구간을 추정한다."""

    WINDOW = 4

    def __init__(self, kangxi, rs_tab):
        refs = []
        self.pos = {}
        for ch, value in kangxi.items():
            key = self._key(value)
            if key is None:
                continue
            self.pos[ch] = key[:2]
            toks = rs_tab.get(ch, "").split()
            if key[2] != 0 or len(toks) != 1 or "'" in toks[0]:
                continue
            n, _simp, res, _tok = parse_rs(toks[0])[0]
            refs.append((key[:2], ord(ch), n, res))
        refs.sort()
        self.refs = refs
        self.keys = [(r[0], r[1]) for r in refs]

    @staticmethod
    def _key(value):
        m = re.match(r"^(\d{4})\.(\d{2})(\d)$", value.split()[0])
        if not m:
            return None
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    @staticmethod
    def _mode(values):
        # 최빈값, 동률이면 가까운 쪽(목록 앞쪽) 우선
        counts = {}
        for v in values:
            counts[v] = counts.get(v, 0) + 1
        best = max(counts.values())
        for v in values:
            if counts[v] == best:
                return v

    def section(self, ch):
        """(부수, lo, hi) 또는 None. lo/hi 는 앞/뒤 이웃의 나머지 획수."""
        if ch not in self.pos:
            return None
        q = (self.pos[ch], ord(ch))
        i = bisect.bisect_left(self.keys, q)
        w = self.WINDOW
        before = [r for r in self.refs[max(0, i - 3 * w):i] if r[1] != ord(ch)][-w:]
        after = [r for r in self.refs[i:i + 3 * w] if r[1] != ord(ch)][:w]
        if not before or not after:
            return None
        before.reverse()  # 가까운 순
        rad = self._mode([r[2] for r in before + after])
        b = [r[3] for r in before if r[2] == rad]
        a = [r[3] for r in after if r[2] == rad]
        if not b or not a:
            return None
        return rad, self._mode(b), self._mode(a)


def choose_rs(rs_list, sec):
    """여러 RS 후보 중 강희 위치에 맞는 것을 고른다."""
    if len(rs_list) == 1 or sec is None:
        return rs_list[0]
    rad, lo, hi = sec
    lo, hi = min(lo, hi), max(lo, hi)
    same = [c for c in rs_list if c[0] == rad]
    inside = [c for c in same if lo <= c[2] <= hi]
    pool = inside or same
    if not pool:
        return rs_list[0]
    return max(pool, key=lambda c: (rs_value(c[0], c[2]), -rs_list.index(c)))


def compute_wonhoek(ch, rs_list, totals, sec=None):
    """returns (wonhoek, rule_string, (radical, simplified, residual))"""
    t0, tmax = totals[0], max(totals)
    chosen = choose_rs(rs_list, sec)
    n, simp, res, tok = chosen
    flags = []
    if chosen is not rs_list[0]:
        flags.append("rs-by-kangxi-pos:" + tok)

    fixed = ch in NUMERALS or ch in OVERRIDES
    if sec is not None and sec[0] == n and not fixed and res >= 0:
        lo, hi = min(sec[1], sec[2]), max(sec[1], sec[2])
        if lo == hi and lo > res:
            flags.append("kangxi-pos-residual:%d>%d" % (res, lo))
            res = lo
        elif not (lo <= res <= hi):
            flags.append("kangxi-pos:%d.%s" % (n, lo if lo == hi else "%d-%d" % (lo, hi)))
    k = rs_value(n, res)

    if ch in NUMERALS:
        value, rule = NUMERALS[ch], "numeral-meaning"
    elif ch in OVERRIDES:
        value, rule = OVERRIDES[ch][0], "override"
    elif n in ABBREVIATED_RADICALS:
        _full, _abbr, full_strokes, min_written = ABBREVIATED_RADICALS[n]
        if res == 0 and t0 < full_strokes:
            value, rule = t0, "radical-itself-check"
        elif k > tmax:
            value, rule = k, "radical-full"
            if k - t0 > full_strokes - min_written:
                flags.append("component-kangxi-diff")
        elif k == t0:
            value, rule = t0, "unicode-total"
        else:
            value, rule = tmax, "radical-variant-check"
    else:
        if k == t0:
            value, rule = t0, "unicode-total"
        elif k > tmax:
            value, rule = k, "kangxi-sum"
        else:
            value, rule = tmax, "total-gt-rs-check"

    for alt in rs_list:
        if alt is chosen:
            continue
        v = rs_value(alt[0], alt[2])
        if v != value:
            flags.append("multi-rs:%s=%d" % (alt[3], v))
    if len(set(totals)) > 1:
        flags.append("total-variants:" + "/".join(str(t) for t in totals))
    if simp:
        flags.append("simplified-radical")
    return value, "|".join([rule] + flags), (n, simp, res)


def load_hun(path):
    """libhangul hanja.txt → {hanja: [(reading, meaning), ...]}"""
    table = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.rstrip("\n").split(":")
            if len(parts) < 3:
                continue
            reading, hanja, meaning = parts[0], parts[1], ":".join(parts[2:])
            if len(hanja) == 1 and len(reading) == 1:
                table.setdefault(hanja, []).append((reading, meaning.strip()))
    return table


def hun_for(ch, readings, hun_table):
    entries = hun_table.get(ch)
    if not entries:
        return ""
    order = {r: i for i, r in enumerate(readings)}
    entries = sorted(entries, key=lambda e: order.get(e[0], len(order)))
    seen, out = set(), []
    for _r, meaning in entries:
        if meaning and meaning not in seen:
            seen.add(meaning)
            out.append(meaning)
    return " / ".join(out)


def clean(s):
    return re.sub(r"[\t\r\n]+", " ", s or "").strip()


def build(mojidb, hun_path=None):
    con = sqlite3.connect("file:%s?mode=ro" % mojidb, uri=True)

    def table(name):
        return dict(con.execute('SELECT UCS, value FROM "%s"' % name))

    khangul = table("unihan_kHangul")
    kname = table("unihan_kKoreanName")
    rs_tab = table("unihan_kRSUnicode")
    ts_tab = table("unihan_kTotalStrokes")
    defs = table("unihan_kDefinition")
    kangxi = table("unihan_kKangXi")
    radical_chars = dict(con.execute(
        "SELECT radical_number, radical_CJKUI FROM radicals "
        "WHERE radical_simplified = 0"))
    con.close()

    kx_index = KangxiIndex(kangxi, rs_tab)
    hun_table = load_hun(hun_path) if hun_path else {}

    rows = []
    for ch in sorted(khangul, key=ord):
        readings = parse_khangul(khangul[ch])
        inm = [r for r, m in readings if "N" in m or "E" in m]
        if not inm:
            continue
        edu = any("E" in m for _r, m in readings)
        rs_list = parse_rs(rs_tab[ch])
        totals = [int(t) for t in ts_tab[ch].split()]
        wonhoek, rule, (n, simp, res) = compute_wonhoek(
            ch, rs_list, totals, kx_index.section(ch))
        dueum_list = []
        for r in inm:
            d = dueum(r)
            if d and d not in inm and d not in dueum_list:
                dueum_list.append(d)
        rows.append({
            "hanja": ch,
            "codepoint": "U+%04X" % ord(ch),
            "inmyeong_readings": ",".join(inm),
            "all_readings": ",".join(r for r, _m in readings),
            "education": "Y" if edu else "N",
            "koreanname_year": kname.get(ch, ""),
            "radical_no": str(n),
            "radical_simplified": "Y" if simp else "N",
            "residual": str(res),
            "unicode_total_strokes": str(totals[0]),
            "wonhoek": str(wonhoek),
            "wonhoek_rule": rule,
            "hoek_ohaeng": HOEK_OHAENG[wonhoek % 10],
            "radical_ohaeng": RADICAL_OHAENG.get(n, ""),
            "definition_en": clean(defs.get(ch, "")),
            "radical_char": radical_chars.get(n, ""),
            "dueum_readings": ",".join(dueum_list),
            "khangul_raw": khangul[ch],
            "hun": clean(hun_for(ch, inm, hun_table)),
        })
    return rows


def write_tsv(rows, out):
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_NONE,
                       quotechar=None, escapechar=None, lineterminator="\n")
        w.writerow(COLUMNS)
        for row in rows:
            w.writerow([row[c] for c in COLUMNS])


# 옥편 대조를 권하는 규칙·플래그 (kangxi-sum, component-kangxi-diff 는 정보성)
CHECK_RULES = {"total-gt-rs-check", "radical-variant-check", "radical-itself-check", "override"}
CHECK_FLAGS = {"multi-rs", "rs-by-kangxi-pos", "kangxi-pos-residual", "kangxi-pos",
               "total-variants", "simplified-radical"}


def report(rows, out=sys.stderr):
    by_char = {r["hanja"]: r for r in rows}
    edu = sum(r["education"] == "Y" for r in rows)
    nonly = sum(r["education"] == "N" for r in rows)
    both = sum(r["education"] == "Y" and r["koreanname_year"] != "" for r in rows)
    print("rows=%d education(E)=%d N-only=%d E&N=%d" % (len(rows), edu, nonly, both), file=out)

    rules, flag_counts = {}, {}
    flagged = check = 0
    for r in rows:
        parts = r["wonhoek_rule"].split("|")
        base, flags = parts[0], [f.split(":")[0] for f in parts[1:]]
        rules[base] = rules.get(base, 0) + 1
        for f in flags:
            flag_counts[f] = flag_counts.get(f, 0) + 1
        if base not in ("unicode-total", "radical-full", "numeral-meaning") or flags:
            flagged += 1
        if base in CHECK_RULES or any(f in CHECK_FLAGS for f in flags):
            check += 1
    print("rules=" + ", ".join("%s:%d" % kv for kv in sorted(rules.items())), file=out)
    print("flags=" + ", ".join("%s:%d" % kv for kv in sorted(flag_counts.items())), file=out)
    print("flagged(any)=%d check-recommended=%d" % (flagged, check), file=out)

    mismatches = 0
    for tok in KNOWN_WONHOEK.split():
        ch, expected = tok[0], int(tok[1:])
        r = by_char.get(ch)
        if r is None:
            print("VALIDATE missing %s" % ch, file=out)
            mismatches += 1
        elif int(r["wonhoek"]) != expected:
            print("VALIDATE mismatch %s expected=%d got=%s rule=%s" % (
                ch, expected, r["wonhoek"], r["wonhoek_rule"]), file=out)
            mismatches += 1
        elif r["wonhoek_rule"].startswith("override"):
            print("VALIDATE ok-by-override %s=%d (%s)" % (ch, expected, OVERRIDES[ch][1]), file=out)
    print("validation mismatches=%d" % mismatches, file=out)
    return mismatches


def report_variants(mojidb, chars="尙尚", out=sys.stderr):
    """자형이 비슷한 글자의 Unihan 한국 관련 값을 출력한다(尙 U+5C19 vs 尚 U+5C1A)."""
    con = sqlite3.connect("file:%s?mode=ro" % mojidb, uri=True)
    for ch in chars:
        vals = []
        for field in ("kHangul", "kKorean", "kIRG_KSource", "kKoreanEducationHanja", "kKoreanName"):
            row = con.execute('SELECT value FROM "unihan_%s" WHERE UCS = ?' % field, (ch,)).fetchone()
            vals.append("%s=%s" % (field, row[0] if row else "-"))
        print("VARIANT %s U+%04X %s" % (ch, ord(ch), " ".join(vals)), file=out)
    con.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description="인명용 한자 TSV 생성 (Unihan 기반)")
    ap.add_argument("--mojidb", required=True, help="@mandel59/mojidata dist/moji.db 경로")
    ap.add_argument("--out", required=True, help="출력 TSV 경로")
    ap.add_argument("--hun", help="libhangul data/hanja/hanja.txt 경로(선택)")
    args = ap.parse_args(argv)

    if args.hun:
        with open(args.hun, "rb") as f:
            print("hun source sha256=%s" % hashlib.sha256(f.read()).hexdigest(), file=sys.stderr)
    rows = build(args.mojidb, args.hun)
    write_tsv(rows, args.out)
    report(rows)
    report_variants(args.mojidb)
    return 0


if __name__ == "__main__":
    sys.exit(main())
