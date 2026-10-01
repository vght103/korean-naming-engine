#!/usr/bin/env python3
"""새 이름 후보 선별·비교표 생성기 (candidate_screen.py)

출생신고 이름 통계(2008–2019 누적)에서 실제로 쓰이는 두 글자 이름을 모으고,
유행 음절을 뺀 뒤, 성 吳(원획 7)과 붙였을 때 아래 조건을 모두 통과하는 인명용
한자 조합이 하나라도 있는 이름을 '후보군'으로 고른다. 그다음 사람이 뜻을 보고 고른
후보 목록(data/new_candidates_*.tsv)을 같은 조건으로 다시 검사해 비교표를 만든다.
수리·원획·오행 계산은 name_search.py 의 함수를 그대로 쓴다. 표준 라이브러리만 쓰며,
같은 입력이면 같은 출력을 낸다.

선별 조건 (조합 단위)
    1. 사격(원 B+C, 형 A+B, 이 A+C, 정 A+B+C) 네 수가 모두 吉 (반길반흉은 길 아님)
    2. 음양: 원획 A·B·C 가 순양(모두 홀수)·순음(모두 짝수)이 아님
    3. 획수오행(원획 끝자리): A–B, B–C 이웃 사이에 상극 없음
    4. 발음오행: 운해본·해례본 두 배속 모두에서 성–이름1, 이름1–이름2 사이에 상극 없음
    5. 자원오행(부수 휴리스틱): 이름 두 글자 사이에 상극 없음('金/土'처럼 갈리면 어느 쪽으로든
       상극이면 제외, 빈칸은 관계 없음으로 본다). 부수 오행이 火이거나 日부수인 글자는 제외
    6. 글자: KS X 1001 에 바로 그 발음으로 수록, 원획 확인 플래그(wonhoek_check) 없음

선별 조건 (이름 단위, --scan)
    - 통계 누적 인원(여+남)이 --min-total 이상 --max-total 이하
    - --exclude-syllables 의 음절을 하나라도 포함하면 제외(유행 음절)
    - --avoid-first 의 음절로 시작하면 제외(성과 붙어 다른 말이 되는 경우. 기본 '해' → '오해~')

이 스크립트가 판단하지 않는 것: 한자 뜻의 좋고 나쁨, 불용문자, 사주 용신. 후보 목록의
풀이(gloss·note)는 사람이 쓴 해석이며 입력 파일에 있다.

사용 예 (저장소 루트에서)
    python3 skills/korean-naming/scripts/candidate_screen.py \\
        --stats f.csv,m.csv --candidates skills/korean-naming/data/new_candidates_2026-10.tsv \\
        --out docs/새후보/후보10_비교표.md
"""

import argparse
import csv
import os
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import name_search as ns  # noqa: E402

SURNAME, SURNAME_READING = "吳", "오"
SCHOOLS = ("project", "haerye")
DEFAULT_EXCLUDE = "율린아온슬리루로결안윤준서하우이"
STATS_URL = "https://raw.githubusercontent.com/randkid/name/8f367547e0f6280df066fe35cfec259f5acf75f6/%s.csv"


def load_stats(spec):
    """'f.csv,m.csv' → {이름: [여, 남]} (두 글자 이름만)."""
    paths = spec.split(",")
    if len(paths) != 2:
        raise SystemExit("--stats 는 '여아csv,남아csv' 두 경로다")
    cnt = {}
    for i, p in enumerate(paths):
        with open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if len(r["name"]) == 2:
                    cnt.setdefault(r["name"], [0, 0])[i] += int(r["weight"])
    return cnt, paths


def no_geuk(seq):
    return all(ns.relation(seq[i], seq[i + 1]) != "극" for i in range(len(seq) - 1))


def sound_seq(name, school):
    return [ns.sound_ohaeng(s, school) for s in SURNAME_READING + name]


def radical_rel(x, y):
    """자원오행 관계. '金/土'처럼 갈리면 가능한 관계를 모두 모은다. 빈칸은 관계 없음."""
    if not x or not y:
        return set()
    return {ns.relation(a, b) for a in x.split("/") for b in y.split("/")}


def char_ok(cd):
    r = cd["row"]
    return (cd["ks_read"] == "1001" and not r["_check"]
            and r["radical_ohaeng"] != "火" and r["radical_no"] != 72)


