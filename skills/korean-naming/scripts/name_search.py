#!/usr/bin/env python3
"""인명용 한자 조합 전수 탐색기 (name_search.py)

data/inmyeong_hanja.tsv(인명용 한자 원획표)와 references/suri_table.md(81수리 길흉표)를
읽어, 성씨 원획 A와 이름 두 글자의 한글 발음이 주어졌을 때 그 발음을 가진 인명용
한자의 모든 조합을 만들고 사격(四格)을 계산해 Markdown(또는 TSV) 표로 출력한다.
표준 라이브러리만 쓰며, 같은 입력이면 항상 같은 출력을 낸다.

사격 공식 (원형이정, 한국 주류 관행 — 이 프로젝트의 채택안)
    A = 성 원획, B = 이름1 원획, C = 이름2 원획
    원격(元) = B + C      초년
    형격(亨) = A + B      청장년 (성명의 중심)
    이격(利) = A + C      중년
    정격(貞) = A + B + C  총운
    81을 넘는 수는 81을 뺀다(82 → 1).

모드
    1) 조합 탐색   --surname 7 --first 은 --second 상 [--all-gil] [--group-strokes]
    2) 획수 쌍     --stroke-pairs --surname 7 [--max-stroke 30] [--first 은 --second 상]
    3) 글자 목록   --list-readings 은,상,윤,하

수리표 처리
    suri_table.md 의 '| 수 | 길흉 | ... |' 행을 읽는다(길흉 열은 수 뒤에서 길흉 표기로
    읽히는 첫 칸으로 자동 판별하므로 --suri 로 다른 형식의 표도 줄 수 있다; 같은 수가
    두 번 나오면 첫 행만 쓴다). 표에 없는 수는 --suri-override
    ('38=길,51=반길반흉')로 채운다. 끝내 값이 없는 수는 '미정'(길 아님)으로 두고
    표준오류에 경고한다. 大吉·吉 은 길, 凶·大凶 은 흉이다. 반길반흉은 기본적으로
    '길 아님'으로 세며, --half-as-gil 을 주면 길로 센다.

정렬과 순위 (기본 --sort score)
    순위 키 = (길수 개수 ↓, 大吉 개수 ↓, 등급 점수 합 ↓, 음양 균형 우선).
    등급 점수: 大吉 2, 吉 1, 반길반흉 0, 凶 -1, 大凶 -2, 미정 0.
    순위는 이 키만으로 매기는 경쟁 순위(1,2,2,4…)이므로 동점자는 같은 순위다.
    같은 순위 안의 나열은 실무 편의 순서(획수 확인 플래그 없음 → KS X 1001 수록 →
    그 발음으로 KS X 1001 수록 → 교육용 → 원획 → 코드포인트)일 뿐 우열이 아니다.

플래그 (표의 '플래그' 열)
    日      이름 글자의 부수가 日(강희 72) — 프로젝트 지침상 火 추가 주의 대상
    순양/순음  A·B·C 원획이 모두 홀수/모두 짝수
    획확인   원획 규칙이 옥편 대조 권장 대상(data/README.md 4절의 163자 기준)
    KS외    글자가 KS X 1001(기본 한자 4,888자)에 없음(1002에만 있거나 없음).
            글꼴·전산 입력 편의의 문제이며 출생신고 가능 여부와는 별개다.
    KS음외   글자는 KS X 1001에 있으나 이 발음으로는 실려 있지 않음(예: 沇은 '연'으로만
            실림) — 한글→한자 변환에서 이 발음으로 안 나올 수 있음.
    두음    --dueum 으로 두음법칙 변형 발음(예: 倫 륜→윤)을 포함해 잡힌 글자

오행 표기
    획수오행: 원획 끝자리 1·2 木 / 3·4 火 / 5·6 土 / 7·8 金 / 9·0 水.
    A·B·C 순서로 적고 이웃끼리의 관계를 생(상생)·극(상극)·비(같음)로 붙인다.
    사격 수리오행(원·형·이·정 각 수의 끝자리 오행)도 같은 방식으로 적는다.
    부수오행은 TSV 의 radical_ohaeng(부수 기반 휴리스틱) 그대로다. 빈칸은 '-'.
    발음오행은 초성 기준(ㄱㅋ 木 / ㄴㄷㄹㅌ 火 / ㅇㅎ 土 / ㅅㅈㅊ 金 / ㅁㅂㅍ 水,
    프로젝트 CLAUDE.md 표). --sound-school haerye 를 주면 훈민정음 해례본 배속
    (ㅇㅎ 水, ㅁㅂㅍ 土)을 쓴다. 발음이 고정이므로 머리말에 한 번만 적는다.

이 스크립트가 판단하지 않는 것: 한자 뜻의 좋고 나쁨, 불용문자, 사주 용신. 표는
수리·음양·오행 분류값을 나열할 뿐이며, 최종 판단은 사람이 한다.
"""

