# -*- coding: utf-8 -*-
"""
final_tools.py — 最后一批工具（辅星+格局+三方断语+四化断语）
"""
import json

# ============ 1. 辅星系统 ============
# 六吉星：左辅右弼天魁天鉞文昌文曲 → 增强主星正面特质
# 六煞星：火星铃星地空地劫擎羊陀罗 → 削弱或特化主星
AUX_GOOD = ['左辅', '右弼', '天魁', '天鉞', '文昌', '文曲']
AUX_BAD = ['火星', '铃星', '地空', '地劫', '擎羊', '陀罗']

AUX_EFFECT = {
    '左辅': '助力+：贵人相助，行事顺遂',
    '右弼': '助力+：多人扶助，人际广',
    '天魁': '贵人+：长辈贵人提携',
    '天鉞': '贵人+：异性贵人相助',
    '文昌': '文星+：聪明利考试，利文书',
    '文曲': '才艺+：口才艺术，利表达',
    '火星': '煞星-：急躁冲动，突发达突失败',
    '铃星': '煞星-：内在焦虑，隐性阻力',
    '地空': '空亡-：理想化，财缘薄',
    '地劫': '劫财-：破财，物质损失',
    '擎羊': '刑伤-：刀伤手术，竞争激烈',
    '陀罗': '拖延-：拖延反复，暗斗',
}

def palace_aux_analysis(major_stars, minor_stars):
    """分析辅星对主星的影响。
    返回: (增强描述列表, 削弱描述列表, 净效应评分)"""
    boosts, debuffs = [], []
    for s in minor_stars:
        if s in AUX_GOOD:
            boosts.append(AUX_EFFECT.get(s, s))
        elif s in AUX_BAD:
            debuffs.append(AUX_EFFECT.get(s, s))
    net = len(boosts) - len(debuffs)
    return boosts, debuffs, net


# ============ 2. 紫微格局判定 ============
# 格局条件 → 断语 → 倾向
FORMATS = [
    # ({条件: 宫名→必需主星}, 格局名, 断语, 事业倾向, 富贵倾向)
    ({'命宫': ['紫微', '天府']}, '君臣庆会', '领袖格局，管理人才，稳重大气', '管理', '高'),
    ({'命宫': ['紫微', '七杀']}, '化杀为权', '强势有魄力，权力欲强，开创力强', '开创', '中高'),
    ({'命宫': ['太阳', '巨门']}, '日照雷门', '口才极好，善于表达，适合律师教师传媒', '口才', '中'),
    ({'命宫': ['武曲', '贪狼']}, '武贪同行', '横发格，中年发迹，商业金融', '商业', '高'),
    ({'命宫': ['廉贞', '贪狼']}, '廉贪双美', '社交桃花，多才多艺，娱乐外交', '社交', '中'),
    ({'命宫': ['天同', '太阴']}, '同阴会合', '温和享受，感性细腻，服务业艺术', '服务', '中'),
    ({'命宫': ['天机', '天梁']}, '机梁嘉会', '善策划分析，适合宗教哲学医药研究', '研究', '中'),
    ({'命宫': ['武曲', '天府']}, '财库加会', '理财高手，稳健致富，金融财政', '金融', '高'),
    ({'官禄': ['紫微']}, '紫微守官', '事业有地位，适合领导管理', '管理', '高'),
    ({'官禄': ['武曲']}, '武曲守官', '事业重实际，适合金融军警技术', '技术金融', '中高'),
    ({'官禄': ['太阳']}, '太阳守官', '事业有名声，适合公职传媒教育', '公职传媒', '中高'),
    ({'夫妻': ['天府']}, '天府守夫妻', '配偶稳重有财力，婚姻稳定', '稳定', '中高'),
    ({'夫妻': ['贪狼']}, '贪狼守夫妻', '配偶社交强桃花重，感情需经营', '社交', '中'),
    ({'财帛': ['武曲']}, '武曲守财', '理财能力强，善管理金钱', '理财', '高'),
    ({'财帛': ['天府']}, '天府守财', '财库丰盈，善积累', '积累', '高'),
]

def check_formats(ziwei_palaces):
    """检查命盘符合哪些紫微格局。"""
    hits = []
    for cond, name, desc, career, wealth_level in FORMATS:
        all_match = True
        for palace, required in cond.items():
            available = ziwei_palaces.get(palace, [])
            if not any(star in available for star in required):
                all_match = False
                break
        if all_match:
            hits.append({'格局': name, '断语': desc, '事业倾向': career, '富贵': wealth_level})
    return hits


# ============ 3. 大限/流年四化断语 ============
SIHUA_MEANING = {
    '禄': {
        '事业': '事业有机遇，贵人提携，升职加薪',
        '财运': '进财顺利，收入增加',
        '婚姻': '感情甜蜜，婚事可成',
        '健康': '身体无大碍',
    },
    '权': {
        '事业': '事业有权，掌权升职',
        '竞争': '竞争力强，胜出概率高',
    },
    '科': {
        '学业': '考试顺利，利学术研究',
        '名声': '有名声，受人肯定',
    },
    '忌': {
        '事业': '事业阻碍，工作不顺',
        '财运': '破财，财务纠纷',
        '婚姻': '婚姻不顺，感情困扰',
        '健康': '注意健康，慢性疾病',
    },
}

def sihua_interpret(hua_type, palace, category):
    """四化入宫的断语。"""
    base = SIHUA_MEANING.get(hua_type, {})
    if palace in base:
        return base[palace]
    if category in base:
        return base[category]
    return base.get('事业', '')


# ============ 4. 三方四正组合断语 ============
TRIO_COMBO = {
    # (命宫主星, 官禄主星, 财帛主星) → 综合断语
    ('紫微', '武曲', '天府'): '紫府武廉格局：管理金融才干，稳健领导型',
    ('天机', '天同', '天梁'): '机月同梁格：文职技术策划，稳定但缺乏开创',
    ('太阳', '天梁', '天同'): '阳梁昌禄格：适合公职教育学术',
    ('廉贞', '七杀', '武曲'): '廉杀武格：军警开创，竞争性行业',
    ('武曲', '贪狼', '紫微'): '武贪紫微格：商业金融，中年发迹',
}

def trio_interpret(ming_stars, guanlu_stars, caibo_stars):
    """三方四正组合断语。"""
    for s1 in ming_stars:
        for s2 in guanlu_stars:
            for s3 in caibo_stars:
                combo = (s1, s2, s3)
                if combo in TRIO_COMBO:
                    return TRIO_COMBO[combo]
                # 尝试反向
                if (s3, s2, s1) in TRIO_COMBO:
                    return TRIO_COMBO[(s3, s2, s1)]
    return None


# ============ 5. 大限四化 ============
def dayun_sihua(dayun_gan, ziwei_palaces):
    """大运干四化飞入紫微宫位。"""
    sihua = SIHUA_TABLE.get(dayun_gan, {})
    result = {}
    for star, hua in sihua.items():
        for palace, stars in ziwei_palaces.items():
            if star in stars:
                result[hua] = (star, palace)
                break
    return result


# ============ 6. 流年四化 ============
def liunian_sihua(liunian_gz, ziwei_palaces):
    """流年干四化飞入紫微宫位。"""
    gan = liunian_gz[:1] if liunian_gz else ''
    return dayun_sihua(gan, ziwei_palaces)
