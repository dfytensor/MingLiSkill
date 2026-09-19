# -*- coding: utf-8 -*-
"""
mine555.py — 统计监督学习流水线
训练集: 2010-2018 + 2021-2023 (315题)
留出集: 2024/2025/2026 (120题, 从未参与任何挖掘)
特征: 流年干支 vs 命例四柱的12种机制特征
"""
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

GAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
ZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
ZHI_HIDE = {'子':('癸',), '丑':('己','癸','辛'), '寅':('甲','丙','戊'), '卯':('乙',),
            '辰':('戊','乙','癸'), '巳':('丙','庚','戊'), '午':('丁','己'), '未':('己','丁','乙'),
            '申':('庚','壬','戊'), '酉':('辛',), '戌':('戊','辛','丁'), '亥':('壬','甲')}
SHENGXIAO = {'木':'火','火':'土','土':'金','金':'水','水':'木'}   # 食伤
KEWO = {'木':'土','火':'金','土':'水','金':'木','水':'火'}        # 官杀
WOKE = {'木':'土','火':'金','土':'水','金':'木','水':'火'}        # 财(我克)
SHENGWO = {'木':'水','火':'木','土':'火','金':'土','水':'金'}     # 印
KU = {'木':'未','火':'戌','金':'丑','水':'辰','土':'辰'}
LIUHE = {'子丑','寅亥','卯戌','辰酉','巳申','午未'}
BANHE = {'申子','子辰','寅午','午戌','巳酉','酉丑','亥卯','卯未'}
CHONG = {'子午','丑未','寅申','卯酉','辰戌','巳亥'}

def year_gz(y):
    gz = []
    stems = '甲乙丙丁戊己庚辛壬癸'
    branches = '子丑寅卯辰巳午未申酉戌亥'
    sy = (y - 4) % 10
    bz = (y - 4) % 12
    return stems[sy] + branches[bz]

def shishen(day_gan, other_gan):
    if not day_gan or not other_gan: return None
    dw = GAN_WX[day_gan]; ow = GAN_WX[other_gan]
    if ow == dw: return '比肩' if GAN.index(other_gan) == GAN.index(day_gan) else '劫财'
    if ow == SHENGXIAO[dw]: return '食神' if GAN.index(other_gan) % 2 == GAN.index(day_gan) % 2 else '伤官'
    if ow == WOKE[dw]: return '正财' if GAN.index(other_gan) % 2 != GAN.index(day_gan) % 2 else '偏财'
    if ow == KEWO[dw]: return '正官' if GAN.index(other_gan) % 2 != GAN.index(day_gan) % 2 else '七杀'
    if ow == SHENGWO[dw]: return '正印' if GAN.index(other_gan) % 2 != GAN.index(day_gan) % 2 else '偏印'
    return None

def features(pillars, year):
    """计算流年相对命例的12特征"""
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

master = json.load(open(r'E:\ming_li_skill\MingLiSkill\data_archive\master_raw.json', encoding='utf-8'))
answers = json.load(open(r'E:\ming_li_skill\MingLiSkill\data_archive\asklingxi_answers.json', encoding='utf-8'))['answers']

TRAIN_YEARS = [str(y) for y in list(range(2010, 2019)) + [2021, 2022, 2023]]
HOLD_YEARS = ['2024', '2025', '2026']

rows = []
for y, persons in master.items():
    key = answers.get(y, [])
    qi = 0
    for p in persons:
        if not p['pillars'] or len(p['pillars']) < 4:
            continue
        for q in p['questions']:
            if qi >= len(key): break
            ans = key[qi]
            qtext = q.get('qtext', '')
            # 题干或选项中的年份
            years_in = [int(m) for m in re.findall(r'(19[5-9]\d|20[0-2]\d)', qtext)]
            for L, t in q.get('options', []):
                years_in += [int(m) for m in re.findall(r'(19[5-9]\d|20[0-2]\d)', t)]
            rows.append({
                'year_set': y, 'qnum': q['qnum'], 'ans': ans,
                'pillars': p['pillars'], 'qtext': qtext,
                'years_in': sorted(set(years_in)),
                'options': q.get('options', []),
            })
            qi += 1

print('total rows:', len(rows))
json.dump(rows, open(r'E:\ming_li_skill\MingLiSkill\data_archive\rows555.json', 'w', encoding='utf-8'),
          ensure_ascii=False)

# ===== 统计挖掘: 事件年题(题干含年份, 答案是年份选项) =====
train = [r for r in rows if r['year_set'] in TRAIN_YEARS]
hold = [r for r in rows if r['year_set'] in HOLD_YEARS]
print('train rows: %d, holdout rows: %d' % (len(train), len(hold)))

def is_year_question(r):
    """题干含年份 且 选项以年份开头"""
    if not r['years_in']: return False
    yopts = 0
    for L, t in r['options']:
        if re.match(r'\s*[A-E]?\s*(19|20)\d\d', t): yopts += 1
    return yopts >= max(2, len(r['options']) // 2)

def correct_year(r):
    idx = 'ABCDE'.find(r['ans'])
    if idx < 0 or idx >= len(r['options']): return None
    t = r['options'][idx][1]
    m = re.search(r'(19[5-9]\d|20[0-2]\d)', t)
    return int(m.group(1)) if m else None

train_yq = [r for r in train if is_year_question(r)]
hold_yq = [r for r in hold if is_year_question(r)]
print('train event-year questions: %d, holdout: %d' % (len(train_yq), len(hold_yq)))

# 每个特征在训练集的命中率
FEATS = ['伏吟日柱','伏吟日支','伏吟年柱','冲日支','合日支','食伤透','官杀透','正官透','七杀透',
         '印星透','偏印透','劫财透','财星透','比肩透','配偶星支','食伤支','官杀支']
stats = {}
for feat in FEATS:
    hit = tot = 0
    for r in train_yq:
        cy = correct_year(r)
        if cy is None: continue
        f = features(r['pillars'], cy)
        tot += 1
        if f[feat]: hit += 1
    rate = hit / tot if tot else 0
    stats[feat] = {'hit': hit, 'tot': tot, 'rate': round(rate, 3)}

# 基线: 任一年份随机具有该特征的概率
print('\nFEATURE | hit/tot | rate (train)')
for feat, s in sorted(stats.items(), key=lambda kv: -kv[1]['rate']):
    print('%s: %d/%d = %.1f%%' % (feat, s['hit'], s['tot'], s['rate']*100))

json.dump(stats, open(r'E:\ming_li_skill\MingLiSkill\data_archive\feature_stats.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
