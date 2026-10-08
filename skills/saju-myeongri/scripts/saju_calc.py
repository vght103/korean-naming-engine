#!/usr/bin/env python3
"""사주팔자 결정론적 계산기 (sxtwl 기반).

고정 기준 (references/standards.md 참조):
- 년주: 입춘 절입 기준 / 월주: 12절(節) 기준 — sxtwl 천문력 사용
- 일주: 23:00(보정 후) 이후 출생은 다음날 일주 적용 (정자시법)
- 시주: 오서둔(五鼠遁) 공식, 2시간 단위 12지지
- 서머타임: 한국 DST 기간 자동 -1시간 보정
- 진태양시: 기본 -30분 보정 (동경 135도 표준시 vs 한반도 중앙 경도)
- 대운: 양남음녀 순행, 음남양녀 역행. 대운수 = 절입까지 일수/3 반올림(최소 1)

사용법:
  python3 saju_calc.py --date 1985-03-20 --time 08:15 --gender M
  python3 saju_calc.py --date 1988-08-15 --lunar --time 22:00 --gender F
  옵션: --leap(윤달), --no-solar-correction(진태양시 보정 끔), --no-dst(서머타임 보정 끔)
"""
import argparse, json, sys
from datetime import datetime, timedelta

try:
    import sxtwl
except ImportError:
    sys.exit("sxtwl 미설치: pip install sxtwl --break-system-packages")

GAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
ZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
GAN_KO = ['갑','을','병','정','무','기','경','신','임','계']
ZHI_KO = ['자','축','인','묘','진','사','오','미','신','유','술','해']
GAN_OH = ['목','목','화','화','토','토','금','금','수','수']  # 천간 오행
ZHI_OH = ['수','토','목','목','토','화','화','토','금','금','토','수']  # 지지 오행
GAN_YY = ['양','음','양','음','양','음','양','음','양','음']
ZHI_YY = ['양','음','양','음','양','음','양','음','양','음','양','음']  # 12개(자~해). 구버전은 10개 버그
ZHI_ANIMAL = ['쥐','소','호랑이','토끼','용','뱀','말','양','원숭이','닭','개','돼지']

# 지장간 (여기/중기/정기 — 통용 기준)
JIJANGGAN = {
    '子':['壬','癸'], '丑':['癸','辛','己'], '寅':['戊','丙','甲'], '卯':['甲','乙'],
    '辰':['乙','癸','戊'], '巳':['戊','庚','丙'], '午':['丙','己','丁'], '未':['丁','乙','己'],
    '申':['戊','壬','庚'], '酉':['庚','辛'], '戌':['辛','丁','戊'], '亥':['戊','甲','壬'],
}

# 한국 서머타임 기간 (KST 기준, 시작일~종료일 포함)
DST_PERIODS = [
    ('1948-06-01','1948-09-12'), ('1949-04-03','1949-09-10'),
    ('1950-04-01','1950-09-09'), ('1951-05-06','1951-09-08'),
    ('1955-05-05','1955-09-08'), ('1956-05-20','1956-09-29'),
    ('1957-05-05','1957-09-21'), ('1958-05-04','1958-09-20'),
    ('1959-05-03','1959-09-19'), ('1960-05-01','1960-09-17'),
    ('1987-05-10','1987-10-10'), ('1988-05-08','1988-10-08'),
]

OHENG_REL = {  # (일간오행, 대상오행) -> 십신 그룹
    ('목','목'):'비겁',('목','화'):'식상',('목','토'):'재성',('목','금'):'관성',('목','수'):'인성',
    ('화','화'):'비겁',('화','토'):'식상',('화','금'):'재성',('화','수'):'관성',('화','목'):'인성',
    ('토','토'):'비겁',('토','금'):'식상',('토','수'):'재성',('토','목'):'관성',('토','화'):'인성',
    ('금','금'):'비겁',('금','수'):'식상',('금','목'):'재성',('금','화'):'관성',('금','토'):'인성',
    ('수','수'):'비겁',('수','목'):'식상',('수','화'):'재성',('수','토'):'관성',('수','금'):'인성',
}
SIBSIN_NAME = {  # (그룹, 음양 같음?) -> 십신
    ('비겁',True):'비견',('비겁',False):'겁재',
    ('식상',True):'식신',('식상',False):'상관',
    ('재성',True):'편재',('재성',False):'정재',
    ('관성',True):'편관',('관성',False):'정관',
    ('인성',True):'편인',('인성',False):'정인',
}

def sibsin(day_gan_idx, target_gan_idx):
    if day_gan_idx == target_gan_idx:
        return '비견'
    g = OHENG_REL[(GAN_OH[day_gan_idx], GAN_OH[target_gan_idx])]
    same = GAN_YY[day_gan_idx] == GAN_YY[target_gan_idx]
    return SIBSIN_NAME[(g, same)]

def in_dst(d):
    s = d.strftime('%Y-%m-%d')
    return any(a <= s <= b for a, b in DST_PERIODS)

