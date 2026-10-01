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
    정격(貞) = A + B + C  총운(말년 포함)
    81을 넘는 수는 80을 뺀다(82 → 2, 161 → 81). 81은 1로 돌아가는 환원수이기 때문이다.

모드
    1) 조합 탐색   --surname 吳 --first 은 --second 상 [--all-gil] [--group-strokes]
    2) 획수 쌍     --stroke-pairs --surname 7 [--max-stroke 30] [--first 은 --second 상]
    3) 글자 목록   --list-readings 은,상,윤,하
    4) 전체 보고서 --surname 吳 --first 은 --second 상 --report --out 파일.md
                  (조건·요약·글자 목록·획수 쌍 전수표·네 격 모두 吉 조합·실무 참고표·
                  전체 조합표를 한 문서로 만든다)
    5) 수리표 점검 --check-suri  (81개 수가 모두 읽히는지 확인, 빠지면 종료 코드 1)

수리표 처리
    references/suri_table.md 의 '| 수 | 격명 | 별칭 | 길흉 | 의미 | 이설 |' 표를 읽는다.
    머리행에서 '길흉'·'격명' 열 위치를 찾고, 그 표 안에서 첫 칸이 숫자인 행만 쓴다.
    머리행이 없는 다른 형식의 표(--suri 로 지정)는 수 뒤의 칸 가운데 길흉 표기로
    읽히는 첫 칸을 길흉 열로 본다. 같은 수가 두 번 나오면 첫 행만 쓴다.
    채택본은 3단계(吉 / 반길반흉 / 凶)다. 다른 표가 쓰는 大吉·大凶도 읽을 수 있으며
    각각 길·흉으로 센다(그 경우에만 '大吉' 개수 열을 보인다).
    반길반흉은 기본적으로 '길 아님'으로 세며, --half-as-gil 을 주면 길로 센다.
    --suri-override('51=길' 처럼)로 특정 수의 판정을 바꿔 민감도를 볼 수 있다.
    표에 없는 수는 '미정'(길 아님)으로 두고 표준오류에 경고한다.

정렬과 순위 (기본 --sort score)
    순위 키 = (길수 개수 ↓, 大吉 개수 ↓, 등급 점수 합 ↓, 음양 균형 우선).
    등급 점수: 大吉 2, 吉 1, 반길반흉 0, 凶 -1, 大凶 -2, 미정 0.
    3단계 표에서는 大吉이 없으므로 네 격이 모두 吉인 조합은 음양이 순양·순음이 아닌 한
    모두 같은 순위(1위)다. 순위는 이 키만으로 매기는 경쟁 순위(1,2,2,4…)다.
    같은 순위 안의 나열은 실무 편의 순서(획수 확인 플래그 없음 → KS X 1001 수록 →
    그 발음으로 KS X 1001 수록 → 교육용 → 원획 → 코드포인트)일 뿐 우열이 아니다.

플래그 (표의 '플래그' 열)
    日      이름 글자의 부수가 日(강희 72) — 프로젝트 지침상 火 추가 주의 대상
    순양/순음  A·B·C 원획이 모두 홀수/모두 짝수
    획확인   원획표의 wonhoek_check = Y(옥편 대조 권장, data/README.md 4절)
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
    운해본 계열 통용 배속). --sound-school haerye 를 주면 훈민정음 해례본 배속
    (ㅇㅎ 水, ㅁㅂㅍ 土)을 쓴다. 발음이 고정이므로 머리말에 한 번만 적는다.
    세 오행은 서로 다른 분류법이며 사주 오행 개수에 더하지 않는다.