import argparse
import csv
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TABLE = os.path.normpath(os.path.join(HERE, "..", "data", "inmyeong_hanja.tsv"))
DEFAULT_SURI = os.path.normpath(os.path.join(HERE, "..", "references", "suri_table.md"))

OHAENG_BY_DIGIT = {1: "木", 2: "木", 3: "火", 4: "火", 5: "土",
                   6: "土", 7: "金", 8: "金", 9: "水", 0: "水"}
SAENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # x 生 SAENG[x]
GEUK = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}   # x 克 GEUK[x]

GRADE_ALIASES = {
    "大吉": "大吉", "대길": "大吉",
    "吉": "吉", "길": "吉",
    "반길반흉": "반길반흉", "半吉半凶": "반길반흉", "반길": "반길반흉", "半吉": "반길반흉",
    "凶": "凶", "흉": "凶",
    "大凶": "大凶", "대흉": "大凶",
}
GRADE_SCORE = {"大吉": 2, "吉": 1, "반길반흉": 0, "凶": -1, "大凶": -2, "미정": 0}

# 원획 옥편 대조 권장 기준 (data/README.md 4절)
CHECK_RULES = {"total-gt-rs-check", "radical-variant-check", "radical-itself-check", "override"}
CHECK_FLAG_PREFIXES = ("multi-rs", "rs-by-kangxi-pos", "kangxi-pos")

# 초성 19자 순서: ㄱ ㄲ ㄴ ㄷ ㄸ ㄹ ㅁ ㅂ ㅃ ㅅ ㅆ ㅇ ㅈ ㅉ ㅊ ㅋ ㅌ ㅍ ㅎ
CHOSEONG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
SOUND_OHAENG = {
    "project": {"ㄱ": "木", "ㄲ": "木", "ㅋ": "木",
                "ㄴ": "火", "ㄷ": "火", "ㄸ": "火", "ㄹ": "火", "ㅌ": "火",
                "ㅇ": "土", "ㅎ": "土",
                "ㅅ": "金", "ㅆ": "金", "ㅈ": "金", "ㅉ": "金", "ㅊ": "金",
                "ㅁ": "水", "ㅂ": "水", "ㅃ": "水", "ㅍ": "水"},
}
SOUND_OHAENG["haerye"] = dict(SOUND_OHAENG["project"])
SOUND_OHAENG["haerye"].update({"ㅇ": "水", "ㅎ": "水", "ㅁ": "土", "ㅂ": "土", "ㅃ": "土", "ㅍ": "土"})


# ---------------------------------------------------------------- 데이터 읽기

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_grade(s):
    s = s.strip()
    if s in GRADE_ALIASES:
        return GRADE_ALIASES[s]
    raise ValueError("알 수 없는 길흉 표기: %r" % s)


