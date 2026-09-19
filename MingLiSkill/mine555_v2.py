# -*- coding: utf-8 -*-
"""mine555_v2.py — 完整统计监督挖掘(自包含)"""
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

GAN = '甲乙丙丁戊己庚辛壬癸'
GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
ZHI_HIDE = {'子':('癸',), '丑':('己','癸','辛'), '寅':('甲','丙','戊'), '卯':('乙',),
            '辰':('戊','乙','癸'), '巳':('丙','庚','戊'), '午':('丁','己'), '未':('己','丁','乙'),
            '申':('庚','壬','戊'), '酉':('辛',), '戌':('戊','辛','丁'), '亥':('壬','甲')}
SHENGXIAO = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
KEWO = {'木':'土','火':'金','土':'水','金':'木','水':'火'}
WOKE = {'木':'土','火':'金','土':'水','金':'木','水':'火'}
SHENGWO = {'木':'水','火':'木','土':'火','金':'土','水':'金'}
LIUHE = {'子丑','寅亥','卯戌','辰酉','巳申','午未'}
BANHE = {'申子','子辰','寅午','午戌','巳酉','酉丑','亥卯','卯未'}
CHONG = {'子午','丑未','寅申','卯酉','辰戌','巳亥'}

def year_gz(y):
    return GAN[(y - 4) % 10] + '子丑寅卯辰巳午未申酉戌亥'[(y - 4) % 12]

def shishen(day_gan, other_gan):
    if not day_gan or not other_gan: return None
    dw = GAN_WX[day_gan]; ow = GAN_WX[other_gan]
    same_parity = GAN.index(other_gan) % 2 == GAN.index(day_gan) % 2
    if ow == dw: return '比肩' if same_parity else '劫财'
    if ow == SHENGXIAO[dw]: return '食神' if same_parity else '伤官'
    if ow == WOKE[dw]: return '正财' if not same_parity else '偏财'
    if ow == KEWO[dw]: return '正官' if not same_parity else '七杀'
    if ow == SHENGWO[dw]: return '正印' if not same_parity else '偏印'
    return None

def features(pillars, year):
    gz = year_gz(year)
    ygan, yzhi = gz[0], gz[1]
    day_p = pillars[2] if len(pillars) >= 4 else ''
    year_p = pillars[0] if pillars else ''
    day_gan = day_p[0] if day_p else ''
    day_zhi = day_p[1:] if len(day_p) > 1 else ''
    f = {}
    f['伏吟日柱'] = (gz == day_p)
    f['伏吟日支'] = (yzhi == day_zhi)
    f['伏吟年柱'] = (gz == year_p)
    f['冲日支'] = ((yzhi + day_zhi) in CHONG)
    f['合日支'] = ((yzhi + day_zhi) in LIUHE or (yzhi + day_zhi) in BANHE)
    ss_g = shishen(day_gan, ygan)
    f['食伤透'] = ss_g in ('食神','伤官')
    f['官杀透'] = ss_g in ('正官','七杀')
    f['正官透'] = ss_g == '正官'
    f['七杀透'] = ss_g == '七杀'
    f['印星透'] = ss_g in ('正印','偏印')
    f['偏印透'] = ss_g == '偏印'
    f['劫财透'] = ss_g == '劫财'
    f['财星透'] = ss_g in ('正财','偏财')
    f['比肩透'] = ss_g == '比肩'
    hid = ZHI_HIDE.get(yzhi, ())
    ss_z = shishen(day_gan, hid[0]) if hid else None
    f['配偶星支'] = (ss_z in ('正官','七杀','正财','偏财'))
    f['食伤支'] = ss_z in ('食神','伤官')
    f['官杀支'] = ss_z in ('正官','七杀')
    return f

master = json.load(open(r'E:\ming_li_skill\MingLiSkill\data_archive\master2.json', encoding='utf-8'))

def strip_tags(h):
    return re.sub(r'<[^>]+>', '', h)

