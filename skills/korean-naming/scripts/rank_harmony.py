#!/usr/bin/env python3
"""harmony_hanja.py 조합(실제 여아 이름) 가운데 오행 상생 연결 수로 순위를 매긴다.
상생 연결 = 획수오행 2 + 발음오행 운해본 2 + 해례본 2 + 이름 자원오행 1 + 사격 수리오행 흐름 3 (최대 10).
동점이면 일본식 외격 吉 > 자원오행 木 글자 포함 > 세분 등급 합 순. 사용: python3 rank_harmony.py <f.csv·m.csv 폴더>"""
import sys
sys.path.insert(0,'skills/korean-naming/scripts')
import name_search as ns, candidate_screen as cs, harmony_hanja as hh
rows=ns.load_table(ns.DEFAULT_TABLE); suri,_,_=ns.load_suri(ns.DEFAULT_SURI,{}); ctx=ns.Ctx(suri,False)
A=7
stats,_=cs.load_stats(f'{sys.argv[1]}/f.csv,{sys.argv[1]}/m.csv')
pool,combos=hh.build(rows,ctx,A)
KT={**{n:2 for n in [13,16,21,23,31,41]},**{n:1 for n in [1,3,5,6,11,15,18,24,32,35,37,39]}}
def rels(seq): return [ns.relation(seq[i],seq[i+1]) for i in range(len(seq)-1)]
out=[]
for cb,cc,s in combos:
    n=cb['reading']+cc['reading']
    f,m=stats.get(n,(0,0))
    if f+m<20 or f/(f+m)<0.7: continue
    B,C=cb['row']['wonhoek'],cc['row']['wonhoek']
    hk=rels([ns.ohaeng_of(x) for x in (A,B,C)])
    so=rels(cs.sound_seq(n,'project')); sh=rels(cs.sound_seq(n,'haerye'))
    ro=cs.radical_rel(cb['row']['radical_ohaeng'],cc['row']['radical_ohaeng'])
    nums=[s['nums'][k] for k in ('원','형','이','정')]
    sr=rels([ns.ohaeng_of(x) for x in nums])
    gaek=ctx.is_gil(ctx.grade(C+1))
    saeng=hk.count('생')+so.count('생')+sh.count('생')+(1 if ro=={'생'} else 0)+sr.count('생')
    wood='木' in (cb['row']['radical_ohaeng'] or '')+(cc['row']['radical_ohaeng'] or '')
    kt=sum(KT.get(x,0) for x in nums)
    out.append((saeng,gaek,wood,kt,f+m,n,cb['row']['hanja']+cc['row']['hanja'],nums,hk,so,sh,ro,sr,cb['row']['radical_ohaeng'],cc['row']['radical_ohaeng'],f,m,cb['row']['education'],cc['row']['education']))
out.sort(key=lambda x:(-x[0],-x[1],-x[2],-x[3]))
for o in out[:40]: print(o[0],o[1],o[2],o[3],'오'+o[5],o[6],o[7],'획',o[8],'운',o[9],'해',o[10],'자',o[11],o[13],o[14],'수리',o[12],o[15],o[16],o[17],o[18])
