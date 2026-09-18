# -*- coding: utf-8 -*-
"""
extra_tools.py — 补充确定性计算工具（对齐 Tianfu Agent 的原子工具思路）
每个函数 = 一个精确计算，可直接调用。
"""
import io, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools.calendar_engine import (
    TIANGAN, DIZHI, TIANGAN_IDX, DIZHI_IDX,
    WUXING_GAN, WUXING_ZHI, ZHI_CANG_GAN,
    changsheng_state, kong_wang,
)

# ============ 1. 三方四正 ============
SANFANG = {
    # 命宫的三方四正: 命宫+财帛+官禄+迁移(对宫)
    '命宫': ['财帛', '官禄', '迁移'],
    '财帛': ['命宫', '福德', '夫妻'],  # 实际按宫位排
    '官禄': ['命宫', '夫妻', '田宅'],
    '夫妻': ['官禄', '迁移', '福德'],
    '迁移': ['命宫', '子女', '兄弟'],
    '福德': ['财帛', '父母', '子女'],
    '子女': ['田宅', '兄弟', '父母'],
    '兄弟': ['子女', '迁移', '疾厄'],
    '父母': ['福德', '疾厄', '田宅'],
    '疾厄': ['父母', '仆役', '兄弟'],
    '仆役': ['疾厄', '田宅', '子女'],
    '田宅': ['官禄', '仆役', '父母'],
}


def sanfang_sizheng(palace_name, ziwei_palaces):
    """给定紫微宫位名，返回三方四正的宫位及星曜。
    ziwei_palaces: {宫名: [星曜列表]}"""
    targets = SANFANG.get(palace_name, [])
    result = {palace_name: ziwei_palaces.get(palace_name, [])}
    for t in targets:
        if t in ziwei_palaces:
            result[t] = ziwei_palaces[t]
    return result


# ============ 2. 大限逐岁推演 ============
def dayun_year_by_year(bazi_pillars, gender, birth_year, start_age=1, count=8):
    """将大运细化为逐岁干支，便于精确流年分析。
    返回 [{year, age, dayun_gz, liunian_gz, liunian_shishen}]"""
    from tools.calendar_engine import year_ganzhi, shi_shen
    day_gan = bazi_pillars['日柱'][0]
    year_gz = bazi_pillars['年柱']
    mgz = bazi_pillars['月柱']
    dayun_list = []
    yin_yang = TIANGAN_IDX[year_gz[0]] % 2
    male = gender in ('男', 'M', 'male')
    forward = (male and yin_yang == 0) or (not male and yin_yang == 1)
    mg = TIANGAN_IDX[mgz[0]]
    mz = DIZHI_IDX[mgz[1]]
    for i in range(count):
        if forward:
            g = (mg + i + 1) % 10
            z = (mz + i + 1) % 12
        else:
            g = (mg - i - 1) % 10
            z = (mz - i - 1) % 12
        dy_gz = TIANGAN[g] + DIZHI[z]
        age_start_i = int(start_age) + i * 10
        for age in range(age_start_i, age_start_i + 10):
            year = birth_year + age
            ln_gz = year_ganzhi(year)
            dayun_list.append({
                'year': year, 'age': age,
                'dayun': dy_gz, 'liunian': ln_gz,
                'liunian_shishen': shi_shen(day_gan, ln_gz[0]),
                'dayun_shishen': shi_shen(day_gan, dy_gz[0]),
            })
    return dayun_list


