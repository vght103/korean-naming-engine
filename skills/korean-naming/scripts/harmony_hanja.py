#!/usr/bin/env python3
"""오(吳)씨와 어울리는 이름 한자표 생성기 (harmony_hanja.py)

뜻이 이름에 무난한 한자(사람이 고른 화이트리스트)를 모아, 성 吳(원획 7) 뒤
둘째 자리(B)·셋째 자리(C)에 놓았을 때 candidate_screen.py 의 6개 조건을
모두 통과하는 조합만 남긴다. 그 결과로
  1) 통과하는 획수 짝, 2) 둘째 자리 한자, 3) 셋째 자리 한자,
  4) 그 한자들로 만들 수 있는 실제 여아 이름(출생신고 2008–2019)
을 Markdown 으로 출력한다. 같은 입력이면 같은 출력을 낸다.

사용 예 (저장소 루트에서; 통계 CSV 는 docs/새후보 재현 명령의 curl 로 받는다)
    python3 skills/korean-naming/scripts/harmony_hanja.py --stats f.csv,m.csv \\
        --out docs/새후보/오씨_어울림한자.md
"""
import argparse
import os
import shlex
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import name_search as ns  # noqa: E402
import candidate_screen as cs  # noqa: E402

# 뜻이 이름에 무난한 글자 (교육용 기초한자 + 인명에 흔한 글자, 사람이 고름)
WHITELIST = (
    "安宇守如好西有伊圭朱"
    "始承尙宙周宜定和松靑雨枝知亞享沇沅姃采林佳京奈"
    "宣姿柔河泉泳貞香相秋信俊厚姸姝沼泫玟垠美"
    "修夏容庭書洪洲珍眞素笑花芽原哲效娟娥玹洙玲珊純秦"
    "樹潤靜運儒叡澐璇蓉穎霖錫"
    "優聰聲遙陽鮮禧霞蓮璟嬪謠"
    "環濟瀅"
)
# libhangul 훈이 어색하거나 비어 있는 글자의 대표 훈
HUN_FIX = {"潤": "윤택할 윤", "姃": "단정할 정", "玹": "옥빛 현", "采": "캘·풍채 채", "姸": "고울 연"}
BAN_SYLLABLES = "음흔언"   # 사용자가 뺀 음절
MIN_TOTAL, MIN_FEMALE = 20, 0.7


def build(rows, ctx, a):
    pool = []
    for h in dict.fromkeys(WHITELIST):
        r = next((x for x in rows if x["hanja"] == h), None)
        if not r:
            continue
        for rd in r["inmyeong_readings"].split():
            rd = rd.split(":")[0]
            if len(rd) != 1 or rd in BAN_SYLLABLES:
                continue
            cd = [c for c in ns.candidates(rows, rd) if c["row"]["hanja"] == h]
            if cd and cs.char_ok(cd[0]):
                pool.append(cd[0])
    combos = []
    for cb in pool:
        for cc in pool:
            if cb is cc:
                continue
            s, ck = cs.checks(ctx, a, cb, cc)
            if all(ck.values()):
                combos.append((cb, cc, s))
    return pool, combos


def label(cd):
    r = cd["row"]
    return "%s %s" % (r["hanja"], cd["reading"])


