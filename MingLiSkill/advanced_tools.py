# -*- coding: utf-8 -*-
"""
advanced_tools.py — 高级确定性工具
1. 干支关系全查（五合/六合/三合/半合/六冲/三刑/六害/破）
2. 十神生克链（力量传导计算）
3. 飞宫四化（每宫天干起四化飞入他宫）
4. 原局冲合刑全查
"""
from collections import defaultdict

# ============ 干支关系表 ============
WU_HE_GAN = [('甲','己'), ('乙','庚'), ('丙','辛'), ('丁','壬'), ('戊','癸')]  # 五合
LIU_HE_ZHI = [('子','丑'), ('寅','亥'), ('卯','戌'), ('辰','酉'), ('巳','申'), ('午','未')]  # 六合
SAN_HE = [('申','子','辰'), ('亥','卯','未'), ('寅','午','戌'), ('巳','酉','丑')]  # 三合
SAN_XING = [('寅','巳','申'), ('丑','戌','未'), ('子','卯')]  # 三刑
ZI_XING = ['辰','午','酉','亥']  # 自刑
LIU_CHONG = [('子','午'), ('丑','未'), ('寅','申'), ('卯','酉'), ('辰','戌'), ('巳','亥')]  # 六冲
LIU_HAI = [('子','未'), ('丑','午'), ('寅','巳'), ('卯','辰'), ('申','亥'), ('酉','戌')]  # 六害
PO = [('子','酉'), ('丑','辰'), ('寅','亥'), ('卯','午'), ('巳','申'), ('未','戌'), ('申','巳'), ('酉','子'), ('戌','未'), ('亥','寅')]  # 破

def _pair_in(a, b, pairs):
    return (a, b) in pairs or (b, a) in pairs

def gan_relations(g1, g2):
    """天干关系"""
    rels = []
    if _pair_in(g1, g2, WU_HE_GAN):
        rels.append('五合')
    from tools.calendar_engine import WUXING_KE, WUXING_SHENG
    wx1, wx2 = None, None
    from tools.calendar_engine import WUXING_GAN
    wx1 = WUXING_GAN.get(g1, '')
    wx2 = WUXING_GAN.get(g2, '')
    if wx1 and wx2:
        if wx1 == wx2:
            rels.append('比和')
        if WUXING_SHENG.get(wx1) == wx2:
            rels.append('%s生%s' % (g1, g2))
        if WUXING_KE.get(wx1) == wx2:
            rels.append('%s克%s' % (g1, g2))
    return rels

def zhi_relations(z1, z2):
    """地支关系"""
    rels = []
    if _pair_in(z1, z2, LIU_HE_ZHI):
        rels.append('六合')
    if _pair_in(z1, z2, LIU_CHONG):
        rels.append('六冲')
    if _pair_in(z1, z2, LIU_HAI):
        rels.append('六害')
    for trio in SAN_HE:
        if z1 in trio and z2 in trio:
            rels.append('半合')
    for trio in SAN_XING:
        if z1 in trio and z2 in trio:
            rels.append('相刑')
    if z1 in ZI_XING and z1 == z2:
        rels.append('自刑')
    for p in PO:
        if _pair_in(z1, z2, [p]):
            rels.append('破')
    return rels


def all_pillar_relations(pillars):
    """四柱全部干支关系查。
    pillars: {'年柱': '辛丑', '月柱': '庚子', ...}
    返回: [(位置A, 位置B, 关系描述)]"""
    results = []
    positions = ['年柱', '月柱', '日柱', '时柱']
    valid = [p for p in positions if pillars.get(p)]

    # 天干对天干
    for i in range(len(valid)):
        for j in range(i+1, len(valid)):
            g1 = pillars[valid[i]][0]
            g2 = pillars[valid[j]][0]
            rels = gan_relations(g1, g2)
            for r in rels:
                if '合' in r or '比' in r:
                    results.append((valid[i]+'干', valid[j]+'干', '%s%s%s' % (g1, r, g2)))

    # 地支对地支
    for i in range(len(valid)):
        for j in range(i+1, len(valid)):
            z1 = pillars[valid[i]][1]
            z2 = pillars[valid[j]][1]
            rels = zhi_relations(z1, z2)
            for r in rels:
                results.append((valid[i]+'支', valid[j]+'支', '%s%s%s[%s]' % (z1, r, z2, r)))

    # 三合局检查（需三支全）
    zhis = [pillars[p][1] for p in valid]
    for trio in SAN_HE:
        if all(z in zhis for z in trio):
            results.append(('全局', '', '三合局：%s' % ''.join(trio)))
    for trio in SAN_XING:
        if all(z in zhis for z in trio) and len(trio) == 3:
            results.append(('全局', '', '三刑全：%s' % ''.join(trio)))

    return results