def load_suri(path, overrides):
    """수리표 → {n: {'grade','name','desc','src'}}. 빠진 수는 '미정'."""
    # 행 형식: '| 수 | ... |'. 길흉 열은 수 뒤의 칸 가운데 길흉 표기로 읽히는 첫 칸으로
    # 자동 판별한다(프로젝트 표는 2열, saju-myeongri suri81.md 는 4열).
    table = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not cells or not cells[0].isdigit():
                continue
            n = int(cells[0])
            grade, gi = None, None
            for i, c in enumerate(cells[1:], 1):
                if c in GRADE_ALIASES:
                    grade, gi = GRADE_ALIASES[c], i
                    break
            if grade is None or not 1 <= n <= 81 or n in table:
                continue
            rest = [c for i, c in enumerate(cells[1:], 1) if i != gi]
            table[n] = {"grade": grade, "name": rest[0] if rest else "",
                        "desc": " / ".join(rest[1:]), "src": "table"}
    for n, grade in overrides.items():
        prev = table.get(n)
        table[n] = {"grade": grade, "name": prev["name"] if prev else "",
                    "desc": prev["desc"] if prev else "", "src": "override"}
    missing = [n for n in range(1, 82) if n not in table]
    for n in missing:
        table[n] = {"grade": "미정", "name": "", "desc": "", "src": "missing"}
    return table, missing


def parse_overrides(text):
    out = {}
    if not text:
        return out
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        k, _, v = part.partition("=")
        n = int(k.strip())
        if not 1 <= n <= 81:
            raise ValueError("수리 범위 밖: %d" % n)
        out[n] = norm_grade(v)
    return out


def load_table(path):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    for r in rows:
        r["wonhoek"] = int(r["wonhoek"])
        r["radical_no"] = int(r["radical_no"]) if r["radical_no"] else 0
        parts = r["wonhoek_rule"].split("|")
        r["_rule"] = parts[0]
        r["_flags"] = parts[1:]
        r["_check"] = (parts[0] in CHECK_RULES or
                       any(fl.startswith(CHECK_FLAG_PREFIXES) for fl in parts[1:]))
        r["_inm"] = [x for x in r["inmyeong_readings"].split(",") if x]
        r["_dueum"] = [x for x in r["dueum_readings"].split(",") if x]
        # kHangul 원문 '연:0N 윤:N' → {읽기: 표지}
        marks = {}
        for tok in r["khangul_raw"].split():
            rd, _, mk = tok.partition(":")
            marks[rd] = mk
        r["_marks"] = marks
    return rows


def _ks_of_mark(mk):
    if "0" in mk:
        return "1001"
    if "1" in mk:
        return "1002"
    return ""


def ks_level(row, reading):
    """(글자 단위 KS 수록, 이 발음 단위 KS 수록). 값은 '1001' / '1002' / ''.
    글자 단위는 어느 발음으로든 KS X 1001(또는 1002)에 실렸는지,
    발음 단위는 바로 이 발음으로 실렸는지다(한글→한자 변환 목록과 관련)."""
    levels = [_ks_of_mark(mk) for mk in row["_marks"].values()]
    char_lv = "1001" if "1001" in levels else ("1002" if "1002" in levels else "")
    read_lv = _ks_of_mark(row["_marks"].get(reading, ""))
    return char_lv, read_lv


def candidates(rows, reading, use_dueum=False, only=None):
    out = []
    for r in rows:
        via = None
        if reading in r["_inm"]:
            via = "인명용"
        elif use_dueum and reading in r["_dueum"]:
            via = "두음"
        if via is None:
            continue
        if only and r["hanja"] not in only:
            continue
        ks_char, ks_read = ks_level(r, reading)
        out.append({"row": r, "via": via, "ks": ks_char, "ks_read": ks_read, "reading": reading})
    return out


# ---------------------------------------------------------------- 계산

def reduce81(n):
    return (n - 1) % 81 + 1 if n > 81 else n


def ohaeng_of(n):
    return OHAENG_BY_DIGIT[n % 10]


def relation(x, y):
    if not x or not y or x not in SAENG or y not in SAENG:
        return "?"
    if x == y:
        return "비"
    if SAENG[x] == y or SAENG[y] == x:
        return "생"
    if GEUK[x] == y or GEUK[y] == x:
        return "극"
    return "?"


def seq_str(elems):
    rels = [relation(elems[i], elems[i + 1]) for i in range(len(elems) - 1)]
    return "%s (%s)" % ("".join(elems), "·".join(rels))


def yinyang(strokes):
    pat = "".join("양" if s % 2 else "음" for s in strokes)
    if all(s % 2 for s in strokes):
        return pat, "순양"
    if all(s % 2 == 0 for s in strokes):
        return pat, "순음"
    return pat, ""