이 스크립트가 판단하지 않는 것: 한자 뜻의 좋고 나쁨, 불용문자, 사주 용신. 표는
수리·음양·오행 분류값을 나열할 뿐이며, 최종 판단은 사람이 한다.
"""

import argparse
import csv
import hashlib
import os
import shlex
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
    "반": "반길반흉",
    "凶": "凶", "흉": "凶",
    "大凶": "大凶", "대흉": "大凶",
}
GRADE_SCORE = {"大吉": 2, "吉": 1, "반길반흉": 0, "凶": -1, "大凶": -2, "미정": 0}

# 원획 옥편 대조 권장 기준 — TSV 에 wonhoek_check 열이 없을 때만 쓰는 예비 규칙
# (build_hanja_table.py 의 CHECK_RULES·CHECK_FLAGS 와 같은 값)
CHECK_RULES = {"total-gt-rs-check", "radical-variant-check", "radical-itself-check", "override"}
CHECK_FLAGS = {"multi-rs", "rs-by-kangxi-pos", "kangxi-pos-residual", "kangxi-pos",
               "meat-moon-not-left", "total-variants", "simplified-radical"}

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
SOUND_SCHOOL_LABEL = {"project": "운해본 계열 통용 배속", "haerye": "훈민정음 해례본 배속"}


# ---------------------------------------------------------------- 데이터 읽기

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_cell(c):
    """'**吉**', '吉 (만성형)' 같은 장식을 걷어 낸 값."""
    c = c.replace("**", "").strip()
    for sep in (" (", "(", " "):
        if sep in c:
            head = c.split(sep, 1)[0].strip()
            if head in GRADE_ALIASES:
                return head
    return c


def norm_grade(s):
    s = clean_cell(s)
    if s in GRADE_ALIASES:
        return GRADE_ALIASES[s]
    raise ValueError("알 수 없는 길흉 표기: %r" % s)


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def load_suri(path, overrides):
    """수리표 → ({n: {'grade','name','desc','src'}}, missing, duplicates)."""
    table, dups = {}, []
    gi = ni = None          # 머리행에서 찾은 길흉·격명 열 위치
    in_main = False
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                in_main = False
                continue
            cells = _cells(line)
            if cells and cells[0] == "수" and "길흉" in cells:
                gi, ni = cells.index("길흉"), (cells.index("격명") if "격명" in cells else None)
                in_main = True
                continue
            if not cells or not cells[0].isdigit():
                continue
            n = int(cells[0])
            if not 1 <= n <= 81:
                continue
            grade = None
            if in_main and gi is not None and gi < len(cells):
                c = clean_cell(cells[gi])
                grade = GRADE_ALIASES.get(c)
                name = cells[ni].replace("**", "") if ni is not None and ni < len(cells) else ""
                rest = [cells[i] for i in range(1, len(cells)) if i not in (gi, ni)]
            elif gi is None:
                # 머리행이 없는 다른 형식: 길흉 표기로 읽히는 첫 칸을 길흉 열로 본다
                for i, c in enumerate(cells[1:], 1):
                    if clean_cell(c) in GRADE_ALIASES:
                        grade = GRADE_ALIASES[clean_cell(c)]
                        rest = [x for j, x in enumerate(cells[1:], 1) if j != i]
                        name, rest = (rest[0] if rest else ""), rest[1:]
                        break
            if grade is None:
                continue
            if n in table:
                dups.append(n)
                continue
            table[n] = {"grade": grade, "name": name,
                        "desc": " / ".join(x for x in rest if x and x != "–"), "src": "table"}
    for n, grade in overrides.items():
        prev = table.get(n)
        table[n] = {"grade": grade, "name": prev["name"] if prev else "",
                    "desc": prev["desc"] if prev else "", "src": "override"}
    missing = [n for n in range(1, 82) if n not in table]
    for n in missing:
        table[n] = {"grade": "미정", "name": "", "desc": "", "src": "missing"}
    return table, missing, dups


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
        if r.get("wonhoek_check") in ("Y", "N"):
            r["_check"] = r["wonhoek_check"] == "Y"
        else:
            r["_check"] = (parts[0] in CHECK_RULES or
                           any(fl.split(":")[0] in CHECK_FLAGS for fl in parts[1:]))
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


def is_practical(cd):
    """실무 참고 조건: KS X 1001 수록 또는 교육용, 그리고 획수 확인 플래그 없음."""
    r = cd["row"]
    return (cd["ks"] == "1001" or r["education"] == "Y") and not r["_check"]


# ---------------------------------------------------------------- 계산

def reduce81(n):
    """81을 넘는 수는 80을 뺀다(82→2, 161→81)."""
    while n > 81:
        n -= 80
    return n


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
        self.has_dae = any(v["grade"] in ("大吉", "大凶") for v in suri.values())

    def grade(self, n):
        return self.suri[reduce81(n)]["grade"]

    def is_gil(self, grade):
        return grade in ("大吉", "吉") or (self.half_as_gil and grade == "반길반흉")

    def sagyeok(self, a, b, c):
        nums = {"원": b + c, "형": a + b, "이": a + c, "정": a + b + c}
        grades = {k: self.grade(v) for k, v in nums.items()}
        n_gil = sum(1 for g in grades.values() if self.is_gil(g))
        n_dae = sum(1 for g in grades.values() if g == "大吉")
        n_half = sum(1 for g in grades.values() if g == "반길반흉")
        score = sum(GRADE_SCORE[g] for g in grades.values())
        yy, yy_flag = yinyang([a, b, c])
        return {"nums": nums, "grades": grades, "n_gil": n_gil, "n_dae": n_dae,
                "n_half": n_half, "score": score, "yy": yy, "yy_flag": yy_flag,
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
                           "practical": is_practical(cb) and is_practical(cc),
                           "sort_key": s["rank_key"] + practical +
                           (rb["wonhoek"], rc["wonhoek"], rb["codepoint"], rc["codepoint"])})
    return combos


def rank_combos(combos):
    ranked = sorted(combos, key=lambda x: x["sort_key"])
    competition_rank(ranked, lambda x: x["s"]["rank_key"])
    return ranked


def short_hun(row):
    h = row["hun"].split("/")[0].split(",")[0].strip()
    return h or "-"


def combo_rows_md(ctx, a, combos, surname_disp, show_def=False):
    head = ["순위", "이름", "원획 A·B·C"] + [LABEL[k] for k in ORDER] + ["길"]
    if ctx.has_dae:
        head.append("大吉")
    head += ["음양", "획수오행 A·B·C", "사격 수리오행 원·형·이·정",
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
                [fmt_g(s["nums"][k], s["grades"][k]) for k in ORDER] + ["%d/4" % s["n_gil"]]
        if ctx.has_dae:
            cells.append(str(s["n_dae"]))
        cells += [s["yy"], hoek, sa, rad, " ".join(cm["flags"]) or "-",
                  "%s / %s" % (short_hun(rb), short_hun(rc))]
        if show_def:
            cells.append("%s / %s" % (rb["definition_en"][:40] or "-", rc["definition_en"][:40] or "-"))
        out.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    return out


def combo_rows_tsv(a, combos, surname_disp):
    head = ["rank", "all_gil", "name", "codepoints", "A", "B", "C"] + \
           ["%s_num" % k for k in ORDER] + ["%s_grade" % k for k in ORDER] + \
           ["n_gil", "n_half", "score", "yinyang", "hoek_ohaeng", "radical_ohaeng", "flags"]
    out = ["\t".join(head)]
    for cm in combos:
        rb, rc, s = cm["b"]["row"], cm["c"]["row"], cm["s"]
        cells = [str(cm["rank"]), "Y" if s["all_gil"] else "N",
                 surname_disp + rb["hanja"] + rc["hanja"],
                 "%s %s" % (rb["codepoint"], rc["codepoint"]),
                 str(a), str(rb["wonhoek"]), str(rc["wonhoek"])] + \
                [str(s["nums"][k]) for k in ORDER] + [s["grades"][k] for k in ORDER] + \
                [str(s["n_gil"]), str(s["n_half"]), str(s["score"]), s["yy"],
                 ohaeng_of(a) + rb["hoek_ohaeng"] + rc["hoek_ohaeng"],
                 "%s,%s" % (rb["radical_ohaeng"], rc["radical_ohaeng"]),
                 ",".join(cm["flags"])]
        out.append("\t".join(cells))
    return out


def grouped_items(ctx, a, cand_b, cand_c):
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
    return items


def grouped_rows_md(ctx, a, cand_b, cand_c, only_all_gil=False):
    """(B,C) 원획 쌍별로 묶은 전수표 — 모든 조합을 빠짐없이 복원할 수 있다."""
    items = grouped_items(ctx, a, cand_b, cand_c)
    head = ["순위", "B·C"] + [LABEL[k] for k in ORDER] + ["길"]
    if ctx.has_dae:
        head.append("大吉")
    head += ["음양", "이름1 후보", "이름2 후보", "조합 수"]
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for it in items:
        s = it["s"]
        if only_all_gil and not s["all_gil"]:
            continue
        cells = [("★" if s["all_gil"] else "") + str(it["rank"]),
                 ("**%d·%d**" if s["all_gil"] else "%d·%d") % (it["b"], it["c"])] + \
                [fmt_g(s["nums"][k], s["grades"][k]) for k in ORDER] + ["%d/4" % s["n_gil"]]
        if ctx.has_dae:
            cells.append(str(s["n_dae"]))
        cells += [s["yy"] + (" " + s["yy_flag"] if s["yy_flag"] else ""),
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
    head = ["순위", "B·C"] + [LABEL[k] for k in ORDER]
    if ctx.has_dae:
        head.append("大吉")
    head += ["음양", "획수오행 A·B·C"]
    with_chars = cand_b is not None
    if with_chars:
        head += ["이름1 후보", "이름2 후보"]
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for it in items:
        s = it["s"]
        cells = [str(it["rank"]), "%d·%d" % (it["b"], it["c"])] + \
                [fmt_g(s["nums"][k], s["grades"][k]) for k in ORDER]
        if ctx.has_dae:
            cells.append(str(s["n_dae"]))
        cells += [s["yy"] + (" " + s["yy_flag"] if s["yy_flag"] else ""),
                  seq_str([ohaeng_of(a), ohaeng_of(it["b"]), ohaeng_of(it["c"])])]
        if with_chars:
            cells += ["".join(it["hb"]) or "-", "".join(it["hc"]) or "-"]
        out.append("| " + " | ".join(cells) + " |")
    return out, items


# ---------------------------------------------------------------- 모드: 글자 목록

def list_readings_md(rows, readings, use_dueum, heading="###"):
    out = []
    for rd in readings:
        cand = candidates(rows, rd, use_dueum)
        cand.sort(key=lambda x: (x["row"]["wonhoek"], x["row"]["codepoint"]))
        out.append("%s '%s' — %d자" % (heading, rd, len(cand)))
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


# ---------------------------------------------------------------- 머리말·보고서

def header_lines(args, rows, suri_info, ctx):
    overrides, missing = suri_info
    ov = ", ".join("%d=%s" % kv for kv in sorted(overrides.items())) or "없음"
    grades = [ctx.suri[n]["grade"] for n in range(1, 82)]
    cnt = {g: grades.count(g) for g in ("大吉", "吉", "반길반흉", "凶", "大凶", "미정") if g in grades}
    return [
        "- 사격 공식: 원격 = B+C, 형격 = A+B, 이격 = A+C, 정격 = A+B+C (81을 넘으면 80을 뺀다)",
        "- 원획표: `%s` (sha256 `%s`, %d자)" % (
            os.path.basename(args.table), sha256_of(args.table), len(rows)),
        "- 수리표: `%s` (sha256 `%s`) — %s. 덮어쓴 값: %s, 미정: %s" % (
            os.path.basename(args.suri), sha256_of(args.suri),
            " · ".join("%s %d" % kv for kv in cnt.items()), ov, missing or "없음"),
        "- 반길반흉 처리: %s" % ("길로 셈(--half-as-gil)" if args.half_as_gil else "길로 세지 않음"),
    ]


def report_md(args, rows, ctx, suri_info, a, surname_disp, s_reading, cand_b, cand_c):
    combos = build_combos(ctx, a, cand_b, cand_c)
    ranked = rank_combos(combos)
    allgil = [c for c in ranked if c["s"]["all_gil"]]
    items = grouped_items(ctx, a, cand_b, cand_c)
    pairs_all = [it for it in items if it["s"]["all_gil"]]
    practical = [c for c in allgil if c["practical"]]
    dist = {}
    for c in combos:
        dist[c["s"]["n_gil"]] = dist.get(c["s"]["n_gil"], 0) + 1
    title = args.title or "%s + %s + %s 인명용 한자 조합 전수표" % (surname_disp, args.first, args.second)
    sb = sound_ohaeng(args.first, args.sound_school)
    sc = sound_ohaeng(args.second, args.sound_school)
    sa = sound_ohaeng(s_reading, args.sound_school) if s_reading else ""

    out = ["# " + title, "",
           "<!-- name_search.py --report 생성물. 직접 고치지 말고 다시 실행할 것. -->", ""]
    if args.command_note:
        out += ["재현 명령(저장소 루트에서 실행):", "", "```bash", args.command_note, "```", ""]
    out += ["## 0. 조건", ""] + header_lines(args, rows, suri_info, ctx) + [
        "- 대상 한자: 원획표의 `inmyeong_readings`(Unihan `kHangul`의 N·E 표지)에 그 발음이 있는 글자%s." % (
            ", 두음법칙 변형 발음 포함" if args.dueum else ""),
        "- 발음오행(%s): %s" % (SOUND_SCHOOL_LABEL[args.sound_school],
                              seq_str([sa, sb, sc]) if sa else seq_str([sb, sc])),
        "- 이 표가 판단하지 않는 것: 한자 뜻의 좋고 나쁨, 불용문자, 사주 용신. 훈음은 libhangul 사전 값이며 대법원 지정 훈이 아니다.",
        ""]
    out += ["## 1. 요약", "",
            "| 항목 | 값 |", "|---|---|",
            "| 성 | %s (원획 %d) |" % (surname_disp, a),
            "| '%s' 한자 수 | %d자 |" % (args.first, len(cand_b)),
            "| '%s' 한자 수 | %d자 |" % (args.second, len(cand_c)),
            "| 전체 조합 | **%d개** |" % len(combos),
            "| 네 격 모두 吉 | **%d개** (획수 쌍 %d쌍 / 전체 %d쌍) |" % (
                len(allgil), len(pairs_all), len(items)),
            "| 길수 개수 분포 | %s |" % ", ".join(
                "%d/4 → %d개" % (k, dist[k]) for k in sorted(dist, reverse=True)),
            "| 실무 참고 조합(4절 조건) | %d개 |" % len(practical),
            ""]
    out += ["## 2. 발음별 인명용 한자", "",
            "- ⚠ = 원획 옥편 대조 권장(`wonhoek_check` = Y). 규칙·플래그 뜻은 `skills/korean-naming/data/README.md` 4절.",
            "- KS(글자/발음): 앞은 글자가 KS X 1001/1002에 있는지, 뒤는 바로 그 발음으로 실렸는지다.",
            ""]
    out += list_readings_md(rows, [args.first, args.second], args.dueum, heading="###")
    out += ["## 3. 획수 쌍별 전수표", "",
            "각 행의 '이름1 후보 × 이름2 후보'가 그 획수 쌍의 모든 한자 조합이다. ★ = 네 격 모두 吉.", ""]
    out += grouped_rows_md(ctx, a, cand_b, cand_c)[0] + [""]
    out += ["## 4. 네 격 모두 吉인 조합 — 전체 %d개" % len(allgil), "",
            "### 4-1. 실무 참고표 (%d개)" % len(practical), "",
            "조건: 두 글자 모두 KS X 1001 수록 또는 교육용 기초한자이고, 원획 확인 플래그(획확인)가 없다. "
            "日·순양·순음·KS음외 플래그는 걸러 내지 않고 표에 보인다. 뜻은 사람이 따로 판단한다.", ""]
    out += combo_rows_md(ctx, a, practical, surname_disp, show_def=True) + [""]
    out += ["### 4-2. 네 격 모두 吉 전체 (%d개)" % len(allgil), ""]
    out += combo_rows_md(ctx, a, allgil, surname_disp, show_def=True) + [""]
    by_strokes = sorted(ranked, key=lambda x: (x["b"]["row"]["wonhoek"], x["c"]["row"]["wonhoek"],
                                               x["b"]["row"]["codepoint"], x["c"]["row"]["codepoint"]))
    out += ["## 5. 전체 조합표 (%d개, 원획 순)" % len(combos), "",
            "순위는 (길수 개수, 등급 점수, 음양) 기준 경쟁 순위다. 3단계 수리표에서는 네 격 모두 吉인 조합이 모두 같은 순위다.", ""]
    out += combo_rows_md(ctx, a, by_strokes, surname_disp, show_def=False)
    return out


# ---------------------------------------------------------------- main

def repro_command(argv):
    """실행 인자로 재현 명령 문자열을 만든다(저장소 루트 기준 경로, --command-note 제외)."""
    keep, skip = [], False
    for tok in argv:
        if skip:
            skip = False
            continue
        if tok == "--command-note":
            skip = True
            continue
        if tok.startswith("--command-note="):
            continue
        keep.append(tok)
    return "python3 skills/korean-naming/scripts/name_search.py " + " ".join(shlex.quote(t) for t in keep)


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
    ap.add_argument("--suri-override", default="", help="특정 수의 판정을 바꿔 봄. 예: '51=길,71=흉'")
    ap.add_argument("--check-suri", action="store_true", help="수리표가 1~81을 빠짐없이 읽히는지 점검")
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
    ap.add_argument("--practical", action="store_true",
                    help="KS X 1001 수록 또는 교육용이면서 획확인 플래그가 없는 글자만")
    ap.add_argument("--all-gil", action="store_true", help="네 격 모두 길인 조합만")
    ap.add_argument("--group-strokes", action="store_true", help="(B,C) 원획 쌍별로 묶어 출력")
    ap.add_argument("--stroke-pairs", action="store_true", help="네 격 모두 길인 (B,C) 획수 쌍 목록")
    ap.add_argument("--max-stroke", type=int, default=30, help="--stroke-pairs 범위 상한(기본 30)")
    ap.add_argument("--list-readings", default="", help="쉼표로 구분한 발음의 인명용 한자 목록")
    ap.add_argument("--report", action="store_true", help="조합 전수 보고서(Markdown) 한 문서로 출력")
    ap.add_argument("--title", default="", help="출력 맨 위에 붙일 제목(# 제목)")
    ap.add_argument("--command-note", default="",
                    help="머리말에 적을 재현 명령(기본: 실제 실행 인자로 자동 작성)")
    ap.add_argument("--sort", choices=["score", "strokes"], default="score")
    ap.add_argument("--limit", type=int, default=0, help="출력 행 수 제한(0=전부)")
    ap.add_argument("--format", choices=["md", "tsv"], default="md")
    ap.add_argument("--show-def", action="store_true", help="영문 뜻 열 추가")
    ap.add_argument("--sound-school", choices=["project", "haerye"], default="project")
    ap.add_argument("--no-header", action="store_true", help="머리말(조건·통계) 생략")
    ap.add_argument("--out", default="-", help="출력 파일(기본: 표준출력)")
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = ap.parse_args(raw_argv)
    if not args.command_note:
        args.command_note = repro_command(raw_argv)

    overrides = parse_overrides(args.suri_override)
    suri, missing, dups = load_suri(args.suri, overrides)
    if missing:
        sys.stderr.write("경고: 수리표에 값이 없는 수 %s → '미정'(길 아님)으로 처리\n" % missing)
    if dups:
        sys.stderr.write("경고: 수리표에 두 번 나온 수 %s → 첫 행만 사용\n" % dups)
    ctx = Ctx(suri, args.half_as_gil)

    if args.check_suri:
        counts = {}
        for n in range(1, 82):
            counts.setdefault(suri[n]["grade"], []).append(n)
        for g in ("大吉", "吉", "반길반흉", "凶", "大凶", "미정"):
            if g in counts:
                print("%s %d: %s" % (g, len(counts[g]), ", ".join(map(str, counts[g]))))
        no_name = [n for n in range(1, 82) if suri[n]["src"] == "table" and not suri[n]["name"]]
        if no_name:
            print("격명 없음: %s" % no_name)
        print("sha256 %s" % sha256_of(args.suri))
        return 1 if (missing or dups) else 0

    rows = load_table(args.table)
    a, s_hanja, s_reading = resolve_surname(rows, args.surname)
    s_hanja = args.surname_hanja or s_hanja or ""
    s_reading = args.surname_reading or s_reading
    surname_disp = s_hanja or "[%d]" % a

    only_b = set(args.first_hanja) if args.first_hanja else None
    only_c = set(args.second_hanja) if args.second_hanja else None
    cand_b = candidates(rows, args.first, args.dueum, only_b) if args.first else None
    cand_c = candidates(rows, args.second, args.dueum, only_c) if args.second else None

    def narrow(cands, pred):
        return [x for x in cands if pred(x)] if cands is not None else None
    if args.exclude_check:
        cand_b, cand_c = (narrow(x, lambda c: not c["row"]["_check"]) for x in (cand_b, cand_c))
    if args.ks_only:
        cand_b, cand_c = (narrow(x, lambda c: c["ks"] == "1001") for x in (cand_b, cand_c))
    if args.practical:
        cand_b, cand_c = (narrow(x, is_practical) for x in (cand_b, cand_c))

    # 모드 4: 보고서
    if args.report:
        if cand_b is None or cand_c is None:
            ap.error("--report 에는 --first 와 --second 가 필요하다")
        return emit(report_md(args, rows, ctx, (overrides, missing), a, surname_disp,
                              s_reading, cand_b, cand_c), args.out)

    out = []
    if args.title and args.format == "md":
        out += ["# " + args.title, ""]
    if not args.no_header and args.format == "md":
        out.append("<!-- name_search.py 생성물. 직접 고치지 말고 다시 실행할 것. -->")
        out.append("")
        if args.command_note:
            out += ["재현 명령(저장소 루트에서 실행):", "", "```bash", args.command_note, "```", ""]
        out += header_lines(args, rows, (overrides, missing), ctx)
        out.append("")

    # 모드 3: 글자 목록
    if args.list_readings:
        readings = [x.strip() for x in args.list_readings.split(",") if x.strip()]
        out += list_readings_md(rows, readings, args.dueum)
        return emit(out, args.out)

    # 모드 2: 획수 쌍
    if args.stroke_pairs:
        lines, items = stroke_pairs(ctx, a, args.max_stroke,
                                    cand_b if cand_b is not None and cand_c is not None else None,
                                    cand_c if cand_b is not None and cand_c is not None else None)
        if args.format == "md" and not args.no_header:
            out.append("A=%d, B·C ∈ 1..%d 에서 네 격이 모두 吉인 쌍: **%d개** (전체 %d쌍)" % (
                a, args.max_stroke, len(items), args.max_stroke ** 2))
            out.append("")
        out += lines
        return emit(out, args.out)

    # 모드 1: 조합
    if cand_b is None or cand_c is None:
        ap.error("--first 와 --second 가 필요하다 (또는 --stroke-pairs / --list-readings / --check-suri)")
    combos = build_combos(ctx, a, cand_b, cand_c)
    rank_combos(combos)   # 순위는 정렬 방식과 무관하게 수리 키로 매긴다
    if args.sort == "strokes":
        combos.sort(key=lambda x: (x["b"]["row"]["wonhoek"], x["c"]["row"]["wonhoek"],
                                   x["b"]["row"]["codepoint"], x["c"]["row"]["codepoint"]))
    else:
        combos.sort(key=lambda x: x["sort_key"])
    n_total = len(combos)
    n_allgil = sum(1 for c in combos if c["s"]["all_gil"])

    if args.format == "md" and not args.no_header:
        sb = sound_ohaeng(args.first, args.sound_school)
        sc = sound_ohaeng(args.second, args.sound_school)
        sa = sound_ohaeng(s_reading, args.sound_school) if s_reading else ""
        out.append("성 %s(원획 %d) + '%s'(%d자) + '%s'(%d자) → 전체 조합 **%d개**, 네 격 모두 吉 **%d개**" % (
            surname_disp, a, args.first, len(cand_b), args.second, len(cand_c), n_total, n_allgil))
        out.append("")
        if sa:
            out.append("발음오행(%s): %s%s%s = %s" % (
                SOUND_SCHOOL_LABEL[args.sound_school], s_reading, args.first, args.second,
                seq_str([sa, sb, sc])))
        else:
            out.append("발음오행(%s, 이름만): %s%s = %s" % (
                SOUND_SCHOOL_LABEL[args.sound_school], args.first, args.second, seq_str([sb, sc])))
        dist = {}
        for c in combos:
            dist[c["s"]["n_gil"]] = dist.get(c["s"]["n_gil"], 0) + 1
        out.append("")
        out.append("길수 개수 분포: " + ", ".join("%d/4 → %d개" % (k, dist[k]) for k in sorted(dist, reverse=True)))
        out.append("")

    if args.group_strokes:
        lines, _ = grouped_rows_md(ctx, a, cand_b, cand_c, only_all_gil=args.all_gil)
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
        d = os.path.dirname(path)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