def get_questions(y):
    h = open(r'E:\ming_li_skill\MingLiSkill\data_archive\asklingxi_html\%d.html' % y, encoding='utf-8').read()
    text = re.sub(r'\s+', '', strip_tags(h))
    parts = re.split(r'Q(\d+)', text)
    qs = {}
    for i in range(1, len(parts) - 1, 2):
        qnum = int(parts[i])
        seg = parts[i + 1][:400]
        seg = seg.replace('查看排盘', '').replace('创建命盘档案', '')
        qs[qnum] = seg
    hits = re.findall(r'rounded-full [^"]*?bg-primary text-white[^"]*?">(?:<!-- -->)?([A-E])', h)
    return qs, hits

def pillars_for_q(y, qnum):
    persons = master[str(y)]['persons']
    with_p = [p for p in persons if p['pillars']]
    if not with_p: return None
    idx = (qnum - 1) // 5
    if idx >= len(with_p): idx = len(with_p) - 1
    return with_p[idx]['pillars']

TRAIN = [str(y) for y in list(range(2010, 2019)) + [2021, 2022, 2023]]
HOLD = ['2024', '2025', '2026']
FEATS = ['伏吟日柱','伏吟日支','伏吟年柱','冲日支','合日支','食伤透','官杀透','正官透','七杀透',
         '印星透','偏印透','劫财透','财星透','比肩透','配偶星支','食伤支','官杀支']

dataset = []
for y in range(2010, 2027):
    ys = str(y)
    qs, hits = get_questions(y)
    for qnum_str, seg in qs.items():
        qnum = int(qnum_str)
        if qnum > len(hits): continue
        ans = hits[qnum - 1]
        pillars = pillars_for_q(y, qnum)
        if not pillars or len(pillars) < 4: continue
        years_in = [int(m) for m in re.findall(r'(19[5-9]\d|20[0-2]\d)', seg)]
        opt_years = re.findall(r'([A-E])[^A-E]{0,150}?((?:19|20)\d\d)', seg)
        ans_year_map = {L: int(y2) for L, y2 in opt_years}
        ans_year = ans_year_map.get(ans)
        dataset.append({'y': ys, 'qnum': qnum, 'ans': ans, 'pillars': pillars,
                        'years_in': sorted(set(years_in)), 'ans_year': ans_year})

json.dump(dataset, open(r'E:\ming_li_skill\MingLiSkill\data_archive\dataset555.json', 'w', encoding='utf-8'),
          ensure_ascii=False)
ay = [d for d in dataset if d['ans_year']]
print('total parsed: %d, event-year-with-answer-year: %d' % (len(dataset), len(ay)))

train = [d for d in dataset if d['y'] in TRAIN and d['ans_year']]
hold = [d for d in dataset if d['y'] in HOLD and d['ans_year']]
print('train event-year: %d, holdout: %d' % (len(train), len(hold)))

print('\n== TRAIN: P(feature | 正确答案年) vs base ==')
sig_feats = {}
for feat in FEATS:
    hit = sum(1 for d in train if features(d['pillars'], d['ans_year'])[feat])
    tot = len(train)
    rate = hit / tot if tot else 0
    base_hit = base_tot = 0
    for d in train:
        for yy in d['years_in']:
            base_tot += 1
            if features(d['pillars'], yy)[feat]: base_hit += 1
    base = base_hit / base_tot if base_tot else 0
    lift = rate / base if base else 0
    star = ''
    if tot >= 30 and lift >= 1.4 and rate >= 0.15:
        star = ' <<< SIGNAL'
        sig_feats[feat] = {'rate': round(rate,3), 'base': round(base,3), 'lift': round(lift,2)}
    print('%s: %d/%d=%.1f%% (base %.1f%%, lift %.2f)%s' % (feat, hit, tot, rate*100, base*100, lift, star))

json.dump(sig_feats, open(r'E:\ming_li_skill\MingLiSkill\data_archive\sig_feats.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('\nsignificant:', list(sig_feats) if sig_feats else 'NONE')