def checks(ctx, a, cb, cc):
    """조합 하나의 조건별 통과 여부(순서 = 모듈 설명의 1~6)."""
    rb, rc = cb["row"], cc["row"]
    s = ctx.sagyeok(a, rb["wonhoek"], rc["wonhoek"])
    hk = [ns.ohaeng_of(x) for x in (a, rb["wonhoek"], rc["wonhoek"])]
    name = cb["reading"] + cc["reading"]
    return s, {
        "사격": s["all_gil"],
        "음양": not s["yy_flag"],
        "획수오행": no_geuk(hk),
        "발음오행": all(no_geuk(sound_seq(name, sc)) for sc in SCHOOLS),
        "자원오행": "극" not in radical_rel(rb["radical_ohaeng"], rc["radical_ohaeng"]),
        "글자": char_ok(cb) and char_ok(cc),
    }


def scan(rows, ctx, a, stats, args):
    cache = {}

    def cands(syl):
        if syl not in cache:
            cache[syl] = [c for c in ns.candidates(rows, syl) if char_ok(c)]
        return cache[syl]

    excl = set(args.exclude_syllables)
    tally = {"전체 두 글자 이름": len(stats)}
    step = [n for n, (f, m) in stats.items() if args.min_total <= f + m <= args.max_total]
    tally["누적 인원 범위 안"] = len(step)
    step = [n for n in step if not set(n) & excl]
    tally["유행 음절 제외 후"] = len(step)
    step = [n for n in step if n[0] not in args.avoid_first]
    tally["성과 붙어 다른 말이 되는 경우 제외 후"] = len(step)
    step = [n for n in step if all(no_geuk(sound_seq(n, sc)) for sc in SCHOOLS)]
    tally["발음오행(두 배속) 통과"] = len(step)
    pool = []
    for n in step:
        k = 0
        for cb in cands(n[0]):
            for cc in cands(n[1]):
                if all(checks(ctx, a, cb, cc)[1].values()):
                    k += 1
        if k:
            pool.append((n, k))
    tally["조건을 모두 통과하는 한자 조합이 있음 = 후보군"] = len(pool)
    pool.sort(key=lambda x: (-(stats[x[0]][0] + stats[x[0]][1]), x[0]))
    return tally, pool


def lean(f, m):
    t = f + m
    if not t:
        return "-"
    if f / t >= 0.8:
        return "여아 %d%%" % round(100 * f / t)
    if m / t >= 0.8:
        return "남아 %d%%" % round(100 * m / t)
    return "중성(여 %d%%)" % round(100 * f / t)


def load_candidates(rows, path):
    by_hanja = {r["hanja"]: r for r in rows}
    out = []
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            h, g = r["hanja"], r["hangul"]
            cds = []
            for ch, rd in zip(h, g):
                if ch not in by_hanja:
                    raise SystemExit("원획표에 없는 글자: %s" % ch)
                cd = [c for c in ns.candidates(rows, rd) if c["row"]["hanja"] == ch]
                if not cd:
                    raise SystemExit("%s 는 인명용 발음 '%s'가 없다" % (ch, rd))
                cds.append(cd[0])
            out.append({"hanja": h, "hangul": g, "gloss": r["gloss"], "note": r["note"], "cds": cds})
    return out