def pillar(tg, dz):
    return {'한자': GAN[tg]+ZHI[dz], '한글': GAN_KO[tg]+ZHI_KO[dz],
            '천간': {'자':GAN[tg], '오행':GAN_OH[tg], '음양':GAN_YY[tg]},
            '지지': {'자':ZHI[dz], '오행':ZHI_OH[dz], '음양':ZHI_YY[dz],
                     '지장간':JIJANGGAN[ZHI[dz]]}}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--date', required=True, help='YYYY-MM-DD')
    p.add_argument('--time', default=None, help='HH:MM (모르면 생략)')
    p.add_argument('--gender', required=True, choices=['M','F'])
    p.add_argument('--lunar', action='store_true')
    p.add_argument('--leap', action='store_true', help='음력 윤달')
    p.add_argument('--no-solar-correction', action='store_true')
    p.add_argument('--no-dst', action='store_true')
    a = p.parse_args()

    y, m, d = map(int, a.date.split('-'))
    if a.lunar:
        day0 = sxtwl.fromLunar(y, m, d, a.leap)
        y, m, d = day0.getSolarYear(), day0.getSolarMonth(), day0.getSolarDay()

    corrections = []
    if a.time:
        hh, mm = map(int, a.time.split(':'))
        dt = datetime(y, m, d, hh, mm)
        if not a.no_dst and in_dst(dt):
            dt -= timedelta(hours=1); corrections.append('서머타임 -1시간')
        if not a.no_solar_correction:
            dt -= timedelta(minutes=30); corrections.append('진태양시 -30분')
        # 일주 기준일: 보정 후 23시 이후면 다음날
        pd = dt + timedelta(hours=1)  # 23:00 -> 다음날 00:00 로 밀기
        pillar_date = pd.date() if dt.hour >= 23 else dt.date()
        hour_zhi = ((dt.hour * 60 + dt.minute + 60) // 120) % 12
    else:
        dt = None
        pillar_date = datetime(y, m, d).date()
        hour_zhi = None

    day = sxtwl.fromSolar(pillar_date.year, pillar_date.month, pillar_date.day)
    yGZ, mGZ, dGZ = day.getYearGZ(), day.getMonthGZ(), day.getDayGZ()

    result = {
        '입력': {'양력': f'{y:04d}-{m:02d}-{d:02d}', '시각': a.time or '미상',
                 '성별': '남' if a.gender == 'M' else '여',
                 '보정': corrections or ['없음'],
                 '보정후시각': dt.strftime('%H:%M') if dt else None},
        '음력': f'{day.getLunarYear()}-{day.getLunarMonth():02d}-{day.getLunarDay():02d}'
                + (' (윤달)' if day.isLunarLeap() else ''),
        '띠': ZHI_ANIMAL[yGZ.dz],
        '사주': {'년주': pillar(yGZ.tg, yGZ.dz), '월주': pillar(mGZ.tg, mGZ.dz),
                 '일주': pillar(dGZ.tg, dGZ.dz)},
    }

    if hour_zhi is not None:
        # 오서둔: 시간 천간 = (일간*2 + 시지) % 10
        h_tg = (dGZ.tg * 2 + hour_zhi) % 10
        result['사주']['시주'] = pillar(h_tg, hour_zhi)

    # 십신 (일간 기준)
    dg = dGZ.tg
    ss = {'년간': sibsin(dg, yGZ.tg), '월간': sibsin(dg, mGZ.tg), '일간': '일원(본인)'}
    if hour_zhi is not None:
        ss['시간'] = sibsin(dg, h_tg)
    # 지지 정기(본기) 십신
    for nm, gz_dz in [('년지', yGZ.dz), ('월지', mGZ.dz), ('일지', dGZ.dz)] + \
                     ([('시지', hour_zhi)] if hour_zhi is not None else []):
        main_gan = JIJANGGAN[ZHI[gz_dz]][-1]
        ss[nm] = sibsin(dg, GAN.index(main_gan))
    result['십신'] = ss

    # 오행 분포 (천간 + 지지, 8자)
    cnt = {'목':0,'화':0,'토':0,'금':0,'수':0}
    for tg2, dz2 in [(yGZ.tg,yGZ.dz),(mGZ.tg,mGZ.dz),(dGZ.tg,dGZ.dz)] + \
                    ([(h_tg,hour_zhi)] if hour_zhi is not None else []):
        cnt[GAN_OH[tg2]] += 1; cnt[ZHI_OH[dz2]] += 1
    result['오행분포'] = cnt
    result['일간'] = {'자': GAN[dg], '한글': GAN_KO[dg], '오행': GAN_OH[dg], '음양': GAN_YY[dg]}

    # 대운: 양남음녀 순행 / 음남양녀 역행
    yang_year = GAN_YY[yGZ.tg] == '양'
    forward = (yang_year and a.gender == 'M') or (not yang_year and a.gender == 'F')
    # 절입(월주 변경일)까지 일수 탐색
    base = datetime(pillar_date.year, pillar_date.month, pillar_date.day)
    cur_m = (mGZ.tg, mGZ.dz)
    days_to = None
    for i in range(1, 40):
        step = i if forward else -i
        nd = base + timedelta(days=step)
        nday = sxtwl.fromSolar(nd.year, nd.month, nd.day)
        ngz = nday.getMonthGZ()
        if (ngz.tg, ngz.dz) != cur_m:
            days_to = i
            break
    daeun_num = max(1, round((days_to or 3) / 3))
    daeun = []
    mtg, mdz = mGZ.tg, mGZ.dz
    for k in range(1, 9):
        if forward:
            t2, z2 = (mtg + k) % 10, (mdz + k) % 12
        else:
            t2, z2 = (mtg - k) % 10, (mdz - k) % 12
        daeun.append({'나이': daeun_num + (k - 1) * 10, '간지': GAN[t2]+ZHI[z2],
                      '한글': GAN_KO[t2]+ZHI_KO[z2]})
    result['대운'] = {'방향': '순행' if forward else '역행', '대운수': daeun_num, '흐름': daeun}

    # 시간 경계 경고 (보정 후 시각이 홀수시 ±10분 이내)
    if dt is not None:
        mins = dt.hour * 60 + dt.minute
        boundary = ((mins + 60) % 120)
        if boundary <= 10 or boundary >= 110:
            result['경고'] = '보정 후 시각이 시주 경계 ±10분 이내입니다. 인접 시주도 함께 검토하세요.'

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
