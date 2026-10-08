#!/usr/bin/env python3
"""두 계보 도구 교차 대조기 (2026-10-08 추가, docs/도구_교차검증.md 의 재현 도구).

이 스킬(saju-myeongri)의 saju_calc.py·name_suri.py 와
정본 스킬(korean-naming)의 saju_calc.py·name_search.py 를 같은 입력으로 실행해
출력만 나란히 놓고 일치/불일치를 센다. 계산은 하지 않는다 — 두 도구의 출력을 비교할 뿐이다.

- 사주: 연·월·일주 비교. 시각은 12:00 으로 통일. 정본 도구는 --jie-source sxtwl.
- 수리: 지정 이름 6건의 사격·길흉, 1~81 각 수의 길흉, 81 초과 환원 규칙.
  * 이 스킬의 81수리 판정은 name_suri.py 의 suri() 함수를 불러 읽는다(CLI 로는 수 하나만 뽑을 수 없음).
  * 정본 판정은 name_search.py --check-suri 출력(CLI)과 reduce81() 함수에서 읽는다.

사용법:
  python3 skills/saju-myeongri/scripts/cross_check_tools.py            # Markdown 보고 출력
  python3 skills/saju-myeongri/scripts/cross_check_tools.py --tsv DIR  # 원자료 TSV 도 DIR 에 저장
표준 라이브러리만 쓴다. sxtwl 은 두 사주 도구가 필요로 한다.
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SM = HERE                                                     # saju-myeongri/scripts
KN = os.path.normpath(os.path.join(HERE, "..", "..", "korean-naming", "scripts"))
SM_SAJU = os.path.join(SM, "saju_calc.py")
SM_SURI = os.path.join(SM, "name_suri.py")
KN_SAJU = os.path.join(KN, "saju_calc.py")
KN_SEARCH = os.path.join(KN, "name_search.py")

U_SANG = "尙"  # 尙 (U+5C19). 尚(U+5C1A) 아님


def run(cmd):
    p = subprocess.run([sys.executable] + cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("실패: %s\n%s" % (" ".join(cmd), p.stderr))
    return p.stdout


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ 사주

def sm_saju(d, t, gender):
    out = json.loads(run([SM_SAJU, "--date", d, "--time", t, "--gender", gender]))
    s = out["사주"]
    r = {"연": s["년주"]["한자"], "월": s["월주"]["한자"], "일": s["일주"]["한자"],
         "시": s.get("시주", {}).get("한자", ""), "음력": out["음력"]}
    return r


def kn_saju(d, t):
    out = json.loads(run([KN_SAJU, "--date", d, "--time", t, "--jie-source", "sxtwl", "--json"]))
    s = out["사주"]
    r = {"연": s["연주"]["간지"], "월": s["월주"]["간지"], "일": s["일주"]["간지"],
         "시": s.get("시주", {}).get("간지", ""), "음력": out["음력"],
         "직전절": out["절기"]["직전 절"], "다음절": out["절기"]["다음 절"],
         "대안": "; ".join("%s→월%s" % (x.get("사유", ""), x.get("월주", "")) for x in out.get("대안", []))}
    return r


def saju_rows():
    rows = []
    rows.append(("아버지", "1990-06-27", "12:00", "M"))
    rows.append(("어머니", "1994-06-17", "12:00", "F"))
    d = date(2026, 11, 1)
    while d <= date(2026, 12, 10):
        rows.append(("아이 구간", d.isoformat(), "12:00", "F"))
        d += timedelta(days=1)
    return rows


BOUNDARY_DATES = {"2026-11-06", "2026-11-07", "2026-11-08", "2026-12-06", "2026-12-07", "2026-12-08"}

# 보조 탐침: 절입 시각 앞뒤(판정 대상 아님). 입동 18:52 · 대설 11:53 (KASI 공표, R CLAUDE.md)
PROBES = [("2026-11-06", "23:45"), ("2026-11-07", "18:00"), ("2026-11-07", "19:30"),
          ("2026-12-06", "23:45"), ("2026-12-07", "11:00"), ("2026-12-07", "12:30")]

# 참고: 부모 전해진 시각(시주는 분석 제외 — 판정 대상 아님)
PARENT_TIMES = [("아버지", "1990-06-27", "19:30", "M"), ("어머니", "1994-06-17", "15:00", "F")]


def saju_section(tsv_dir):
    lines = ["## 사주 대조 (12:00 통일, 연·월·일주)", ""]
    recs, mism = [], []
    for who, d, t, g in saju_rows():
        a, b = sm_saju(d, t, g), kn_saju(d, t)
        diff = [k for k in ("연", "월", "일") if a[k] != b[k]]
        recs.append((who, d, t, a, b, diff))
        if diff:
            mism.append((who, d, t, a, b, diff))
    n = len(recs)
    pillars = n * 3
    bad_p = sum(len(r[5]) for r in recs)
    lines.append("- 입력 %d건(부모 2 + 2026-11-01~12-10 %d일), 비교 기둥 %d개" % (n, n - 2, pillars))
    lines.append("- 일치 %d건 / 불일치 %d건 (기둥 기준 일치 %d / 불일치 %d)"
                 % (n - len(mism), len(mism), pillars - bad_p, bad_p))
    for k in ("연", "월", "일"):
        lines.append("  - %s주 불일치 %d건" % (k, sum(1 for r in recs if k in r[5])))
    lines.append("")
    lines.append("### 불일치 전부")
    lines.append("")
    if not mism:
        lines.append("없음")
    else:
        lines.append("| 대상 | 날짜 시각 | 기둥 | saju-myeongri | korean-naming(sxtwl) | korean-naming 직전 절 / 다음 절 |")
        lines.append("|---|---|---|---|---|---|")
        for who, d, t, a, b, diff in mism:
            for k in diff:
                lines.append("| %s | %s %s | %s주 | %s | %s | %s / %s |"
                             % (who, d, t, k, a[k], b[k], b["직전절"], b["다음절"]))
    lines.append("")
    lines.append("### 절입 경계일 (11-06·07·08, 12-06·07·08) 12:00")
    lines.append("")
    lines.append("| 날짜 | saju-myeongri 연·월·일 | korean-naming 연·월·일 | 일치 | korean-naming 대안 표기 |")
    lines.append("|---|---|---|---|---|")
    for who, d, t, a, b, diff in recs:
        if d in BOUNDARY_DATES:
            lines.append("| %s | %s·%s·%s | %s·%s·%s | %s | %s |"
                         % (d, a["연"], a["월"], a["일"], b["연"], b["월"], b["일"],
                            "불일치(" + "·".join(diff) + ")" if diff else "일치", b["대안"] or "-"))
    lines.append("")
    lines.append("### 보조 탐침 — 절입 시각 앞뒤 (판정 대상 아님)")
    lines.append("")
    lines.append("| 날짜 시각 | saju-myeongri 월주·일주 | korean-naming 월주·일주 | 월주 | 일주 |")
    lines.append("|---|---|---|---|---|")
    for d, t in PROBES:
        a, b = sm_saju(d, t, "F"), kn_saju(d, t)
        lines.append("| %s %s | %s·%s | %s·%s | %s | %s |"
                     % (d, t, a["월"], a["일"], b["월"], b["일"],
                        "일치" if a["월"] == b["월"] else "불일치", "일치" if a["일"] == b["일"] else "불일치"))
    lines.append("")
    lines.append("### 참고 — 부모 전해진 시각의 시주 (D3: 분석 제외, 판정 대상 아님)")
    lines.append("")
    lines.append("| 대상 | 날짜 시각 | saju-myeongri 연·월·일·시 | korean-naming 연·월·일·시 | 시주 일치 |")
    lines.append("|---|---|---|---|---|")
    for who, d, t, g in PARENT_TIMES:
        a, b = sm_saju(d, t, g), kn_saju(d, t)
        lines.append("| %s | %s %s | %s·%s·%s·%s | %s·%s·%s·%s | %s |"
                     % (who, d, t, a["연"], a["월"], a["일"], a["시"], b["연"], b["월"], b["일"], b["시"],
                        "일치" if a["시"] == b["시"] else "불일치"))
    lines.append("")
    # saju-myeongri 음력 표기 'YYYY-MM-DD' (+ ' (윤달)') → 앞 10자만 비교
    lunar_diff = sum(1 for r in recs if r[3]["음력"][:10].replace("-", "") != _kn_lunar_norm(r[4]["음력"]))
    lines.append("- 참고: 음력 표기(두 도구 모두 sxtwl 중국 음력) 불일치 %d건 / %d건" % (lunar_diff, n))
    lines.append("")
    if tsv_dir:
        with open(os.path.join(tsv_dir, "saju_rows.tsv"), "w", encoding="utf-8") as f:
            f.write("who\tdate\ttime\tsm_year\tsm_month\tsm_day\tkn_year\tkn_month\tkn_day\tdiff\n")
            for who, d, t, a, b, diff in recs:
                f.write("\t".join([who, d, t, a["연"], a["월"], a["일"], b["연"], b["월"], b["일"], ",".join(diff)]) + "\n")
    return lines


def _kn_lunar_norm(s):
    # '2026년 9월 29일' / '1990년 윤5월 5일' → '20260929' 형태 (윤달 표기는 따로 비교하지 않음)
    import re
    m = re.match(r"(\d+)년 (윤)?(\d+)월 (\d+)일", s)
    if not m:
        return s
    return "%s%02d%02d" % (m.group(1), int(m.group(3)), int(m.group(4)))


# ------------------------------------------------------------------ 수리

NAMES = [
    ("오하송", "吳河松", "하", "송", "河", "松", (7, 9, 8)),
    ("오송하", "吳松河", "송", "하", "松", "河", (7, 8, 9)),
    ("오송하", "吳松霞", "송", "하", "松", "霞", (7, 8, 17)),
    ("오채윤", "吳采潤", "채", "윤", "采", "潤", (7, 8, 16)),
    ("오은상", "吳垠" + U_SANG, "은", "상", "垠", U_SANG, (7, 9, 8)),
    ("오아진", "吳亞眞", "아", "진", "亞", "眞", (7, 8, 10)),
]
SM_GRADE = {"길": "吉", "흉": "凶", "반길반흉": "반길반흉"}


def kn_name(first, second, fh, sh):
    out = run([KN_SEARCH, "--surname", "吳", "--first", first, "--second", second,
               "--first-hanja", fh, "--second-hanja", sh, "--format", "tsv"])
    lines = [l for l in out.splitlines() if l.strip()]
    head = lines[0].split("\t")
    rows = [dict(zip(head, l.split("\t"))) for l in lines[1:]]
    if len(rows) != 1:
        raise RuntimeError("name_search 결과가 1행이 아님: %s%s %d행" % (fh, sh, len(rows)))
    return rows[0]


def sm_name(kor, strokes):
    out = json.loads(run([SM_SURI, "--name", kor, "--strokes", ",".join(map(str, strokes))]))
    s = out["수리사격"]
    keys = [k for k in s if k.startswith(("원격", "형격", "이격", "정격"))]
    return {k[:2]: s[k] for k in keys}, out["종합"]


def suri_section(tsv_dir):
    lines = ["## 수리 대조", "", "### 이름 6건 — 사격과 길흉", ""]
    lines.append("| 이름 | 지정 원획 | korean-naming 표 원획 | 격 | 수 (SM / KN) | saju-myeongri 판정 (등급) | korean-naming 판정 | 일치 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    agree = total = 0
    stroke_mismatch = []
    for kor, hanja, f, s, fh, sh, st in NAMES:
        kn = kn_name(f, s, fh, sh)
        kn_st = (int(kn["A"]), int(kn["B"]), int(kn["C"]))
        if kn_st != st:
            stroke_mismatch.append((kor, hanja, st, kn_st))
        sm, summ = sm_name(kor, st)
        for g, key in (("원격", "원"), ("형격", "형"), ("이격", "이"), ("정격", "정")):
            a = sm[g]
            n_kn = int(kn[key + "_num"])
            g_sm = SM_GRADE[a["길흉"]]
            g_kn = kn[key + "_grade"]
            same = (a["수"] == n_kn) and (g_sm == g_kn)
            total += 1
            agree += same
            lines.append("| %s(%s) | %s | %s | %s | %d / %d | %s (%s) | %s | %s |"
                         % (kor, hanja, "·".join(map(str, st)), "·".join(map(str, kn_st)), g,
                            a["수"], n_kn, g_sm, a["등급"], g_kn, "일치" if same else "불일치"))
    lines.append("")
    lines.append("- 격 단위 일치 %d / %d" % (agree, total))
    if stroke_mismatch:
        for kor, hanja, st, kn_st in stroke_mismatch:
            lines.append("- 원획 불일치: %s(%s) 지정 %s ↔ korean-naming 표 %s"
                         % (kor, hanja, "·".join(map(str, st)), "·".join(map(str, kn_st))))
    else:
        lines.append("- 지정 원획과 korean-naming 원획표(data/inmyeong_hanja.tsv) 값이 6건 모두 같다")
    lines.append("")

    # 1~81 전수
    ns = load_module(SM_SURI, "sm_name_suri")
    kn_mod = load_module(KN_SEARCH, "kn_name_search")
    chk = run([KN_SEARCH, "--check-suri"])
    kn_grade = {}
    for l in chk.splitlines():
        if ":" in l and not l.startswith("sha256"):
            g, nums = l.split(":", 1)
            g = g.split()[0]
            for x in nums.split(","):
                if x.strip():
                    kn_grade[int(x)] = g
    diffs = []
    sm_counts, kn_counts = {}, {}
    for n in range(1, 82):
        r = ns.suri(n)
        g_sm = SM_GRADE[r["길흉"]]
        sm_counts[g_sm] = sm_counts.get(g_sm, 0) + 1
        kn_counts[kn_grade[n]] = kn_counts.get(kn_grade[n], 0) + 1
        if g_sm != kn_grade[n]:
            diffs.append((n, r["격"], r["등급"], kn_grade[n]))
    lines.append("### 1~81 길흉 전수 대조")
    lines.append("")
    lines.append("- saju-myeongri(name_suri.py 내장표): " + " · ".join("%s %d" % (k, sm_counts.get(k, 0)) for k in ("吉", "반길반흉", "凶")))
    lines.append("- korean-naming(suri_table.md, --check-suri): " + " · ".join("%s %d" % (k, kn_counts.get(k, 0)) for k in ("吉", "반길반흉", "凶")))
    lines.append("- 길흉 일치 %d / 81, 불일치 %d" % (81 - len(diffs), len(diffs)))
    lines.append("")
    lines.append("| 수 | saju-myeongri 격명 | saju-myeongri 판정(등급) | korean-naming 판정 |")
    lines.append("|---|---|---|---|")
    for n, name, deung, gk in diffs:
        lines.append("| %d | %s | %s | %s |" % (n, name, deung, gk))
    lines.append("")
    dae = sorted(ns.DAEGIL)
    lines.append("- 참고: saju-myeongri DAEGIL %d수 = %s (korean-naming 표는 大吉 등급 없음)"
                 % (len(dae), ", ".join(map(str, dae))))
    # 격명(참고): korean-naming 격명은 '태초격(太初格)' 형식 → 괄호 앞 한글만 비교
    kn_tab, _, _ = kn_mod.load_suri(kn_mod.DEFAULT_SURI, {})
    name_diff = []
    for n in range(1, 82):
        a = ns.suri(n)["격"]
        b = kn_tab[n]["name"].split("(")[0].strip()
        if a != b:
            name_diff.append("%d %s/%s" % (n, a, b))
    lines.append("- 참고: 격명(한글) 다른 수 %d개 (saju-myeongri/korean-naming): %s"
                 % (len(name_diff), " · ".join(name_diff) if name_diff else "없음"))
    lines.append("")

    # 환원 규칙
    lines.append("### 81 초과 환원")
    lines.append("")
    lines.append("| 입력 수 | saju-myeongri 적용수 | korean-naming 적용수 | saju-myeongri 판정 | korean-naming 판정 |")
    lines.append("|---|---|---|---|---|")
    for n in (81, 82, 83, 85, 90, 161, 162):
        r = ns.suri(n)
        k = kn_mod.reduce81(n)
        lines.append("| %d | %d | %d | %s | %s |" % (n, r["적용수"], k, SM_GRADE[r["길흉"]], kn_grade[k]))
    lines.append("")
    if tsv_dir:
        with open(os.path.join(tsv_dir, "suri_1_81.tsv"), "w", encoding="utf-8") as f:
            f.write("n\tsm_name\tsm_grade\tsm_deung\tkn_grade\n")
            for n in range(1, 82):
                r = ns.suri(n)
                f.write("%d\t%s\t%s\t%s\t%s\n" % (n, r["격"], SM_GRADE[r["길흉"]], r["등급"], kn_grade[n]))
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tsv", default="", help="원자료 TSV 저장 폴더(선택)")
    a = ap.parse_args()
    if a.tsv:
        os.makedirs(a.tsv, exist_ok=True)
    out = ["# 도구 교차 대조 출력", ""]
    out += saju_section(a.tsv)
    out += suri_section(a.tsv)
    print("\n".join(out))


if __name__ == "__main__":
    main()
