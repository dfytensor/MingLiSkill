"""
Integrate ZiweiToolkit and BaziToolkit into the rules engine.
Call tools directly and use their results for scoring.
"""
from __future__ import annotations

import json, sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.ziwei_tools import ZiweiToolkit, PALACE_ORDER
from tools.bazi_tools import BaziToolkit


_zw = ZiweiToolkit()
_bz = BaziToolkit()


def get_ziwei_chart(year, month, day, hour, gender="男"):
    """Get full Ziwei Dou Shu chart."""
    result = _zw.paipan(year, month, day, hour, gender)
    return json.loads(result)


def get_ziwei_personality(ming_stars):
    """Get personality traits from 命宫 stars."""
    result = _zw.analyze_personality(json.dumps(ming_stars, ensure_ascii=False))
    return json.loads(result)


def get_ziwei_career(guanlu_stars, ming_stars):
    """Get career traits from 官禄宫 + 命宫 stars."""
    result = _zw.analyze_career(
        json.dumps(guanlu_stars, ensure_ascii=False),
        json.dumps(ming_stars, ensure_ascii=False),
    )
    return json.loads(result)


def get_ziwei_marriage(couple_stars):
    """Get marriage traits from 夫妻宫 stars."""
    result = _zw.analyze_marriage(json.dumps(couple_stars, ensure_ascii=False))
    return json.loads(result)


def get_ziwei_wealth(caibo_stars):
    """Get wealth traits from 财帛宫 stars."""
    result = _zw.analyze_wealth(json.dumps(caibo_stars, ensure_ascii=False))
    return json.loads(result)


def get_ziwei_health(jie_stars):
    """Get health traits from 疾厄宫 stars."""
    result = _zw.analyze_health(json.dumps(jie_stars, ensure_ascii=False))
    return json.loads(result)


def get_bazi_shensha(year_ganzhi, month_ganzhi, day_ganzhi, hour_ganzhi):
    """Get shensha from BaziToolkit."""
    result = _bz.find_shensha(year_ganzhi, month_ganzhi, day_ganzhi, hour_ganzhi)
    return json.loads(result)


def get_bazi_career(year, month, day, hour, gender="男"):
    """Get career analysis from BaziToolkit."""
    result = _bz.analyze_career(year, month, day, hour, gender)
    return json.loads(result)


def get_bazi_marriage(year, month, day, hour, gender="男"):
    """Get marriage analysis from BaziToolkit."""
    result = _bz.analyze_marriage(year, month, day, hour, gender)
    return json.loads(result)


# Ziwei star → personality keyword mapping
ZIWEI_PERSONALITY_KEYWORDS = {
    "紫微": ["威严", "领袖", "大方", "领导", "高贵", "有主见", "强势", "大方"],
    "天机": ["聪明", "善变", "灵活", "思考", "机智", "多谋", "善变"],
    "太阳": ["热情", "大方", "乐于助人", "阳光", "正义", "开朗"],
    "武曲": ["刚毅", "果断", "重实际", "实干", "决断", "重义"],
    "天同": ["温和", "随和", "享受", "乐观", "懒", "安逸"],
    "廉贞": ["能干", "好胜", "多才", "争强", "傲", "精明"],
    "天府": ["稳重", "保守", "理财", "守成", "可靠", "踏实"],
    "太阴": ["温柔", "敏感", "重感情", "细腻", "多愁", "浪漫"],
    "贪狼": ["多才多艺", "交际", "欲望", "桃花", "喜欢结交", "好动"],
    "巨门": ["口才", "多疑", "分析", "直言", "啰嗦", "多嘴"],
    "天相": ["随和", "协调", "形象", "服务", "圆滑"],
    "天梁": ["正直", "慈悲", "为人师", "老成", "稳重", "有原则"],
    "七杀": ["勇敢", "独立", "冲劲", "好胜", "霸气", "不服输"],
    "破军": ["破坏", "善变", "不守成规", "叛逆", "开创", "折腾"],
}