# ============ 飞宫四化 ============
SIHUA_TABLE = {
    '甲': {'廉贞': '禄', '破军': '权', '武曲': '科', '太阳': '忌'},
    '乙': {'天机': '禄', '天梁': '权', '紫微': '科', '太阴': '忌'},
    '丙': {'天同': '禄', '天机': '权', '文昌': '科', '廉贞': '忌'},
    '丁': {'太阴': '禄', '天同': '权', '天机': '科', '巨门': '忌'},
    '戊': {'贪狼': '禄', '太阴': '权', '右弼': '科', '天机': '忌'},
    '己': {'武曲': '禄', '贪狼': '权', '天梁': '科', '文曲': '忌'},
    '庚': {'太阳': '禄', '武曲': '权', '太阴': '科', '天同': '忌'},
    '辛': {'巨门': '禄', '太阳': '权', '文曲': '科', '文昌': '忌'},
    '壬': {'天梁': '禄', '紫微': '权', '左辅': '科', '武曲': '忌'},
    '癸': {'破军': '禄', '巨门': '权', '太阴': '科', '贪狼': '忌'},
}

# 宫位天干（简化版：按五虎遁从年干推）
def get_palace_stems(year_gan, yin_yang_forward):
    """简化：返回12宫天干序列"""
    # 五虎遁：甲己年丙寅首, 乙庚年戊寅首, 丙辛年庚寅首, 丁壬年壬寅首, 戊癸年甲寅首
    first_gan = {'甲': '丙', '己': '丙', '乙': '戊', '庚': '戊',
                 '丙': '庚', '辛': '庚', '丁': '壬', '壬': '壬',
                 '戊': '甲', '癸': '甲'}
    start = TIANGAN_IDX.get(first_gan.get(year_gan, '丙'), 2)
    from tools.calendar_engine import DIZHI
    zhi_start = TIANGAN_IDX.get('寅', 2)  # 寅
    stems = []
    for i in range(12):
        g = TIANGAN[(start + i) % 10]
        z = DIZHI[(zhi_start + i) % 12]
        stems.append((g, z))
    return stems


def feigong_sihua(natal_year_gan, ziwei_palace_stars, palace_order):
    """飞宫四化：生年四化 + 每宫天干四化飞入他宫。
    ziwei_palace_stars: {宫名: [星名列表]}
    palace_order: [宫名有序列表]（12宫顺序）
    返回: [(来源宫, 化型, 目标星, 目标宫)]"""
    results = []

    # 生年四化
    natal_sihua = SIHUA_TABLE.get(natal_year_gan, {})
    for star, hua in natal_sihua.items():
        for palace, stars in ziwei_palace_stars.items():
            if star in stars:
                results.append(('生年', hua, star, palace))
                break

    # 各宫干四化（飞宫）
    palace_stems = get_palace_stems(natal_year_gan, True)
    for i, palace in enumerate(palace_order[:12]):
        if i >= len(palace_stems):
            break
        pg = palace_stems[i][0]
        pg_sihua = SIHUA_TABLE.get(pg, {})
        for star, hua in pg_sihua.items():
            for tp, stars in ziwei_palace_stars.items():
                if star in stars:
                    results.append((palace, hua, star, tp))
                    break

    return results


# ============ 十神生克链 ============
SHISHEN_CHAIN = {
    # 十神 → 克制的十神
    '七杀': ['比肩', '劫财'],  # 杀克比劫
    '正官': ['劫财'],           # 官克劫
    '正印': ['伤官'],           # 印克伤
    '偏印': ['食神'],           # 枭夺食
    '正财': ['偏印'],           # 财克印
    '偏财': ['正印'],           # 财克印
    '食神': ['七杀'],           # 食制杀
    '伤官': ['正官'],           # 伤见官
    '比肩': ['正财'],           # 比克财
    '劫财': ['正财', '偏财'],   # 劫克财
}

def shishen_chain_analysis(tg_shishen, wx_scores):
    """分析透干十神之间的生克链。
    tg_shishen: {位置: 十神}  如 {'年干': '正财', '月干': '七杀'}
    wx_scores: {十神: 五行力量}
    返回: [(攻击方, 被攻方, 描述)]"""
    chains = []
    tg_list = list(tg_shishen.items())

    for i, (pos1, ss1) in enumerate(tg_list):
        for j, (pos2, ss2) in enumerate(tg_list):
            if i >= j:
                continue
            if ss2 in SHISHEN_CHAIN.get(ss1, []):
                strength1 = wx_scores.get(ss1, 0)
                strength2 = wx_scores.get(ss2, 0)
                ratio = strength1 / max(strength2, 0.1)
                if ratio > 1.2:
                    desc = '%s(%s,力%.1f) 克 %s(%s,力%.1f) → %s受损' % (
                        pos1, ss1, strength1, pos2, ss2, strength2, ss2)
                    chains.append((ss1, ss2, desc))
    return chains


# ============ 综合工具调用入口 ============
def full_analysis(pillars, ten_gods, gender):
    """一键全查：所有干支关系 + 十神生克链"""
    out = {}

    # 1. 干支关系全查
    rels = all_pillar_relations(pillars)
    out['干支关系'] = rels

    # 2. 透干十神
    tg = {k: v for k, v in ten_gods.items() if k.endswith('天干')}

    # 3. 十神力量（按五行力量映射）
    return out