# ============ 3. 紫微四化飞星 ============
SIHUA = {
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


def sihua_feigong(year_gan, ziwei_palaces):
    """按生年天干起四化，查各化星落宫。
    返回 {禄: (星, 宫), 权: (星, 宫), 科: (星, 宫), 忌: (星, 宫)}"""
    sihua = SIHUA.get(year_gan, {})  # {星名: 化型}
    result = {}
    for star, hua_type in sihua.items():
        for palace, stars in ziwei_palaces.items():
            if star in stars:
                result[hua_type] = (star, palace)
                break
    return result


# ============ 4. 用神自动判定（按问题类别） ============
YONGSHEN_RULES = {
    '事业': {'喜': '官印食伤', '忌': '比劫夺官', '主看': '官禄宫+正官七杀+格局'},
    '婚姻': {'喜': '配偶星+配偶宫', '忌': '伤官克官(女)/比劫夺财(男)', '主看': '夫妻宫+日支+配偶星'},
    '财运': {'喜': '财星+食伤生财', '忌': '比劫夺财', '主看': '财帛宫+正财偏财'},
    '健康': {'喜': '五行平衡', '忌': '五行偏枯+七杀攻身', '主看': '疾厄宫+最弱五行'},
    '子女': {'喜': '食伤有力+子女宫强', '忌': '食伤入墓/被合', '主看': '子女宫+时柱+食伤'},
    '学业': {'喜': '印星+文昌', '忌': '财多坏印', '主看': '官禄宫+印星+文昌'},
    '性格': {'喜': '日主本性+命宫主星', '忌': '地支克身过度', '主看': '命宫+日主+天干透出'},
    '六亲': {'喜': '六亲星有根有护', '忌': '六亲星入墓/被冲', '主看': '对应宫位+对应十神'},
}


def auto_yongshen(category, bazi_data):
    """按问题类别返回该类别的用神分析要点。"""
    rules = YONGSHEN_RULES.get(category, {})
    wx = bazi_data.get('五行力量', {})
    yong = bazi_data.get('喜用神', '')
    ji = bazi_data.get('忌神', '')
    day_wx = bazi_data.get('日主五行', '')
    return {
        'category': category,
        '核心规则': rules,
        '全局喜用': yong,
        '全局忌神': ji,
        '日主': day_wx,
        '五行力量': wx,
        '分析要点': '先查%s，再看%s是否有力，最后检查%s' % (
            rules.get('主看', ''), rules.get('喜', ''), rules.get('忌', '')),
    }


# ============ 5. 星曜亮度查表（庙旺利陷） ============
STAR_BRIGHTNESS = {
    '紫微': {'子': '旺', '丑': '庙', '寅': '庙', '卯': '旺', '辰': '得', '巳': '利', '午': '庙', '未': '庙', '申': '旺', '酉': '旺', '戌': '得', '亥': '陷'},
    '天机': {'子': '庙', '丑': '陷', '寅': '得', '卯': '庙', '辰': '利', '巳': '平', '午': '庙', '未': '陷', '申': '得', '酉': '庙', '戌': '利', '亥': '平'},
    '太阳': {'子': '陷', '丑': '陷', '寅': '旺', '卯': '庙', '辰': '得', '巳': '利', '午': '旺', '未': '得', '申': '利', '酉': '平', '戌': '陷', '亥': '陷'},
    '武曲': {'子': '旺', '丑': '庙', '寅': '得', '卯': '利', '辰': '庙', '巳': '平', '午': '旺', '未': '庙', '申': '得', '酉': '利', '戌': '庙', '亥': '平'},
    '天同': {'子': '旺', '丑': '利', '寅': '利', '卯': '平', '辰': '平', '巳': '庙', '午': '旺', '未': '利', '申': '旺', '酉': '平', '戌': '平', '亥': '庙'},
    '廉贞': {'子': '平', '丑': '利', '寅': '庙', '卯': '平', '辰': '利', '巳': '陷', '午': '平', '未': '利', '申': '庙', '酉': '平', '戌': '利', '亥': '陷'},
    '天府': {'子': '庙', '丑': '庙', '寅': '庙', '卯': '得', '辰': '庙', '巳': '得', '午': '旺', '未': '庙', '申': '庙', '酉': '得', '戌': '庙', '亥': '得'},
    '太阴': {'子': '庙', '丑': '庙', '寅': '利', '卯': '陷', '辰': '陷', '巳': '陷', '午': '陷', '未': '利', '申': '利', '酉': '旺', '戌': '旺', '亥': '庙'},
    '贪狼': {'子': '旺', '丑': '庙', '寅': '平', '卯': '利', '辰': '庙', '巳': '陷', '午': '旺', '未': '庙', '申': '平', '酉': '利', '戌': '庙', '亥': '旺'},
    '巨门': {'子': '旺', '丑': '陷', '寅': '庙', '卯': '庙', '辰': '利', '巳': '平', '午': '旺', '未': '陷', '申': '庙', '酉': '庙', '戌': '利', '亥': '旺'},
    '天相': {'子': '庙', '丑': '得', '寅': '庙', '卯': '陷', '辰': '得', '巳': '利', '午': '庙', '未': '得', '申': '庙', '酉': '陷', '戌': '得', '亥': '利'},
    '天梁': {'子': '庙', '丑': '庙', '寅': '庙', '卯': '庙', '辰': '利', '巳': '陷', '午': '庙', '未': '利', '申': '陷', '酉': '得', '戌': '庙', '亥': '庙'},
    '七杀': {'子': '旺', '丑': '庙', '寅': '庙', '卯': '旺', '辰': '利', '巳': '平', '午': '旺', '未': '庙', '申': '庙', '酉': '利', '戌': '利', '亥': '平'},
    '破军': {'子': '庙', '丑': '旺', '寅': '得', '卯': '陷', '辰': '利', '巳': '平', '午': '庙', '未': '旺', '申': '得', '酉': '陷', '戌': '利', '亥': '平'},
}

BRIGHTNESS_SCORE = {'庙': 4, '旺': 3, '得': 2, '利': 1, '平': 0, '陷': -1, '不': -2}


def star_brightness(star_name, palace_zhi):
    """查星曜在宫位的亮度。返回 (亮度文字, 分数)。"""
    b = STAR_BRIGHTNESS.get(star_name, {}).get(palace_zhi, '平')
    return b, BRIGHTNESS_SCORE.get(b, 0)


def palace_brightness_score(ziwei_palaces, palace_zhi_map):
    """给每个宫的星曜打亮度分。
    ziwei_palaces: {宫名: [星名列表]}
    palace_zhi_map: {宫名: 地支}
    返回 {宫名: 总分, 最强星, 最弱星}"""
    result = {}
    for palace, stars in ziwei_palaces.items():
        zhi = palace_zhi_map.get(palace, '')
        total = 0
        best = ('', -99)
        worst = ('', 99)
        for star in stars:
            if star in STAR_BRIGHTNESS:
                b, sc = star_brightness(star, zhi)
                total += sc
                if sc > best[1]:
                    best = (star, sc)
                if sc < worst[1]:
                    worst = (star, sc)
        result[palace] = {'total': total, 'best': best, 'worst': worst}
    return result