def sound_ohaeng(syllable, school):
    if not syllable:
        return ""
    code = ord(syllable[0]) - 0xAC00
    if not 0 <= code < 11172:
        return ""
    return SOUND_OHAENG[school][CHOSEONG[code // 588]]


class Ctx:
    def __init__(self, suri, half_as_gil):
        self.suri = suri
        self.half_as_gil = half_as_gil

    def grade(self, n):
        return self.suri[reduce81(n)]["grade"]

    def is_gil(self, grade):
        return grade in ("大吉", "吉") or (self.half_as_gil and grade == "반길반흉")

    def sagyeok(self, a, b, c):
        nums = {"원": b + c, "형": a + b, "이": a + c, "정": a + b + c}
        grades = {k: self.grade(v) for k, v in nums.items()}
        n_gil = sum(1 for g in grades.values() if self.is_gil(g))
        n_dae = sum(1 for g in grades.values() if g == "大吉")
        score = sum(GRADE_SCORE[g] for g in grades.values())
        yy, yy_flag = yinyang([a, b, c])
        return {"nums": nums, "grades": grades, "n_gil": n_gil, "n_dae": n_dae,
                "score": score, "yy": yy, "yy_flag": yy_flag,
                "all_gil": n_gil == 4,
                "rank_key": (-n_gil, -n_dae, -score, 1 if yy_flag else 0)}


ORDER = ("원", "형", "이", "정")
LABEL = {"원": "원격(B+C)", "형": "형격(A+B)", "이": "이격(A+C)", "정": "정격(A+B+C)"}


def fmt_g(n, g):
    return "%d %s" % (n, g)


def competition_rank(items, key):
    """items 는 이미 key 로 정렬됨. 경쟁 순위(1,2,2,4) 부여."""
    prev, rank = None, 0
    for i, it in enumerate(items, 1):
        k = key(it)
        if k != prev:
            rank, prev = i, k
        it["rank"] = rank


# ---------------------------------------------------------------- 모드: 조합

def build_combos(ctx, a, cand_b, cand_c):
    combos = []
    for cb in cand_b:
        for cc in cand_c:
            rb, rc = cb["row"], cc["row"]
            s = ctx.sagyeok(a, rb["wonhoek"], rc["wonhoek"])
            flags = []
            if rb["radical_no"] == 72 or rc["radical_no"] == 72:
                flags.append("日")
            if s["yy_flag"]:
                flags.append(s["yy_flag"])
            if rb["_check"] or rc["_check"]:
                flags.append("획확인")
            if cb["ks"] != "1001" or cc["ks"] != "1001":
                flags.append("KS외")
            elif cb["ks_read"] != "1001" or cc["ks_read"] != "1001":
                flags.append("KS음외")
            if cb["via"] == "두음" or cc["via"] == "두음":
                flags.append("두음")
            practical = (int(rb["_check"]) + int(rc["_check"]),
                         int(cb["ks"] != "1001") + int(cc["ks"] != "1001"),
                         int(cb["ks_read"] != "1001") + int(cc["ks_read"] != "1001"),
                         int(rb["education"] != "Y") + int(rc["education"] != "Y"))
            combos.append({"b": cb, "c": cc, "s": s, "flags": flags,
                           "sort_key": s["rank_key"] + practical +
                           (rb["wonhoek"], rc["wonhoek"], rb["codepoint"], rc["codepoint"])})
    return combos


def short_hun(row):
    h = row["hun"].split("/")[0].split(",")[0].strip()
    return h or "-"


def combo_rows_md(ctx, a, combos, surname_disp, show_def=False):
    head = ["순위", "이름", "원획 A·B·C"] + [LABEL[k] for k in ORDER] + \
           ["길", "大吉", "음양", "획수오행 A·B·C", "사격 수리오행 원·형·이·정",
            "부수오행 B·C", "플래그", "훈음 B / C"]
    if show_def:
        head.append("영문 뜻 B / C")
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for cm in combos:
        rb, rc, s = cm["b"]["row"], cm["c"]["row"], cm["s"]
        name = surname_disp + rb["hanja"] + rc["hanja"]
        if s["all_gil"]:
            name = "**" + name + "**"
        rank = ("★" if s["all_gil"] else "") + str(cm["rank"])
        hoek = seq_str([ohaeng_of(a), rb["hoek_ohaeng"], rc["hoek_ohaeng"]])
        sa = "".join(ohaeng_of(s["nums"][k]) for k in ORDER)
        rad = "%s·%s" % (rb["radical_ohaeng"] or "-", rc["radical_ohaeng"] or "-")
        cells = [rank, name, "%d·%d·%d" % (a, rb["wonhoek"], rc["wonhoek"])] + \
                [fmt_g(s["nums"][k], s["grades"][k]) for k in ORDER] + \
                ["%d/4" % s["n_gil"], str(s["n_dae"]), s["yy"], hoek, sa, rad,
                 " ".join(cm["flags"]) or "-",
                 "%s / %s" % (short_hun(rb), short_hun(rc))]
        if show_def:
            cells.append("%s / %s" % (rb["definition_en"][:40] or "-", rc["definition_en"][:40] or "-"))
        out.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    return out


def combo_rows_tsv(a, combos, surname_disp):
    head = ["rank", "all_gil", "name", "codepoints", "A", "B", "C"] + \
           ["%s_num" % k for k in ORDER] + ["%s_grade" % k for k in ORDER] + \
           ["n_gil", "n_daegil", "score", "yinyang", "hoek_ohaeng", "radical_ohaeng", "flags"]
    out = ["\t".join(head)]
    for cm in combos:
        rb, rc, s = cm["b"]["row"], cm["c"]["row"], cm["s"]
        cells = [str(cm["rank"]), "Y" if s["all_gil"] else "N",
                 surname_disp + rb["hanja"] + rc["hanja"],
                 "%s %s" % (rb["codepoint"], rc["codepoint"]),
                 str(a), str(rb["wonhoek"]), str(rc["wonhoek"])] + \
                [str(s["nums"][k]) for k in ORDER] + [s["grades"][k] for k in ORDER] + \
                [str(s["n_gil"]), str(s["n_dae"]), str(s["score"]), s["yy"],
                 ohaeng_of(a) + rb["hoek_ohaeng"] + rc["hoek_ohaeng"],
                 "%s,%s" % (rb["radical_ohaeng"], rc["radical_ohaeng"]),
                 ",".join(cm["flags"])]
        out.append("\t".join(cells))
    return out


def grouped_rows_md(ctx, a, cand_b, cand_c):
    """(B,C) 원획 쌍별로 묶은 전수표 — 모든 조합을 빠짐없이 복원할 수 있다."""
    by_b, by_c = {}, {}
    for cb in cand_b:
        by_b.setdefault(cb["row"]["wonhoek"], []).append(cb["row"]["hanja"])
    for cc in cand_c:
        by_c.setdefault(cc["row"]["wonhoek"], []).append(cc["row"]["hanja"])
    items = []
    for b in sorted(by_b):
        for c in sorted(by_c):
            s = ctx.sagyeok(a, b, c)
            items.append({"b": b, "c": c, "s": s, "hb": by_b[b], "hc": by_c[c],
                          "k": s["rank_key"] + (b, c)})
    items.sort(key=lambda x: x["k"])
    competition_rank(items, lambda x: x["s"]["rank_key"])
    head = ["순위", "B·C"] + [LABEL[k] for k in ORDER] + \
           ["길", "大吉", "음양", "이름1 후보", "이름2 후보", "조합 수"]
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for it in items:
        s = it["s"]
        cells = [("★" if s["all_gil"] else "") + str(it["rank"]),
                 ("**%d·%d**" if s["all_gil"] else "%d·%d") % (it["b"], it["c"])] + \
                [fmt_g(s["nums"][k], s["grades"][k]) for k in ORDER] + \
                ["%d/4" % s["n_gil"], str(s["n_dae"]),
                 s["yy"] + (" " + s["yy_flag"] if s["yy_flag"] else ""),
                 "".join(it["hb"]), "".join(it["hc"]), str(len(it["hb"]) * len(it["hc"]))]
        out.append("| " + " | ".join(cells) + " |")
    return out, items


# ---------------------------------------------------------------- 모드: 획수 쌍

def stroke_pairs(ctx, a, max_stroke, cand_b=None, cand_c=None):
    by_b, by_c = {}, {}
    for cb in cand_b or []:
        by_b.setdefault(cb["row"]["wonhoek"], []).append(cb["row"]["hanja"])
    for cc in cand_c or []:
        by_c.setdefault(cc["row"]["wonhoek"], []).append(cc["row"]["hanja"])
    items = []
    for b in range(1, max_stroke + 1):
        for c in range(1, max_stroke + 1):
            s = ctx.sagyeok(a, b, c)
            if s["all_gil"]:
                items.append({"b": b, "c": c, "s": s,
                              "hb": by_b.get(b, []), "hc": by_c.get(c, [])})
    items.sort(key=lambda x: (x["s"]["rank_key"], x["b"], x["c"]))
    competition_rank(items, lambda x: x["s"]["rank_key"])
    head = ["순위", "B·C"] + [LABEL[k] for k in ORDER] + ["大吉", "음양", "획수오행 A·B·C"]
    with_chars = cand_b is not None
    if with_chars:
        head += ["이름1 후보", "이름2 후보"]
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for it in items:
        s = it["s"]
        cells = [str(it["rank"]), "%d·%d" % (it["b"], it["c"])] + \
                [fmt_g(s["nums"][k], s["grades"][k]) for k in ORDER] + \
                [str(s["n_dae"]), s["yy"] + (" " + s["yy_flag"] if s["yy_flag"] else ""),
                 seq_str([ohaeng_of(a), ohaeng_of(it["b"]), ohaeng_of(it["c"])])]
        if with_chars:
            cells += ["".join(it["hb"]) or "-", "".join(it["hc"]) or "-"]
        out.append("| " + " | ".join(cells) + " |")
    return out, items


# ---------------------------------------------------------------- 모드: 글자 목록

def list_readings_md(rows, readings, use_dueum):
    out = []
    for rd in readings:
        cand = candidates(rows, rd, use_dueum)
        cand.sort(key=lambda x: (x["row"]["wonhoek"], x["row"]["codepoint"]))
        out.append("### '%s' — %d자" % (rd, len(cand)))
        out.append("")
        head = ["한자", "코드", "원획", "원획 규칙", "부수", "획수오행", "부수오행",
                "교육용", "KS(글자/발음)", "경로", "훈음", "영문 뜻"]
        out.append("| " + " | ".join(head) + " |")
        out.append("|" + "---|" * len(head))
        for cd in cand:
            r = cd["row"]
            rule = r["wonhoek_rule"].replace("|", " + ")
            if r["_check"]:
                rule = "⚠ " + rule
            cells = [r["hanja"], r["codepoint"], str(r["wonhoek"]), rule,
                     "%s(%d)" % (r["radical_char"], r["radical_no"]),
                     r["hoek_ohaeng"], r["radical_ohaeng"] or "-",
                     "Y" if r["education"] == "Y" else "",
                     "%s/%s" % (cd["ks"] or "없음", cd["ks_read"] or "없음"), cd["via"],
                     (r["hun"] or "-").replace("|", "/"),
                     (r["definition_en"] or "-").replace("|", "/")]
            out.append("| " + " | ".join(cells) + " |")
        out.append("")
    return out


# ---------------------------------------------------------------- main

def resolve_surname(rows, text):
    if text.isdigit():
        return int(text), None, None
    for r in rows:
        if r["hanja"] == text:
            return r["wonhoek"], text, (r["_inm"][0] if r["_inm"] else None)
    raise SystemExit("성씨 한자 %r 를 표에서 찾지 못했다. 원획 숫자로 주라." % text)


def main(argv=None):
    ap = argparse.ArgumentParser(description="인명용 한자 조합 전수 탐색 (원=B+C, 형=A+B, 이=A+C, 정=A+B+C)")
    ap.add_argument("--table", default=DEFAULT_TABLE, help="inmyeong_hanja.tsv 경로")
    ap.add_argument("--suri", default=DEFAULT_SURI, help="81수리표 Markdown 경로")
    ap.add_argument("--suri-override", default="", help="예: '38=길,51=반길반흉'")
    ap.add_argument("--half-as-gil", action="store_true", help="반길반흉을 길로 센다(기본: 길 아님)")
    ap.add_argument("--surname", default="7", help="성 원획(숫자) 또는 성 한자(예: 吳)")
    ap.add_argument("--surname-hanja", default=None, help="표시용 성 한자(숫자로 줬을 때)")
    ap.add_argument("--surname-reading", default=None, help="발음오행용 성 한글(예: 오)")
    ap.add_argument("--first", help="이름1 한글 발음")
    ap.add_argument("--second", help="이름2 한글 발음")
    ap.add_argument("--first-hanja", default="", help="이름1 한자를 이 글자들로 제한(예: 昀沇)")
    ap.add_argument("--second-hanja", default="", help="이름2 한자를 이 글자들로 제한")
    ap.add_argument("--dueum", action="store_true", help="두음법칙 변형 발음도 포함(예: 倫→윤)")
    ap.add_argument("--exclude-check", action="store_true", help="원획 옥편 대조 권장 글자 제외")
    ap.add_argument("--ks-only", action="store_true", help="KS X 1001에 있는 글자만(발음 무관)")
    ap.add_argument("--all-gil", action="store_true", help="네 격 모두 길인 조합만")
    ap.add_argument("--group-strokes", action="store_true", help="(B,C) 원획 쌍별로 묶어 출력")
    ap.add_argument("--stroke-pairs", action="store_true", help="네 격 모두 길인 (B,C) 획수 쌍 목록")
    ap.add_argument("--max-stroke", type=int, default=30, help="--stroke-pairs 범위 상한(기본 30)")
    ap.add_argument("--list-readings", default="", help="쉼표로 구분한 발음의 인명용 한자 목록")
    ap.add_argument("--sort", choices=["score", "strokes"], default="score")
    ap.add_argument("--limit", type=int, default=0, help="출력 행 수 제한(0=전부)")
    ap.add_argument("--format", choices=["md", "tsv"], default="md")
    ap.add_argument("--show-def", action="store_true", help="영문 뜻 열 추가")
    ap.add_argument("--sound-school", choices=["project", "haerye"], default="project")
    ap.add_argument("--no-header", action="store_true", help="머리말(조건·통계) 생략")
    ap.add_argument("--out", default="-", help="출력 파일(기본: 표준출력)")
    args = ap.parse_args(argv)

    overrides = parse_overrides(args.suri_override)
    suri, missing = load_suri(args.suri, overrides)
    if missing:
        sys.stderr.write("경고: 수리표에 값이 없는 수 %s → '미정'(길 아님)으로 처리\n" % missing)
    rows = load_table(args.table)
    ctx = Ctx(suri, args.half_as_gil)

    a, s_hanja, s_reading = resolve_surname(rows, args.surname)
    s_hanja = args.surname_hanja or s_hanja or ""
    s_reading = args.surname_reading or s_reading
    surname_disp = s_hanja or "[%d]" % a

    out = []
    if not args.no_header and args.format == "md":
        out.append("<!-- name_search.py 생성물. 직접 고치지 말고 다시 실행할 것. -->")
        out.append("")
        out.append("- 사격 공식: 원격=B+C, 형격=A+B, 이격=A+C, 정격=A+B+C (81 초과 시 81을 뺌)")
        out.append("- 원획표: `%s` (sha256 `%s`, %d자)" % (
            os.path.basename(args.table), sha256_of(args.table)[:16], len(rows)))
        ov = ", ".join("%d=%s" % kv for kv in sorted(overrides.items())) or "없음"
        out.append("- 수리표: `%s` (sha256 `%s`), 덮어쓴 값: %s, 미정: %s" % (
            os.path.basename(args.suri), sha256_of(args.suri)[:16], ov, missing or "없음"))
        out.append("- 반길반흉 처리: %s" % ("길" if args.half_as_gil else "길 아님"))
        out.append("")

    # 모드 3: 글자 목록
    if args.list_readings:
        readings = [x.strip() for x in args.list_readings.split(",") if x.strip()]
        out += list_readings_md(rows, readings, args.dueum)
        return emit(out, args.out)

    only_b = set(args.first_hanja) if args.first_hanja else None
    only_c = set(args.second_hanja) if args.second_hanja else None
    cand_b = candidates(rows, args.first, args.dueum, only_b) if args.first else None
    cand_c = candidates(rows, args.second, args.dueum, only_c) if args.second else None
    if args.exclude_check:
        cand_b = [x for x in cand_b if not x["row"]["_check"]] if cand_b is not None else None
        cand_c = [x for x in cand_c if not x["row"]["_check"]] if cand_c is not None else None
    if args.ks_only:
        cand_b = [x for x in cand_b if x["ks"] == "1001"] if cand_b is not None else None
        cand_c = [x for x in cand_c if x["ks"] == "1001"] if cand_c is not None else None

    # 모드 2: 획수 쌍
    if args.stroke_pairs:
        lines, items = stroke_pairs(ctx, a, args.max_stroke,
                                    cand_b if cand_b is not None and cand_c is not None else None,
                                    cand_c if cand_b is not None and cand_c is not None else None)
        if args.format == "md" and not args.no_header:
            out.append("A=%d, B·C ∈ 1..%d 에서 네 격이 모두 길인 쌍: **%d개** (전체 %d쌍)" % (
                a, args.max_stroke, len(items), args.max_stroke ** 2))
            out.append("")
        out += lines
        return emit(out, args.out)

    # 모드 1: 조합
    if cand_b is None or cand_c is None:
        ap.error("--first 와 --second 가 필요하다 (또는 --stroke-pairs / --list-readings)")
    combos = build_combos(ctx, a, cand_b, cand_c)
    if args.sort == "strokes":
        combos.sort(key=lambda x: (x["b"]["row"]["wonhoek"], x["c"]["row"]["wonhoek"],
                                   x["b"]["row"]["codepoint"], x["c"]["row"]["codepoint"]))
    else:
        combos.sort(key=lambda x: x["sort_key"])
    # 순위는 정렬 방식과 무관하게 수리 키로 매긴다
    ranked = sorted(combos, key=lambda x: x["sort_key"])
    competition_rank(ranked, lambda x: x["s"]["rank_key"])
    n_total = len(combos)
    n_allgil = sum(1 for c in combos if c["s"]["all_gil"])

    if args.format == "md" and not args.no_header:
        sb = sound_ohaeng(args.first, args.sound_school)
        sc = sound_ohaeng(args.second, args.sound_school)
        sa = sound_ohaeng(s_reading, args.sound_school) if s_reading else ""
        out.append("성 %s(원획 %d) + '%s'(%d자) + '%s'(%d자) → 전체 조합 **%d개**, 네 격 모두 길 **%d개**" % (
            surname_disp, a, args.first, len(cand_b), args.second, len(cand_c), n_total, n_allgil))
        out.append("")
        if sa:
            out.append("발음오행(%s): %s%s%s = %s" % (
                args.sound_school, s_reading, args.first, args.second, seq_str([sa, sb, sc])))
        else:
            out.append("발음오행(%s, 이름만): %s%s = %s" % (
                args.sound_school, args.first, args.second, seq_str([sb, sc])))
        dist = {}
        for c in combos:
            dist[c["s"]["n_gil"]] = dist.get(c["s"]["n_gil"], 0) + 1
        out.append("")
        out.append("길수 개수 분포: " + ", ".join("%d/4 → %d개" % (k, dist[k]) for k in sorted(dist, reverse=True)))
        out.append("")

    if args.group_strokes:
        lines, _ = grouped_rows_md(ctx, a, cand_b, cand_c)
        if args.all_gil:
            lines = lines[:2] + [ln for ln in lines[2:] if ln.startswith("| ★")]
        out += lines
        return emit(out, args.out)

    shown = [c for c in combos if c["s"]["all_gil"]] if args.all_gil else combos
    if args.limit:
        shown = shown[:args.limit]
    if args.format == "tsv":
        out += combo_rows_tsv(a, shown, surname_disp)
    else:
        out += combo_rows_md(ctx, a, shown, surname_disp, args.show_def)
    return emit(out, args.out)


def emit(lines, path):
    text = "\n".join(lines) + "\n"
    if path == "-":
        sys.stdout.write(text)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