def char_table(combos, idx):
    by = defaultdict(lambda: [None, set()])
    for c in combos:
        cd, other = c[idx], c[1 - idx]
        key = (cd["row"]["hanja"], cd["reading"])
        by[key][0] = cd
        by[key][1].add(other["row"]["wonhoek"])
    groups = defaultdict(list)
    for (h, rd), (cd, partners) in by.items():
        groups[cd["row"]["wonhoek"]].append((rd, h, cd, sorted(partners)))
    out = []
    for w in sorted(groups):
        out.append("| **%d획** | %s |" % (w, " · ".join(
            "%s(%s) %s%s" % (rd, h, HUN_FIX.get(h, ns.short_hun(cd["row"])),
                             "" if not cd["row"]["radical_ohaeng"] else ", " + cd["row"]["radical_ohaeng"])
            for rd, h, cd, _ in sorted(groups[w]))))
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(description="오씨와 어울리는 이름 한자표")
    ap.add_argument("--stats", required=True, help="여아csv,남아csv")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)
    rows = ns.load_table(ns.DEFAULT_TABLE)
    suri, _, _ = ns.load_suri(ns.DEFAULT_SURI, {})
    ctx = ns.Ctx(suri, False)
    a = next(r["wonhoek"] for r in rows if r["hanja"] == "吳")
    stats, _ = cs.load_stats(args.stats)
    pool, combos = build(rows, ctx, a)

    L = ["# 오(吳)씨와 어울리는 이름 한자표", "",
         "<!-- harmony_hanja.py 생성물. 직접 고치지 말고 다시 실행할 것. -->", "",
         "재현: `python3 skills/korean-naming/scripts/harmony_hanja.py " +
         " ".join(shlex.quote(t) for t in argv) + "` (통계 CSV는 `docs/새후보/후보10_비교표.md`의 curl 명령으로 받는다)", "",
         "## 1. 어떻게 골랐나", "",
         "- 이름에 쓰기 무난한 뜻의 한자 %d자(교육용 기초한자 + 이름에 흔한 글자)를 먼저 모았습니다. "
         "日·火 부수 글자, 컴퓨터 입력이 어려운 글자, 사용자가 뺀 음절(%s)은 제외했습니다." % (
             len({c["row"]["hanja"] for c in pool}), "·".join(BAN_SYLLABLES)),
         "- 그 한자들을 성 오(吳, 7획) 뒤 둘째·셋째 자리에 하나씩 놓아 보고, 아래 조건을 **모두** 통과하는 조합만 남겼습니다.",
         "  1. 숫자 4개(원격·형격·이격·정격)가 모두 좋은 수(吉)",
         "  2. 획수의 홀짝이 한쪽으로 몰리지 않음",
         "  3. 획수 오행(성→둘째→셋째)끼리 부딪힘 없음",
         "  4. 발음 오행이 두 학파(운해본·해례본) 모두에서 부딪힘 없음",
         "  5. 이름 두 글자의 부수 오행끼리 부딪힘 없음",
         "  6. 컴퓨터로 입력되는 글자(KS X 1001)",
         "- 그래서 **아래 두 표에서 아무 글자나 고르면 되는 것은 아닙니다.** 둘째 자리 글자와 셋째 자리 글자의 **획수 짝**이 2절 표에 있어야 하고, 발음도 맞아야 합니다. 실제로 맞는 조합은 5절 이름 목록에 모두 들어 있습니다.",
         "- 통과 조합: %d개" % len(combos), ""]

    pairs = defaultdict(list)
    for cb, cc, s in combos:
        pairs[(cb["row"]["wonhoek"], cc["row"]["wonhoek"])] = s
    L += ["## 2. 오(吳)와 맞는 획수 짝", "",
          "| 둘째 획수 | 셋째 획수 | 원격 | 형격 | 이격 | 정격 |", "|---|---|---|---|---|---|"]
    for (b, c), s in sorted(pairs.items()):
        n = s["nums"]
        L.append("| %d | %d | %s | %s | %s | %s |" % (b, c, *(
            "%d %s" % (n[k], ctx.suri[ns.reduce81(n[k])]["name"].split("(")[0]) for k in ("원", "형", "이", "정"))))
    L += ["", "※ 형격(성 7 + 둘째 획수)이 둘째 자리 획수만으로 정해지므로, 둘째 자리 8획 글자들은 형격이 모두 15(통솔격)입니다.", ""]

    L += ["## 3. 둘째 자리(이름 첫 글자)에 좋은 한자", "",
          "발음 첫소리가 **ㅇ·ㅎ·ㅅ·ㅈ·ㅊ** 인 글자만 남습니다. 성 '오'(ㅇ)와 발음 오행이 두 학파 모두에서 맞는 첫소리가 이것뿐이기 때문입니다. "
          "괄호 뒤는 뜻과 부수 오행입니다.", "", "| 획수 | 글자 (발음(한자) 뜻) |", "|---|---|"]
    L += char_table(combos, 0)
    L += ["", "## 4. 셋째 자리(이름 끝 글자)에 좋은 한자", "",
          "셋째 자리는 둘째 글자에 따라 맞는 발음이 달라집니다. 아래는 둘째 자리 글자 가운데 하나 이상과 조건을 모두 통과하는 글자입니다.", "",
          "| 획수 | 글자 (발음(한자) 뜻) |", "|---|---|"]
    L += char_table(combos, 1)

    names = defaultdict(list)
    for cb, cc, s in combos:
        names[cb["reading"] + cc["reading"]].append((cb, cc, s))
    real = []
    for n, v in names.items():
        f, m = stats.get(n, (0, 0))
        if f + m >= MIN_TOTAL and f / (f + m) >= MIN_FEMALE:
            real.append((n, f, m, v))
    real.sort(key=lambda x: (-(x[1] + x[2]), x[0]))
    trend = set(cs.DEFAULT_EXCLUDE)

    def block(title, lo, hi):
        rows_ = [x for x in real if lo <= x[1] + x[2] < hi]
        out = ["### %s (%d개)" % (title, len(rows_)), "",
               "| 이름 | 한자 조합 (숫자 4개 원·형·이·정) | 출생신고 2008–19 여/남 |", "|---|---|---|"]
        for n, f, m, v in rows_:
            mark = " ⓣ" if set(n) & trend else ""
            opts = " · ".join("%s(吳%s%s) %s" % ("오" + n, cb["row"]["hanja"], cc["row"]["hanja"],
                                                 "·".join(str(s["nums"][k]) for k in ("원", "형", "이", "정")))
                              for cb, cc, s in v[:6])
            more = " 외 %d" % (len(v) - 6) if len(v) > 6 else ""
            out.append("| **오%s**%s | %s%s | %s / %s |" % (n, mark, opts, more, format(f, ","), format(m, ",")))
        return out + [""]

    L += ["", "## 5. 이 한자들로 만들 수 있는 실제 여자아이 이름", "",
          "2·3절 한자로 조건을 모두 통과하면서, 2008–2019년 출생신고에 실제로 있는 이름(누적 %d명 이상, 여아 %d%% 이상)입니다. "
          "ⓣ는 요즘 유행 음절(%s)이 들어간 이름입니다." % (MIN_TOTAL, int(MIN_FEMALE * 100), "·".join(cs.DEFAULT_EXCLUDE)), ""]
    L += block("흔한 이름 — 3,000명 이상", 3000, 10 ** 9)
    L += block("보통 — 300~2,999명", 300, 3000)
    L += block("드문 이름 — 300명 미만", 0, 300)
    L += ["## 6. 한계", "",
          "- 한자 후보는 사람이 고른 화이트리스트라 빠진 좋은 글자가 있을 수 있습니다. 넣고 싶은 글자가 있으면 스크립트의 `WHITELIST`에 더하고 다시 실행합니다.",
          "- 한자 데이터는 대법원 인명용 2018 목록까지입니다. 출생신고 직전 대법원 조회로 자형과 발음을 다시 확인합니다.",
          "- 숫자 풀이는 전통 해석이며, 사주와의 맞춤은 아기가 태어난 뒤 다시 봅니다.", ""]
    text = "\n".join(L) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