def render(args, rows, ctx, suri_info, a, stats, stat_paths, tally, pool, cands):
    o = ["# 새 이름 후보 %d선 — 오(吳) + 두 글자 비교표" % len(cands), "",
         "<!-- candidate_screen.py 생성물. 직접 고치지 말고 다시 실행할 것. -->", "",
         "재현 명령(저장소 루트에서 실행):", "", "```bash"]
    if stats:
        o += ["curl -sSO %s" % (STATS_URL % "f"), "curl -sSO %s" % (STATS_URL % "m")]
    o += [args.command, "```", ""]
    o += ["## 0. 조건", ""] + ns.header_lines(args, rows, suri_info, ctx) + [
        "- 후보 풀이 입력: `%s`" % os.path.relpath(args.candidates),
        "- 성: %s(원획 %d), 발음오행은 운해본(ㅇㅎ 土)·해례본(ㅇㅎ 水)을 모두 검사한다." % (SURNAME, a),
        "- 출생 전 **조건부 비교**다. 사주 보완 여부는 아이 일주 확정 후 다시 판단한다. "
        "획수·발음·자원오행은 서로 다른 분류법이며 사주 오행 개수에 더하지 않는다.",
        ""]
    o += ["## 1. 선별 조건", "",
          "조합 단위(모두 통과해야 함):", "",
          "1. 사격 네 수가 모두 吉 (`suri_table.md` 정본, 반길반흉은 길 아님)",
          "2. 원획 A·B·C 가 순양·순음이 아님",
          "3. 획수오행 A–B, B–C 사이에 상극 없음 (기존 후보 오은상 金水金·오윤하 金金水와 같은 기준)",
          "4. 발음오행: 운해본·해례본 **두 배속 모두**에서 상극 없음 → 이름 첫 글자 초성이 ㅇ·ㅎ·ㅅ·ㅈ·ㅊ",
          "5. 자원오행: 이름 두 글자 사이 상극 없음. 火부수·日부수 글자 제외(주의사항 3)",
          "6. KS X 1001 에 그 발음으로 수록, 원획 확인 플래그 없음",
          ""]
    if stats:
        o += ["이름 단위(후보군 선별):", "",
              "- 출생신고 통계: randkid/name 커밋 `8f367547` (대법원 '선호하는 출생자 이름 현황' 2008–2019 합산) — `%s`" %
              "`, `".join(os.path.basename(p) for p in stat_paths),
              "- 누적 인원 %d ~ %d명 (너무 낯설거나 너무 흔한 이름 제외)" % (args.min_total, args.max_total),
              "- 유행 음절 제외: %s" % " ".join(args.exclude_syllables),
              "- 첫 음절 제외: %s (성과 붙어 '오해~'처럼 읽힘)" % " ".join(args.avoid_first),
              "", "| 단계 | 이름 수 |", "|---|---:|"]
        o += ["| %s | %d |" % kv for kv in tally.items()]
        o += ["", "후보군에서 뜻을 보고 고른 것이 아래 %d개다(사람의 선택). 후보군 전체는 부록에 있다." % len(cands), ""]

    o += ["## 2. 비교표", "",
          "| # | 이름 | 원획 A·B·C | 원격(B+C) | 형격(A+B) | 이격(A+C) | 정격(A+B+C) | 음양 | 획수오행 | "
          "발음오행 운해본 / 해례본 | 자원오행 B·C | 훈음(libhangul) | 출생신고 2008–19 (여/남) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    detail = []
    for i, c in enumerate(cands, 1):
        cb, cc = c["cds"]
        rb, rc = cb["row"], cc["row"]
        s, ck = checks(ctx, a, cb, cc)
        n = s["nums"]
        hk = [ns.ohaeng_of(x) for x in (a, rb["wonhoek"], rc["wonhoek"])]
        snd = " / ".join(ns.seq_str(sound_seq(c["hangul"], sc)) for sc in SCHOOLS)
        st = stats.get(c["hangul"]) if stats else None
        st_s = "%d / %d · %s" % (st[0], st[1], lean(*st)) if st else "-"
        gy = ["%d %s %s" % (n[k], ctx.suri[ns.reduce81(n[k])]["name"].split("(")[0], s["grades"][k])
              for k in ("원", "형", "이", "정")]
        o.append("| %d | **오%s %s%s** | %d·%d·%d | %s | %s | %s | %s | %s | %s | %s | %s·%s | %s / %s | %s |" % (
            i, c["hangul"], SURNAME, c["hanja"], a, rb["wonhoek"], rc["wonhoek"],
            gy[0], gy[1], gy[2], gy[3], s["yy"], ns.seq_str(hk), snd,
            rb["radical_ohaeng"] or "-", rc["radical_ohaeng"] or "-",
            ns.short_hun(rb), ns.short_hun(rc), st_s))
        bad = [k for k, v in ck.items() if not v]
        detail.append((i, c, rb, rc, cb, cc, bad))
    o += ["", "- 자원오행 '-'는 부수 관행이 없는 글자다(관계 판단에서 빼고 본다).",
          "- 훈음은 libhangul 사전 첫 뜻이라 대법원 지정 훈과 다를 수 있다.", ""]

    o += ["## 3. 조건 검사와 글자 정보", "",
          "| # | 이름 | 조건 1~6 | 코드포인트 | 교육용 | 부수 | 뜻(해석) | 비고 |",
          "|---|---|---|---|---|---|---|---|"]
    for i, c, rb, rc, cb, cc, bad in detail:
        o.append("| %d | %s%s | %s | %s · %s | %s · %s | %s · %s | %s | %s |" % (
            i, SURNAME, c["hanja"], "모두 통과" if not bad else "✗ " + ", ".join(bad),
            rb["codepoint"], rc["codepoint"],
            "Y" if rb["education"] == "Y" else "N", "Y" if rc["education"] == "Y" else "N",
            rb["radical_char"], rc["radical_char"], c["gloss"], c["note"]))
    o += ["", "뜻·비고 칸은 입력 파일에 사람이 쓴 해석이다. 출생신고 직전에는 "
          "[대법원 인명용 한자 조회](https://efamily.scourt.go.kr/cs/CsBltnWrtList.do?bltnbordId=0000010)로 "
          "자형과 지정 발음을 다시 확인한다.", ""]

    o += ["## 4. 한계", "",
          "1. 이름 통계는 2019년까지 누적이라 2020년 이후 새로 유행한 이름은 반영되지 않는다. 유행 음절 목록은 판단으로 정했다.",
          "2. 대상 한자는 2018년 대법원 목록까지다(`data/README.md`). 2024-06-11 시행 9,389자 추가분은 없다.",
          "3. 자원오행은 부수 휴리스틱이고, 조건 4·5는 이 프로젝트가 고른 보수적 기준이다. 유파에 따라 다르게 볼 수 있다.",
          "4. 이름이 운명·건강·재물을 정한다고 보지 않는다. 표는 전통 분류값의 비교일 뿐이다.",
          ""]
    if pool:
        o += ["## 부록. 후보군 전체 (%d개, 누적 인원 순)" % len(pool), "",
              "| 이름 | 여 / 남 | 조건을 모두 통과하는 한자 조합 수 |", "|---|---|---:|"]
        o += ["| %s | %d / %d | %d |" % (n, stats[n][0], stats[n][1], k) for n, k in pool]
    return o


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(description="새 이름 후보 선별·비교표")
    ap.add_argument("--table", default=ns.DEFAULT_TABLE)
    ap.add_argument("--suri", default=ns.DEFAULT_SURI)
    ap.add_argument("--stats", default="", help="여아csv,남아csv (randkid/name f.csv, m.csv)")
    ap.add_argument("--candidates", required=True, help="후보 TSV (hanja, hangul, gloss, note)")
    ap.add_argument("--min-total", type=int, default=100)
    ap.add_argument("--max-total", type=int, default=6000)
    ap.add_argument("--exclude-syllables", default=DEFAULT_EXCLUDE)
    ap.add_argument("--avoid-first", default="해")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)
    args.half_as_gil = False
    args.command = "python3 skills/korean-naming/scripts/candidate_screen.py " + " ".join(
        shlex.quote(t) for t in argv)

    rows = ns.load_table(args.table)
    suri, missing, _ = ns.load_suri(args.suri, {})
    ctx = ns.Ctx(suri, False)
    a = next(r["wonhoek"] for r in rows if r["hanja"] == SURNAME)
    stats, paths, tally, pool = {}, [], {}, []
    if args.stats:
        stats, paths = load_stats(args.stats)
        tally, pool = scan(rows, ctx, a, stats, args)
    cands = load_candidates(rows, args.candidates)
    lines = render(args, rows, ctx, ({}, missing), a, stats, paths, tally, pool, cands)
    text = "\n".join(lines) + "\n"
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
    for c in cands:
        _, ck = checks(ctx, a, *c["cds"])
        if not all(ck.values()):
            print("경고: %s 가 조건을 통과하지 못함: %s" % (
                c["hanja"], [k for k, v in ck.items() if not v]), file=sys.stderr)
    if pool:
        names = {n for n, _ in pool}
        for c in cands:
            if c["hangul"] not in names:
                print("경고: '%s' 는 후보군 밖이다" % c["hangul"], file=sys.stderr)


if __name__ == "__main__":
    main()