# Ziwei career star → profession keywords
ZIWEI_CAREER_KEYWORDS = {
    "紫微": ["管理", "领导", "老板", "高管", "政府"],
    "天机": ["技术", "策划", "研究", "咨询", "谋略"],
    "太阳": ["政治", "公关", "服务", "教育", "公益"],
    "武曲": ["金融", "银行", "投资", "财", "实业"],
    "天同": ["服务", "休闲", "餐饮", "娱乐", "文职"],
    "廉贞": ["法律", "军事", "竞争", "技术", "创业"],
    "天府": ["银行", "会计", "管理", "稳定", "财务"],
    "太阴": ["艺术", "设计", "房地产", "文化", "女性"],
    "贪狼": ["销售", "公关", "演艺", "媒体", "交际"],
    "巨门": ["律师", "教师", "口才", "评论", "研究"],
    "天相": ["行政", "秘书", "公关", "服务", "协调"],
    "天梁": ["医生", "教育", "宗教", "公益", "监督"],
    "七杀": ["军警", "执法", "创业", "运动", "冒险"],
    "破军": ["创业", "变革", "运输", "开拓", "冒险"],
}

# Ziwei marriage star → trait keywords
ZIWEI_MARRIAGE_KEYWORDS = {
    "romantic": ["桃花", "恋爱", "浪漫", "多情", "风流"],
    "stable": ["稳定", "和睦", "恩爱", "美满", "白头"],
    "volatile": ["波折", "离", "分手", "争吵", "变故"],
}

# Ziwei health star → organ keywords
ZIWEI_HEALTH_ORGANS = {
    "紫微": ["脾胃", "胃", "脾", "消化"],
    "天机": ["肝", "胆", "神经", "头"],
    "太阳": ["心", "眼", "血液"],
    "武曲": ["肺", "呼吸", "鼻", "皮毛"],
    "天同": ["泌尿", "肾", "膀胱"],
    "廉贞": ["心血管", "心", "血"],
    "天府": ["脾胃", "胃", "脾"],
    "太阴": ["肾", "眼", "目"],
    "贪狼": ["肝", "胆", "泌尿"],
    "巨门": ["口", "喉", "呼吸道", "咽"],
    "天相": ["皮肤", "肠胃", "肠"],
    "天梁": ["骨", "骨骼", "关节"],
    "七杀": ["肺", "呼吸", "外伤", "伤"],
    "破军": ["肾", "泌尿", "生殖"],
}

ZIWEI_STAR_MARRIAGE_TYPE = {
    "紫微": "stable",
    "天府": "stable",
    "天相": "stable",
    "天梁": "stable",
    "天同": "stable",
    "贪狼": "romantic",
    "廉贞": "romantic",
    "破军": "volatile",
    "太阴": "romantic",
    "七杀": "volatile",
    "巨门": "volatile",
    "天机": "volatile",
    "太阳": "stable",
    "武曲": "stable",
}


def build_tool_data(year, month, day, hour, gender="男"):
    """Build all tool data for a given birth info."""
    data = {}

    ziwei = get_ziwei_chart(year, month, day, hour, gender)
    if ziwei.get("success"):
        data["ziwei"] = ziwei
        palaces = ziwei.get("十二宫", {})
        for pname in PALACE_ORDER:
            p = palaces.get(pname, {})
            data[f"zw_{pname}"] = p.get("主星", [])
        data["zw_body_palace"] = ziwei.get("身宫", "命宫")
        data["zw_ju"] = ziwei.get("五行局", "")

    bz = get_bazi_career(year, month, day, hour, gender)
    if bz.get("success"):
        data["bz_career"] = bz

    bz_m = get_bazi_marriage(year, month, day, hour, gender)
    if bz_m.get("success"):
        data["bz_marriage"] = bz_m

    try:
        r = _bz.analyze_health(year, month, day, hour)
        data["bz_health"] = json.loads(r)
    except Exception:
        pass

    try:
        r = _bz.analyze_wealth(year, month, day, hour)
        data["bz_wealth"] = json.loads(r)
    except Exception:
        pass

    try:
        r = _bz.analyze_yin_shou(year, month, day, hour)
        data["bz_education"] = json.loads(r)
    except Exception:
        pass

    try:
        r = _bz.analyze_huoyuan(year, month, day, hour, gender)
        data["bz_huoyuan"] = json.loads(r)
    except Exception:
        pass

    return data
