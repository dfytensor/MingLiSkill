"""
MingLi-Bench Rules Engine v3 — tool-integrated rules.
Uses BaziToolkit + ZiweiToolkit for scoring.
"""

from __future__ import annotations

import json, os, sys, time, re, random
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.calendar_engine import (
    TIANGAN, DIZHI, TIANGAN_IDX, DIZHI_IDX,
    WUXING_GAN, WUXING_ZHI, WUXING_SHENG, WUXING_KE,
    WUXING_BEING_SHENG, WUXING_BEING_KE,
    YINYANG_GAN, ZHI_CANG_GAN, CHANGSHENG_12,
    build_four_pillars, build_dayun, build_liunian,
    shi_shen, five_element_strength, nayin, year_ganzhi,
    day_ganzhi_from_date, hour_ganzhi, month_ganzhi,
    changsheng_state, kong_wang, animal_year, wuxing_relation,
)

shen = shi_shen

from tools.tool_integration import (
    build_tool_data,
    ZIWEI_PERSONALITY_KEYWORDS, ZIWEI_CAREER_KEYWORDS,
    ZIWEI_HEALTH_ORGANS, ZIWEI_STAR_MARRIAGE_TYPE,
    ZIWEI_MARRIAGE_KEYWORDS,
    PALACE_ORDER,
)


WX_ORGAN = {
    "木": ("肝", "胆", "筋", "目", "头", "神经"),
    "火": ("心", "小肠", "脉", "舌", "眼", "血液"),
    "土": ("脾", "胃", "肉", "口", "消化", "腹"),
    "金": ("肺", "大肠", "皮毛", "鼻", "呼吸", "骨"),
    "水": ("肾", "膀胱", "骨", "耳", "泌尿", "生殖", "脑"),
}

# ============================================================
# 阴阳五行深化：阴阳平衡 + 五行乘侮病理
# ============================================================
WUXING_TISSUE = {
    "木": ("筋", "爪", "韧带"), "火": ("脉", "血管", "面色"),
    "土": ("肌肉", "四肢", "唇"), "金": ("皮毛", "皮肤", "喉咙"),
    "水": ("骨髓", "头发", "牙齿"),
}

WUXING_EMOTION = {
    "木": ("怒", "烦躁"), "火": ("喜", "狂躁"),
    "土": ("思", "忧虑"), "金": ("悲", "忧愁", "抑郁"),
    "水": ("恐", "惊", "焦虑"),
}

WUXING_SENSE = {"木": "目", "火": "舌", "土": "口", "金": "鼻", "水": "耳"}

WUXING_TASTE = {"木": "酸", "火": "苦", "土": "甘", "金": "辛", "水": "咸"}

WUXING_FLUID = {"木": "泪", "火": "汗", "土": "涎", "金": "涕", "水": "唾"}


def analyze_yinyang_balance(wx_dict):
    """Analyze 阴阳 balance: count 阳(+)/阴(-) 天干地支 to detect 偏盛."""
    result = {}
    # 木火 = 阳, 金水 = 阴, 土 = 中性
    yang_score = wx_dict.get("木", 0) + wx_dict.get("火", 0)
    yin_score = wx_dict.get("金", 0) + wx_dict.get("水", 0)
    total = sum(wx_dict.values()) or 1
    
    result["阳值"] = yang_score
    result["阴值"] = yin_score
    result["阳阴比"] = yang_score / max(yin_score, 0.01)
    
    if yang_score > yin_score * 1.5:
        result["诊断"] = "阳盛阴虚"
        result["倾向病症"] = ["燥热", "口干", "失眠", "易怒", "高血压", "炎症"]
    elif yin_score > yang_score * 1.5:
        result["诊断"] = "阴盛阳虚"
        result["倾向病症"] = ["畏寒", "乏力", "嗜睡", "水肿", "低血压", "抑郁"]
    else:
        result["诊断"] = "阴阳平和"
        result["倾向病症"] = []
    return result


def analyze_wuxing_pathology(wx_dict, yong, ji):
    """五行乘侮分析：检测病理性克害关系。
    乘: too strong → over-acts on the element it normally ke's
    侮: too strong → reverses the ke relationship (insults)
    """
    issues = []
    sorted_wx = sorted(wx_dict.items(), key=lambda x: -x[1])
    strongest = sorted_wx[0][0]
    weakest = sorted_wx[-1][0]
    strong_val = sorted_wx[0][1]
    weak_val = sorted_wx[-1][1]
    total = sum(wx_dict.values()) or 1
    
    # Check each element
    for wx_name, val in wx_dict.items():
        pct = val / total
        # 过旺 (>40%) → 乘其所胜
        if pct > 0.40:
            victim = WUXING_KE.get(wx_name, "")
            if victim:
                issues.append({
                    "类型": "乘",
                    "元凶": wx_name,
                    "受害者": victim,
                    "机制": f"{wx_name}过旺乘{wx_name}克{victim}",
                    "症状": f"{WX_ORGAN.get(victim, ())[0]}系统受损",
                    "紧急度": "高" if victim in ji else "中",
                })
            # 侮其所不胜
            attacker = WUXING_BEING_KE.get(wx_name, "")
            if attacker:
                issues.append({
                    "类型": "侮",
                    "元凶": wx_name,
                    "受害者": attacker,
                    "机制": f"{wx_name}过旺反侮被{attacker}克",
                    "症状": f"{WX_ORGAN.get(attacker, ())[0]}系统异常",
                    "紧急度": "高" if attacker in yong else "中",
                })
        # 过弱 (<10%) → 母病及子 or 子盗母气
        if pct < 0.10 and wx_name in ji:
            mother = WUXING_BEING_SHENG.get(wx_name, "")
            if mother:
                issues.append({
                    "类型": "母虚",
                    "元凶": mother,
                    "受害者": wx_name,
                    "机制": f"{mother}(母)虚不能生{wx_name}(子)",
                    "症状": f"{WX_ORGAN.get(mother, ())[0]}{WX_ORGAN.get(wx_name, ())[0]}同病",
                    "紧急度": "中",
                })
    
    return {"最强": strongest, "最弱": weakest, "病理": issues}


# ============================================================
# 五行中医模块：辨证论治
# ============================================================
TCM_SYNDROME_MAP = {
    # 肝木系统
    ("木", "过旺"): {
        "证型": "肝阳上亢 / 肝火上炎",
        "症状": ["头痛", "眩晕", "目赤", "口苦", "烦躁易怒", "胁痛", "高血压"],
        "治法": "平肝潜阳，清肝泻火",
    },
    ("木", "过弱"): {
        "证型": "肝血虚 / 肝阴虚",
        "症状": ["头晕", "眼花", "视物模糊", "肢体麻木", "筋脉拘急", "月经不调"],
        "治法": "养血柔肝，滋阴补肝",
    },
    # 火心系统
    ("火", "过旺"): {
        "证型": "心火亢盛 / 心火上炎",
        "症状": ["心烦", "失眠", "口舌生疮", "心悸", "舌尖红", "小便赤"],
        "治法": "清心泻火，养心安神",
    },
    ("火", "过弱"): {
        "证型": "心气虚 / 心阳虚",
        "症状": ["心悸", "气短", "自汗", "胸闷", "面色白", "脉弱"],
        "治法": "补心气，温心阳",
    },
    # 土脾系统
    ("土", "过旺"): {
        "证型": "脾虚湿盛 / 湿热蕴脾",
        "症状": ["腹胀", "纳呆", "便溏", "肥胖", "身重", "口腻"],
        "治法": "健脾利湿，清热化湿",
    },
    ("土", "过弱"): {
        "证型": "脾气虚 / 脾阳虚",
        "症状": ["食少", "腹胀", "便溏", "消瘦", "乏力", "面色萎黄", "消化不良"],
        "治法": "健脾益气，温中补虚",
    },
    # 金肺系统
    ("金", "过旺"): {
        "证型": "肺气壅滞 / 肺热壅盛",
        "症状": ["咳嗽", "气喘", "胸闷", "鼻塞", "喉痛", "痰黄", "呼吸不畅"],
        "治法": "宣肺清热，化痰平喘",
    },
    ("金", "过弱"): {
        "证型": "肺气虚 / 肺阴虚",
        "症状": ["咳嗽无力", "气短", "自汗", "易感冒", "皮肤干燥", "声音低"],
        "治法": "补肺益气，滋阴润肺",
    },
    # 水肾系统
    ("水", "过旺"): {
        "证型": "肾不纳气 / 水湿泛滥",
        "症状": ["水肿", "腰酸", "小便不利", "畏寒", "嗜睡", "脑力下降"],
        "治法": "温阳利水，纳气归肾",
    },
    ("水", "过弱"): {
        "证型": "肾阴虚 / 肾精不足",
        "症状": ["腰膝酸软", "耳鸣", "脱发", "健忘", "五心烦热", "骨弱"],
        "治法": "滋阴补肾，填精益髓",
    },
}


def diagnose_tcm(wx_dict, yong, ji):
    """中医辨证：根据五行盛衰给出证型诊断。"""
    results = []
    total = sum(wx_dict.values()) or 1
    for wx_name, val in wx_dict.items():
        pct = val / total
        if pct > 0.35:
            key = (wx_name, "过旺")
        elif pct < 0.08 and wx_name in ji:
            key = (wx_name, "过弱")
        else:
            continue
        syndrome = TCM_SYNDROME_MAP.get(key, {})
        if syndrome:
            results.append({
                "五行": wx_name,
                "状态": key[1],
                "占比": f"{pct:.0%}",
                "证型": syndrome["证型"],
                "症状": syndrome["症状"][:5],
                "治法": syndrome["治法"],
            })
    return results


def _compute_augmented_wuxing(chart, year_eval):
    """Compute augmented五行 by adding流年+大运 influence to native wx."""
    wx = dict(chart.get("五行力量", {}))
    if not wx:
        return {}
    total = sum(wx.values()) or 1
    ln = year_eval.get("ln", {})
    du = year_eval.get("du", {})
    # Add流年 influence (weight: 0.5 per occurrence)
    if ln.get("gan_wx"):
        wx[ln["gan_wx"]] = wx.get(ln["gan_wx"], 0) + 0.8
    if ln.get("zhi_wx"):
        wx[ln["zhi_wx"]] = wx.get(ln["zhi_wx"], 0) + 0.5
    # Add大运 influence (weight: 1.0 per occurrence,大运管10年影响更大)
    if du and du.get("gan_wx"):
        wx[du["gan_wx"]] = wx.get(du["gan_wx"], 0) + 1.2
    if du and du.get("zhi_wx"):
        wx[du["zhi_wx"]] = wx.get(du["zhi_wx"], 0) + 0.8
    return wx


def score_tcm_health(chart, option_text):
    """用中医辨证给健康选项打分。"""
    s = 0.0
    wx = chart.get("五行力量", {})
    yong = chart.get("喜用神", [])
    ji = chart.get("忌神", [])
    
    # Get TCM diagnosis
    diagnoses = diagnose_tcm(wx, yong, ji)
    for diag in diagnoses:
        for symptom in diag.get("症状", []):
            if symptom in option_text:
                s += 2.0
                break  # one symptom match per diagnosis
    
    # Check for specific organ-vs-element matches
    total = sum(wx.values()) or 1
    for wx_name, organs in WX_ORGAN.items():
        pct = wx.get(wx_name, 0) / total
        for organ in organs:
            if organ in option_text:
                if pct > 0.30:
                    s += 1.5  # over-strong element → organ excess syndrome
                elif pct < 0.10 and wx_name in ji:
                    s += 2.0  # weak +忌神 → organ deficiency syndrome
                else:
                    s += 0.5
    
    # Yin-Yang balance → symptom matching
    yy = analyze_yinyang_balance(wx)
    for symptom in yy.get("倾向病症", []):
        if symptom in option_text:
            s += 1.5
    
    # Five element pathology matching
    path = analyze_wuxing_pathology(wx, yong, ji)
    for issue in path.get("病理", []):
        organ_text = issue.get("症状", "")
        for wx_name, organs in WX_ORGAN.items():
            for organ in organs:
                if organ in organ_text and organ in option_text:
                    s += 1.0 if issue["紧急度"] == "高" else 0.5
    
    # Emotion-to-organ matching (情志致病)
    for wx_name, emotions in WUXING_EMOTION.items():
        for em in emotions:
            if em in option_text and wx_name in ji:
                s += 1.2
    
    return s


# ============================================================
# 奇门遁甲评分模块
# ============================================================
def score_qimen_for_option(qimen_data, year, option_text, cat):
    """Use Qimen Dunjia pan data to score an option."""
    s = 0.0
    if not qimen_data:
        return 0.0
    
    year_str = str(year)
    qm = qimen_data.get(year_str, {})
    pan = qm.get("pan", {})
    keji = qm.get("keji", {})
    
    if not pan.get("success"):
        return 0.0
    
    gong_data = pan.get("九宫布局", {})
    
    # Category-specific 用神 checking
    if cat == "健康":
        # 天芮星 = illness star
        # 死门 = death/danger
        for gong_num, gong in gong_data.items():
            stars = gong.get("九星", "")
            men = gong.get("八门", "")
            if "天芮" in str(stars) and ("病" in option_text or "癌" in option_text or "瘤" in option_text):
                s += 2.5
            if "死门" in str(men) and ("死" in option_text or "亡" in option_text or "去世" in option_text):
                s += 2.0
            if "天心" in str(stars) and ("手术" in option_text or "开刀" in option_text or "切除" in option_text):
                s += 1.5  # 天心星 = 医生/手术 star
            if "伤门" in str(men) and ("伤" in option_text or "折" in option_text or "骨折" in option_text):
                s += 1.5
            if "开门" in str(men):
                if "顺利" in option_text or "无" in option_text or "平安" in option_text:
                    s += 1.0  # 开门 = 通达顺利
    
    elif cat == "婚姻":
        for gong_num, gong in gong_data.items():
            men = gong.get("八门", "")
            shen = gong.get("八神", "")
            if "六合" in str(shen) and ("婚" in option_text or "嫁" in option_text):
                s += 2.0  # 六合 = marriage
            if "休门" in str(men) and ("稳定" in option_text or "恩爱" in option_text):
                s += 1.5
            if "死门" in str(men) and ("离" in option_text or "亡" in option_text):
                s += 1.5
    
    elif cat == "财运":
        for gong_num, gong in gong_data.items():
            men = gong.get("八门", "")
            if "生门" in str(men) and ("财" in option_text or "赚" in option_text or "富" in option_text):
                s += 2.0
            if "戊" in pan.get("值符", "") and ("资本" in option_text or "投资" in option_text):
                s += 1.0
    
    elif cat == "事业":
        for gong_num, gong in gong_data.items():
            men = gong.get("八门", "")
            if "开门" in str(men) and ("事业" in option_text or "升" in option_text or "创业" in option_text):
                s += 2.0
            if "杜门" in str(men) and ("技术" in option_text or "保密" in option_text):
                s += 1.0
    
    elif cat == "官非":
        for gong_num, gong in gong_data.items():
            men = gong.get("八门", "")
            if "惊门" in str(men) and ("官司" in option_text or "被告" in option_text or "官非" in option_text):
                s += 2.5
            if "死门" in str(men) and ("牢" in option_text or "狱" in option_text):
                s += 2.0
    
    # 反吟/伏吟 check
    qimen_type = pan.get("阴阳遁", "")
    if qimen_type == "阳遁" and ("旺" in option_text or "顺" in option_text):
        s += 0.5
    if qimen_type == "阴遁" and ("暗" in option_text or "逆" in option_text or "病" in option_text):
        s += 0.5
    
    return s

PERSONALITY_MAP = {
    "甲": {"pos": ["正直", "仁慈", "上进", "领导力", "大方", "有魄力", "不服输"],
           "neg": ["固执", "不够灵活", "死板", "倔强"]},
    "乙": {"pos": ["温柔", "灵活", "善解人意", "体贴", "有艺术天赋", "随和"],
           "neg": ["优柔寡断", "善变", "缺乏主见", "犹豫"]},
    "丙": {"pos": ["热情", "开朗", "大方", "乐于助人", "阳光", "正义感"],
           "neg": ["急躁", "冲动", "粗暴", "易怒"]},
    "丁": {"pos": ["细腻", "敏感", "有洞察力", "善于观察", "聪明", "内心丰富"],
           "neg": ["多疑", "小心眼", "心机重", "记仇"]},
    "戊": {"pos": ["稳重", "厚道", "守信", "可靠", "踏实", "包容"],
           "neg": ["保守", "固执", "缺乏创新", "反应慢"]},
    "己": {"pos": ["细心", "谦虚", "善于照顾人", "勤恳", "忍耐", "务实"],
           "neg": ["多虑", "敏感", "缺乏魄力", "消极"]},
    "庚": {"pos": ["果断", "刚毅", "义气", "勇敢", "执行力强", "重义"],
           "neg": ["冷酷", "好胜", "不够圆滑", "强硬"]},
    "辛": {"pos": ["精明", "追求完美", "有品味", "敏锐", "细腻"],
           "neg": ["虚荣", "尖刻", "过于挑剔", "好面子"]},
    "壬": {"pos": ["聪明", "灵活", "有谋略", "大气", "善于交际", "适应力强"],
           "neg": ["善变", "不专一", "虎头蛇尾", "贪玩"]},
    "癸": {"pos": ["智慧", "内敛", "有耐力", "善于思考", "谦虚"],
           "neg": ["阴郁", "内向过头", "想太多", "消极", "被动"]},
}

PROFESSION_TENGOD = {
    "正官": ["公务员", "政府", "管理", "行政", "体制内", "领导", "保险"],
    "七杀": ["军警", "执法", "医生", "外科", "律师", "创业", "的士", "运输"],
    "正印": ["教师", "文员", "秘书", "图书馆", "研究", "学术", "文职"],
    "偏印": ["技术", "研发", "设计", "艺术", "自由职业", "非主流"],
    "正财": ["银行", "会计", "财务", "零售", "职员", "固定工作"],
    "偏财": ["生意", "销售", "公关", "投资", "中介", "地产"],
    "食神": ["餐饮", "文学", "艺术", "表演", "教育", "服务"],
    "伤官": ["技术", "创意", "设计", "自由业", "演艺", "颠覆性"],
    "比肩": ["合作创业", "同行", "体力活", "运动"],
    "劫财": ["投机", "竞争性行业", "销售", "冒险性行业"],
}

WX_PERSONALITY_EXTRA = {
    "木旺": ["仁慈", "固执", "直率", "不屈服"],
    "火旺": ["热情", "急躁", "好面子", "好表现"],
    "土旺": ["稳重", "保守", "讲信用", "慢热"],
    "金旺": ["果断", "好胜", "讲义气", "刚强"],
    "水旺": ["聪明", "善变", "深藏不露", "灵活"],
    "木弱": ["缺乏主见", "胆小"],
    "火弱": ["缺乏热情", "冷漠"],
    "土弱": ["不信守承诺", "浮躁"],
    "金弱": ["优柔寡断", "软弱"],
    "水弱": ["缺乏变通", "死板"],
}


def _j(s):
    try:
        return json.loads(s)
    except:
        return {}


def compute_chart(bi):
    y, m, d, h = bi.get("year"), bi.get("month"), bi.get("day"), bi.get("hour") or 12
    g = bi.get("gender") or "男"
    if not all([y, m, d]):
        return {}
    c = build_four_pillars(y, m, d, h, g)
    c["gender"] = g
    c["birth_year"] = y
    c["birth_month"] = m
    c["birth_day"] = d
    c["birth_hour"] = h
    pillars = c.get("四柱", {})
    ygz = pillars.get("年柱", "")
    mgz = pillars.get("月柱", "")
    if ygz and mgz:
        c["大运"] = build_dayun(g, ygz, mgz, 1)
    return c


def _get_tool_data(bi):
    y, m, d, h = bi.get("year"), bi.get("month"), bi.get("day"), bi.get("hour") or 12
    g = bi.get("gender") or "男"
    if not all([y, m, d]):
        return {}
    try:
        return build_tool_data(y, m, d, h, g)
    except Exception:
        return {}


def _score_ziwei(text, tool_data, cat):
    """Score using Ziwei Dou Shu data — LIGHTWEIGHT secondary signal only."""
    s = 0.0
    if not tool_data:
        return 0.0

    if cat == "性格":
        ming_stars = tool_data.get("zw_命宫", [])
        for star in ming_stars:
            for kw in ZIWEI_PERSONALITY_KEYWORDS.get(star, []):
                if kw in text:
                    s += 0.8

    elif cat == "事业":
        guanlu_stars = tool_data.get("zw_官禄", [])
        ming_stars = tool_data.get("zw_命宫", [])
        for star in guanlu_stars + ming_stars:
            for kw in ZIWEI_CAREER_KEYWORDS.get(star, []):
                if kw in text:
                    s += 0.8
        bz_career = tool_data.get("bz_career", {})
        geju = bz_career.get("格局倾向", "")
        if geju == "官印相生":
            if "管理" in text or "公务员" in text or "政府" in text: s += 0.5
        elif geju == "食伤生财":
            if "创业" in text or "生意" in text or "技术" in text: s += 0.5
        elif geju == "杀印相生":
            if "军" in text or "警" in text or "技术" in text: s += 0.5
        elif geju == "身旺任财":
            if "生意" in text or "投资" in text or "创业" in text: s += 0.5

    elif cat == "外貌":
        ming_stars = tool_data.get("zw_命宫", [])
        star_looks = {
            "紫微": ["高贵", "端庄", "大方"],
            "天机": ["瘦", "清秀"],
            "太阳": ["圆", "红润", "大方"],
            "武曲": ["方", "刚毅"],
            "天同": ["圆", "胖", "丰满"],
            "廉贞": ["高", "瘦"],
            "天府": ["方", "厚", "稳重"],
            "太阴": ["白", "秀气", "温柔"],
            "贪狼": ["美", "艳", "高"],
            "巨门": ["瘦", "尖"],
            "天相": ["方脸", "端正"],
            "天梁": ["老成", "厚"],
            "七杀": ["锐", "刚"],
            "破军": ["高", "瘦", "俊"],
        }
        for star in ming_stars:
            for kw in star_looks.get(star, []):
                if kw in text:
                    s += 0.8

    elif cat == "学业":
        ming_stars = tool_data.get("zw_命宫", [])
        guanlu_stars = tool_data.get("zw_官禄", [])
        all_stars = ming_stars + guanlu_stars
        has_wenchang_type = any(st in ("天机", "巨门", "天梁") for st in all_stars)
        has_leader = any(st in ("紫微", "天府", "太阳", "武曲") for st in all_stars)
        if has_wenchang_type:
            if "大学" in text or "硕士" in text or "博士" in text: s += 0.5
        if has_leader:
            if "大学" in text or "毕业" in text: s += 0.3

    return s


def year_ganzhi_detail(year):
    gz = year_ganzhi(year)
    return {
        "ganzhi": gz, "gan": gz[0], "zhi": gz[1],
        "gan_wx": WUXING_GAN[gz[0]], "zhi_wx": WUXING_ZHI[gz[1]],
    }


def get_dayun_at(day_gan, year_ganzhi_str, month_ganzhi_str, gender, target_year, birth_year):
    yin_yang = TIANGAN_IDX[year_ganzhi_str[0]] % 2
    male = gender in ("男", "M", "male")
    forward = (male and yin_yang == 0) or (not male and yin_yang == 1)
    mg = TIANGAN_IDX[month_ganzhi_str[0]]
    mz = DIZHI_IDX[month_ganzhi_str[1]]
    age = target_year - birth_year
    for i in range(8):
        if forward:
            g = (mg + i + 1) % 10; z = (mz + i + 1) % 12
        else:
            g = (mg - i - 1) % 10; z = (mz - i - 1) % 12
        s = i * 10 + 1; e = s + 9
        if s <= age <= e:
            gz = TIANGAN[g] + DIZHI[z]
            return {"ganzhi": gz, "gan": gz[0], "zhi": gz[1],
                    "gan_wx": WUXING_GAN[gz[0]], "zhi_wx": WUXING_ZHI[gz[1]],
                    "start_age": s, "end_age": e}
    return {}


def eval_year(chart, year):
    """Evaluate the Bazi dynamics for a specific year. Returns rich dict."""
    day_gan = chart["日主"]
    day_wx = chart["日主五行"]
    strong = chart["日主强弱"] == "身强"
    yong = chart["喜用神"]
    ji = chart["忌神"]
    pillars = chart["四柱"]
    wx = chart["五行力量"]
    tg = chart["十神"]

    ln = year_ganzhi_detail(year)
    ln["gan_ss"] = shen(day_gan, ln["gan"])
    ln["zhi_cang"] = ZHI_CANG_GAN.get(ln["zhi"], [])
    ln["zhi_cang_ss"] = [shen(day_gan, c) for c in ln["zhi_cang"]]
    ln["rel_gan"] = wuxing_relation(day_wx, ln["gan_wx"])
    ln["rel_zhi"] = wuxing_relation(day_wx, ln["zhi_wx"])

    ln["is_yong"] = (ln["gan_wx"] == yong or ln["zhi_wx"] == yong or
                     WUXING_SHENG.get(ln["gan_wx"]) == yong or
                     WUXING_SHENG.get(ln["zhi_wx"]) == yong)
    ln["is_ji"] = (ln["gan_wx"] == ji or ln["zhi_wx"] == ji or
                   WUXING_SHENG.get(ln["gan_wx"]) == ji or
                   WUXING_SHENG.get(ln["zhi_wx"]) == ji)

    ygz = pillars.get("年柱", "")
    mgz = pillars.get("月柱", "")
    du = get_dayun_at(day_gan, ygz, mgz, chart.get("gender", "男"),
                      year, chart.get("birth_year", 1990))
    if du:
        du["gan_ss"] = shen(day_gan, du["gan"])
        du["zhi_cang"] = ZHI_CANG_GAN.get(du["zhi"], [])
        du["zhi_cang_ss"] = [shen(day_gan, c) for c in du["zhi_cang"]]
        du["is_yong"] = (du["gan_wx"] == yong or du["zhi_wx"] == yong or
                         WUXING_SHENG.get(du["gan_wx"]) == yong)
        du["is_ji"] = (du["gan_wx"] == ji or du["zhi_wx"] == ji or
                       WUXING_SHENG.get(du["gan_wx"]) == ji)

    all_ss = set()
    for s in [ln["gan_ss"]] + ln["zhi_cang_ss"]:
        if s: all_ss.add(s)
    if du:
        for s in [du.get("gan_ss", "")] + du.get("zhi_cang_ss", []):
            if s: all_ss.add(s)

    chong_pairs = []
    he_pairs = []
    hai_pairs = []
    po_pairs = []
    pillar_zhis = [gz[1] for gz in pillars.values() if gz and len(gz) > 1]
    for pzh in pillar_zhis:
        r = _check_chong_he(pzh, ln["zhi"])
        if "六冲" in r: chong_pairs.append((pzh, ln["zhi"], "流年冲命"))
        if "六合" in r: he_pairs.append((pzh, ln["zhi"], "流年合命"))
        if "三合" in r: he_pairs.append((pzh, ln["zhi"], "流年三合命"))
        if "六害" in r: hai_pairs.append((pzh, ln["zhi"], "流年害命"))
        if "六破" in r: po_pairs.append((pzh, ln["zhi"], "流年破命"))
    if du:
        for pzh in pillar_zhis:
            r = _check_chong_he(pzh, du["zhi"])
            if "六冲" in r: chong_pairs.append((pzh, du["zhi"], "大运冲命"))
            if "六合" in r: he_pairs.append((pzh, du["zhi"], "大运合命"))
            if "六害" in r: hai_pairs.append((pzh, du["zhi"], "大运害命"))
            if "六破" in r: po_pairs.append((pzh, du["zhi"], "大运破命"))

    return {"ln": ln, "du": du, "all_ss": all_ss,
            "chong": chong_pairs, "he": he_pairs,
            "hai": hai_pairs, "po": po_pairs,
            "day_gan": day_gan, "day_wx": day_wx,
            "strong": strong, "yong": yong, "ji": ji,
            "wx": wx, "tg": tg, "pillars": pillars}


def _check_chong_he(z1, z2):
    pair = tuple(sorted([z1, z2]))
    liu_chong = {("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"),
                 ("辰", "戌"), ("巳", "亥")}
    liu_he = {("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"),
              ("巳", "申"), ("午", "未")}
    liu_hai = {tuple(sorted(p)) for p in [("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"),
               ("申", "亥"), ("酉", "戌")]}
    liu_po = {tuple(sorted(p)) for p in [("子", "酉"), ("寅", "亥"), ("辰", "丑"), ("午", "卯"),
              ("申", "巳"), ("戌", "未")]}
    san_he = [{("申", "子"), ("子", "辰"), ("辰", "申")},
              {("亥", "卯"), ("卯", "未"), ("未", "亥")},
              {("寅", "午"), ("午", "戌"), ("戌", "寅")},
              {("巳", "酉"), ("酉", "丑"), ("丑", "巳")}]

    results = []
    if pair in liu_chong: results.append("六冲")
    if pair in liu_he: results.append("六合")
    if pair in liu_hai: results.append("六害")
    if pair in liu_po: results.append("六破")
    for trio in san_he:
        if z1 in set().union(*[set(t) for t in trio]) and z2 in set().union(*[set(t) for t in trio]) and z1 != z2:
            results.append("三合")
    return results


def extract_years_from_options(options):
    years = {}
    for o in options:
        nums = re.findall(r'(?:19|20)\d{2}', o.get("text", ""))
        if nums:
            years[o["letter"]] = int(nums[0])
    return years


def extract_question_year(q_text):
    """Extract year from question text. For multi-year questions, returns last year (culmination)."""
    years = re.findall(r'(\d{4})\s*年', q_text)
    if not years:
        return None
    if len(years) >= 2 and re.search(r'(?:和|与|及|、).{0,2}\d{4}\s*年', q_text):
        return int(years[-1])
    return int(years[0])


def score_option_v2(opt_text, chart, cat, q_text, year_eval=None):
    """Score a single option. year_eval is the eval_year result if available."""
    s = 0.0
    if not chart:
        return 0.0

    day_gan = chart["日主"]
    day_wx = chart["日主五行"]
    strong = chart["日主强弱"] == "身强"
    yong = chart["喜用神"]
    ji = chart["忌神"]
    wx = chart["五行力量"]
    tg = chart["十神"]
    gender = chart.get("gender", "男")
    pillars = chart["四柱"]

    if year_eval:
        all_ss = year_eval["all_ss"]
        chong = year_eval["chong"]
        he = year_eval["he"]
        ln = year_eval["ln"]
        du = year_eval["du"]
        is_favorable = ln.get("is_yong") or du.get("is_yong")
        is_unfavorable = ln.get("is_ji") or du.get("is_ji")
    else:
        all_ss = set(tg.values())
        chong = []
        he = []
        ln = {}
        du = {}
        is_favorable = False
        is_unfavorable = False

    has_health_neg = bool(re.search(r'病|抑郁|癌|手术|患|过世|逝世|去世|药|疾|痛|住院|医疗', opt_text))
    has_accident = bool(re.search(r'交通|意外|撞|车祸|事故|跌|伤|灾', opt_text))
    has_death = bool(re.search(r'过世|逝世|去世|亡|死', opt_text))
    has_marriage_pos = bool(re.search(r'认识.{0,4}妻|认识.{0,4}夫|结婚|恋爱|交往|拍拖|新婚|姻缘|美满', opt_text))
    has_divorce = bool(re.search(r'离|分居|分手|外遇|情人|出轨', opt_text))
    has_wealth_pos = bool(re.search(r'得财|赚|发|意外之财|横财|中.|赢|财富增加|收入.*增|积蓄', opt_text))
    has_wealth_neg = bool(re.search(r'破财|输|亏|负债|欠|赔|诈|骗|破产|债务', opt_text))
    has_career_pos = bool(re.search(r'升|晋升|提升|创业成功|加薪|提拔|融资', opt_text))
    has_career_neg = bool(re.search(r'失业|倒闭|被辞|失败|降', opt_text))
    has_study_pos = bool(re.search(r'毕业|升学|考上|留学|录取|及格', opt_text))
    has_study_neg = bool(re.search(r'辍学|落榜|没考|退学', opt_text))
    has_child = bool(re.search(r'生|怀孕|添丁|子女|孩子|宝宝', opt_text))
    has_lawsuit = bool(re.search(r'官非|坐牢|被捕|犯|法庭|被告|刑事|牢', opt_text))

    is_negative_event = (has_health_neg or has_accident or has_death or has_divorce or
                         has_wealth_neg or has_career_neg or has_lawsuit)
    is_positive_event = (has_marriage_pos or has_wealth_pos or has_career_pos or
                         has_study_pos or has_child)

    # ===== Category-specific scoring =====

    if cat == "健康":
        organ_mentioned = {}
        for wx_name, organs in WX_ORGAN.items():
            for organ in organs:
                if organ in opt_text:
                    organ_mentioned.setdefault(wx_name, []).append(organ)

        if "七杀" in all_ss:
            s += 2.5 if has_health_neg else 0
            s += 2.0 if has_accident else 0
            s += 1.5 if has_surgery_word(opt_text) else 0
        if "伤官" in all_ss:
            s += 2.0 if has_health_neg else 0
            s += 1.5 if has_accident else 0
        if "偏印" in all_ss:
            s += 1.0 if has_health_neg else 0
        if chong:
            s += 1.5 if has_accident else 0
            s += 1.0 if has_health_neg else 0
        if is_unfavorable:
            s += 2.0 if has_health_neg else 0
            s += 1.0 if has_accident else 0
            s -= 1.0 if is_positive_event else 0
        if is_favorable:
            s -= 1.5 if has_health_neg else 0
            s -= 1.0 if has_accident else 0  # 喜用年意外也应该少
            s += 0.5 if ("没" in opt_text or "平安" in opt_text or "无" in opt_text) else 0

        # Interaction bonus for health
        s += get_interaction_bonus(all_ss, "健康", gender)
        # 七杀+伤官 both present = high surgery/accident risk
        if "七杀" in all_ss and "伤官" in all_ss:
            s += 2.0 if has_health_neg else 0
            s += 2.0 if has_accident else 0
            s += 2.0 if has_surgery_word(opt_text) else 0
        # 七杀+劫财 = violent accident
        if "七杀" in all_ss and "劫财" in all_ss:
            s += 1.5 if has_accident else 0

        if organ_mentioned:
            weak_wx = min(wx, key=wx.get)
            strong_wx = max(wx, key=wx.get)
            if weak_wx in organ_mentioned:
                s += 2.0
            # Use augmented五行 if year context available
            if year_eval:
                aug_wx = _compute_augmented_wuxing(chart, year_eval)
                aug_strong = max(aug_wx, key=aug_wx.get) if aug_wx else strong_wx
                aug_weak = min(aug_wx, key=aug_wx.get) if aug_wx else weak_wx
                # Check乘: augmented strongest克其胜
                ke_victim = WUXING_KE.get(aug_strong, "")
                if ke_victim in organ_mentioned:
                    s += 3.0  # strong乘关系 = disease from乘
                # Check侮: augmented element克 strongest? No.
                # Check侮: org element被某元素克, but that克者 surged →反侮
                for org_wx_name, _ in organ_mentioned.items():
                    # Find who克's this organ element
                    for attacker, victim in WUXING_KE.items():
                        if victim == org_wx_name:
                            # attacker克organ. Does attacker surge in aug?
                            aug_attacker = aug_wx.get(attacker, 0)
                            native_attacker = wx.get(attacker, 0)
                            if aug_attacker > native_attacker * 2 and aug_attacker > 2.0:
                                # attacker surged significantly →反侮organ
                                s += 2.5
                        # Also: organ element克 someone, and that someone surged →侮 organ
                        if attacker == org_wx_name:
                            aug_victim = aug_wx.get(victim, 0)
                            native_victim = wx.get(victim, 0)
                            if aug_victim > native_victim * 3 and aug_victim > 2.5:
                                # The克 target surged →反侮克者(organ)
                                s += 2.5
            ke_wx = WUXING_KE.get(strong_wx, "")
            if ke_wx in organ_mentioned:
                s += 1.5
            if ji in organ_mentioned:
                s += 2.0  # boosted: 忌神器官更危险

        if has_death:
            if chong and is_unfavorable:
                s += 3.0
            else:
                s -= 0.5

        # Pregnancy/miscarriage option-level detection
        is_birth = bool(re.search(r'开刀生|生小孩|剖腹', opt_text))
        is_miscarriage = bool(re.search(r'流产|堕胎|小产|滑胎', opt_text))
        if is_birth or is_miscarriage:
            yin_stars = ("正印", "偏印")
            child_stars = ("食神", "伤官")
            yin_count = sum(1 for s in all_ss if s in yin_stars)
            child_count = sum(1 for s in all_ss if s in child_stars)
            if yin_count >= 2 and child_count >= 1:
                if is_miscarriage: s += 2.5
                if is_birth: s -= 1.5
            if child_count >= 1 and yin_count < 2:
                if is_birth: s += 1.5
                if is_miscarriage: s -= 1.0
            zi_mu = {"戌", "辰", "丑", "未"}
            yr_zhi_in_mu = False
            if year_eval:
                yr_zhi_check = year_eval["ln"].get("zhi", "")
                yr_zhi_in_mu = yr_zhi_check in zi_mu
            has_child_ss = any(s in child_stars for s in all_ss)
            if yr_zhi_in_mu and has_child_ss:
                if is_miscarriage: s += 2.5
                if is_birth: s -= 1.5

        # TCM diagnosis scoring (chart-level only, not year-specific)
        if not year_eval:
            s += score_tcm_health(chart, opt_text)
        spouse_ss = ["正财", "偏财"] if gender in ("男", "M", "male") else ["正官", "七杀"]
        has_spouse_ss = any(x in all_ss for x in spouse_ss)
        peach_zhi = {"子", "午", "卯", "酉"}
        ln_zhi = ln.get("zhi", "")
        has_peach = ln_zhi in peach_zhi
        has_he_zhi = bool(he)

        if has_spouse_ss:
            s += 3.0 if has_marriage_pos else 0
            s -= 1.0 if has_divorce else 0
        if has_peach:
            s += 1.5 if has_marriage_pos else 0
        if has_he_zhi:
            s += 2.0 if has_marriage_pos else 0
            s -= 0.5 if has_divorce else 0
        if "比肩" in all_ss or "劫财" in all_ss:
            s += 1.5 if has_divorce else 0
            s += 1.0 if "外遇" in opt_text or "情人" in opt_text else 0
            s -= 0.5 if has_marriage_pos else 0
        if "伤官" in all_ss and gender in ("女", "F", "female"):
            s += 2.0 if has_divorce else 0
            if not has_spouse_ss:
                s += 1.5 if has_divorce else 0
        if "食神" in all_ss:
            s += 0.5 if has_marriage_pos else 0
        if is_favorable:
            s += 1.5 if has_marriage_pos else 0
            s -= 1.0 if has_divorce else 0
        if is_unfavorable:
            s += 1.0 if has_divorce else 0
            s -= 0.5 if has_marriage_pos else 0
        if chong:
            s += 1.0 if has_divorce else 0

        s += get_interaction_bonus(all_ss, "婚姻", gender)

        if "美满" in opt_text or "恩爱" in opt_text:
            if is_favorable and has_spouse_ss:
                s += 2.0
            elif is_unfavorable:
                s -= 1.0
        if "至今未婚" in opt_text or "单身" in opt_text:
            if has_spouse_ss or has_he_zhi:
                s -= 2.0
            else:
                s += 1.0

        if gender in ("男", "M", "male"):
            day_to_spouse = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
            sp_wx = day_to_spouse.get(day_wx, "金")
            cai_wx_val = chart.get("五行力量", {}).get(sp_wx, 5)
            if cai_wx_val < 1.0:
                if "独身" in opt_text or "清心寡欲" in opt_text or "单身" in opt_text or "未嫁" in opt_text:
                    s += 3.0
                if "已婚" in opt_text and "未" not in opt_text:
                    s -= 1.5
        elif gender in ("女", "F", "female"):
            guan_wx_from_day = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}
            guan_wx = guan_wx_from_day.get(day_wx, "水")
            guan_wx_val = chart.get("五行力量", {}).get(guan_wx, 5)
            if guan_wx_val < 1.0:
                if "独身" in opt_text or "单身" in opt_text or "未嫁" in opt_text or "一生未" in opt_text:
                    s += 2.5

    elif cat == "财运":
        wealth_ss = {"正财", "偏财"}
        robber_ss = {"比肩", "劫财"}
        food_ss = {"食神", "伤官"}
        has_w = bool(all_ss & wealth_ss)
        has_r = bool(all_ss & robber_ss)
        has_f = bool(all_ss & food_ss)

        if has_w and not has_r:
            s += 3.0 if has_wealth_pos else 0
            s -= 1.5 if has_wealth_neg else 0
        if has_r and not has_w:
            s += 2.5 if has_wealth_neg else 0
            s -= 1.0 if has_wealth_pos else 0
        if has_w and has_r:
            s += 1.0 if has_wealth_neg else 0
            s += 0.5 if has_wealth_pos else 0
        if has_f:
            s += 1.5 if has_wealth_pos else 0
        if "正财" in all_ss and "正官" in all_ss:
            s += 1.0 if ("稳定" in opt_text or "理财" in opt_text or "积蓄" in opt_text) else 0
        if is_favorable:
            s += 1.5 if has_wealth_pos else 0
        if is_unfavorable:
            s += 1.5 if has_wealth_neg else 0
        if has_lawsuit and ("诈" in opt_text or "骗" in opt_text):
            s += 1.0

        if "欠" in opt_text or "债务" in opt_text or "负债" in opt_text:
            if has_r and is_unfavorable:
                s += 2.5
        if "理" in opt_text and "财" in opt_text:
            if strong and "正财" in all_ss:
                s += 1.5
            if not strong:
                s -= 0.5

    elif cat == "事业":
        if "正官" in all_ss or "七杀" in all_ss:
            s += 2.5 if has_career_pos else 0
        if "正印" in all_ss:
            s += 1.0 if has_career_pos else 0
        if "食神" in all_ss or "伤官" in all_ss:
            s += 1.5 if ("创业" in opt_text or "技术" in opt_text) else 0
        if is_favorable:
            s += 2.0 if has_career_pos else 0
            s -= 1.0 if has_career_neg else 0
        if is_unfavorable:
            s += 1.5 if has_career_neg else 0
        if chong:
            s += 1.0 if has_career_neg else 0

        for ss_name, profs in PROFESSION_TENGOD.items():
            if ss_name in all_ss or ss_name in set(tg.values()):
                for p in profs:
                    if p in opt_text:
                        s += 1.5
        if strong:
            if "管理" in opt_text or "领导" in opt_text or "老板" in opt_text:
                s += 1.0
        if not strong:
            if "文职" in opt_text or "职员" in opt_text or "文员" in opt_text:
                s += 1.0

    elif cat == "性格":
        dp = PERSONALITY_MAP.get(day_gan, {})
        for trait in dp.get("pos", []):
            if trait in opt_text:
                s += 2.0
        for trait in dp.get("neg", []):
            if trait in opt_text:
                s += 1.5

        strongest = max(wx, key=wx.get)
        weakest = min(wx, key=wx.get)
        for trait in WX_PERSONALITY_EXTRA.get(strongest + "旺", []):
            if trait in opt_text:
                s += 1.5
        for trait in WX_PERSONALITY_EXTRA.get(weakest + "弱", []):
            if trait in opt_text:
                s += 1.0

        dominant_gods = {}
        for pos, god in tg.items():
            dominant_gods[god] = dominant_gods.get(god, 0) + 1
        top3 = sorted(dominant_gods.items(), key=lambda x: -x[1])[:3]

        god_traits = {
            "正官": ["守规矩", "正直", "传统", "保守"],
            "七杀": ["好胜", "急躁", "果断", "不服输", "霸道"],
            "正印": ["善良", "仁慈", "爱学习", "文静", "被动"],
            "偏印": ["多疑", "敏感", "多才", "特立独行"],
            "正财": ["勤恳", "务实", "节俭", "守本分"],
            "偏财": ["大方", "好交际", "重享受"],
            "食神": ["温和", "有口福", "乐观", "善良"],
            "伤官": ["傲气", "叛逆", "口才好", "不服输", "任性"],
            "比肩": ["自尊心强", "独立", "不服输"],
            "劫财": ["好赌", "好胜", "冲动"],
        }
        for god, cnt in top3:
            for trait in god_traits.get(god, []):
                if trait in opt_text:
                    s += 1.0 * min(cnt, 2)

        if not strong:
            if "耳根子软" in opt_text or "不善拒绝" in opt_text or "被动" in opt_text:
                s += 1.5
            if "付出" in opt_text and "压榨" in opt_text:
                s += 1.5
        if strong:
            if "强势" in opt_text or "固执" in opt_text or "有主见" in opt_text:
                s += 1.0

        if "内向" in opt_text or "沉默" in opt_text:
            if day_wx in ("水", "土") and not strong:
                s += 1.5
        if "外向" in opt_text or "胆大" in opt_text:
            if day_wx in ("火", "金") and strong:
                s += 1.5

    elif cat == "家庭":
        if "正印" in all_ss or "偏印" in all_ss:
            if "父" in opt_text or "母" in opt_text:
                s += 1.5
        if "比肩" in all_ss or "劫财" in all_ss:
            if "兄" in opt_text or "弟" in opt_text or "姐" in opt_text or "妹" in opt_text:
                s += 1.5
        if is_unfavorable:
            if has_death:
                s += 2.5
            if has_health_neg:
                s += 1.5
            if "破产" in opt_text or "赌" in opt_text:
                s += 1.0
        if chong:
            if has_death or has_health_neg:
                s += 1.5

        ygz = pillars.get("年柱", "")
        mgz = pillars.get("月柱", "")
        if ygz:
            yz = ygz[1]
            if "冲" in str(_check_chong_he(yz, ln.get("zhi", ""))):
                if "父" in opt_text and has_death:
                    s += 2.0

        if "跟" in opt_text and "母" in opt_text:
            if "偏财" in tg.values() or "正财" in tg.values():
                s += 0.5
        if "跟" in opt_text and "父" in opt_text:
            if "比肩" in tg.values():
                s += 0.5

        if "不在父母身边" in opt_text or "孤儿" in opt_text:
            if is_unfavorable and "偏印" not in all_ss:
                s += 1.5

        if "融洽" in opt_text:
            if is_favorable:
                s += 1.0
            else:
                s -= 0.5
        if "淡薄" in opt_text:
            if is_unfavorable:
                s += 1.0

    elif cat == "子女":
        child_ss = {"食神", "伤官"}
        if all_ss & child_ss:
            s += 3.0 if has_child else 0
        if "正印" in all_ss:
            s += 1.0 if has_child else 0
        if is_favorable:
            s += 1.0 if has_child else 0

    elif cat == "学业":
        if "正印" in all_ss or "偏印" in all_ss:
            s += 3.0 if has_study_pos else 0
            s -= 1.0 if has_study_neg else 0
        if "食神" in all_ss:
            s += 1.0 if has_study_pos else 0
        if "伤官" in all_ss:
            s += 1.0 if has_study_neg else 0
        if is_favorable:
            s += 1.5 if has_study_pos else 0
        if is_unfavorable:
            s += 1.0 if has_study_neg else 0
        if strong:
            s += 0.5 if has_study_pos else 0
        else:
            if has_study_neg:
                s += 0.5

    elif cat == "外貌":
        looks = {
            "木": ["修长", "高", "瘦", "瘦削"],
            "火": ["红润", "尖", "上尖下阔"],
            "土": ["厚", "方", "圆", "胖", "矮", "肥"],
            "金": ["白", "方脸", "眉目"],
            "水": ["黑", "圆脸", "胖", "丰满"],
        }
        for trait in looks.get(day_wx, []):
            if trait in opt_text:
                s += 2.0
        st = max(wx, key=wx.get)
        for trait in looks.get(st, []):
            if trait in opt_text:
                s += 1.5
        if strong:
            if "肥" in opt_text or "壮" in opt_text:
                s += 0.5
        else:
            if "瘦" in opt_text or "瘦削" in opt_text:
                s += 0.5

    elif cat == "官非":
        if "七杀" in all_ss:
            s += 3.0 if has_lawsuit else 0
        if "伤官" in all_ss:
            s += 2.0 if has_lawsuit else 0
        if is_unfavorable:
            s += 1.5 if has_lawsuit else 0
        if chong:
            s += 1.0 if has_lawsuit else 0

    elif cat == "灾劫":
        if "七杀" in all_ss or "伤官" in all_ss:
            s += 3.0 if has_accident else 0
        if chong:
            s += 2.0 if has_accident else 0
        if is_unfavorable:
            s += 2.0 if (has_accident or has_health_neg) else 0
            s -= 1.5 if is_positive_event else 0

    elif cat == "运势":
        if is_favorable and not is_unfavorable:
            s += 2.0 if is_positive_event else 0
            s -= 1.5 if is_negative_event else 0
        if is_unfavorable and not is_favorable:
            s += 2.0 if is_negative_event else 0
            s -= 1.0 if is_positive_event else 0
        if chong:
            s += 1.0 if is_negative_event else 0
        if he:
            s += 1.0 if is_positive_event else 0

    return s


def has_surgery_word(text):
    return bool(re.search(r'手术|开刀|切除', text))


# ============================================================
# Interaction factors: ten-god combos amplify or suppress scores
# ============================================================
SHEN_INTERACTIONS = {
    # Dangerous combos (conservative weights)
    ("七杀", "伤官"): {"灾劫": 2.0, "健康": 2.0, "官非": 2.0, "婚姻": 0.5},
    ("七杀", "劫财"): {"灾劫": 1.5, "健康": 1.5, "财运": -1.5},
    ("伤官", "正官"): {"婚姻": 2.5, "事业": -1.5},  # 伤官见官
    ("伤官", "七杀"): {"健康": 2.0, "灾劫": 2.0},
    ("伤官", "劫财"): {"财运": -1.5, "健康": 0.5},
    ("比肩", "劫财"): {"财运": -2.0, "婚姻": -1.5},
    # Beneficial combos
    ("正官", "正印"): {"事业": 2.0, "学业": 2.0, "婚姻": 1.0},
    ("七杀", "正印"): {"事业": 2.0, "学业": 1.0},
    ("食神", "正财"): {"财运": 2.5, "事业": 1.0},
    ("食神", "偏财"): {"财运": 2.0, "事业": 0.5},
    ("伤官", "正财"): {"财运": 1.5, "事业": 1.0},
    ("伤官", "偏财"): {"财运": 1.5},
    ("正财", "正官"): {"事业": 1.5, "婚姻": 1.0, "财运": 1.0},
    ("正官", "食神"): {"事业": 0.5, "婚姻": 0.5},
    ("偏印", "七杀"): {"学业": 1.5, "事业": 1.0},
    ("正印", "食神"): {"学业": 1.0, "健康": 0.5},
}


def get_interaction_bonus(all_ss, cat, gender="男"):
    """Calculate bonus/penalty from ten-god interactions."""
    bonus = 0.0
    ss_list = list(all_ss) if isinstance(all_ss, set) else all_ss
    if not isinstance(ss_list, list):
        ss_list = list(ss_list)

    for pair, cat_bonuses in SHEN_INTERACTIONS.items():
        if pair[0] in ss_list and pair[1] in ss_list:
            # Direct match
            bonus += cat_bonuses.get(cat, 0)
            # Gender-specific adjustments
            if cat == "婚姻" and "伤官" in pair and "正官" in pair and gender in ("女", "F", "female"):
                bonus += 2.0  # 女命伤官见官 = 克夫
            if cat == "婚姻" and "比肩" in pair and "劫财" in pair and gender in ("男", "M", "male"):
                bonus += 1.5  # 男命比劫夺财 = 克妻
            if cat == "健康" and "七杀" in pair and "伤官" in pair:
                bonus += 1.5  # Extra: surgery/accident
            if cat == "财运" and "比肩" in pair and "劫财" in pair:
                if "财" in str(ss_list):  # has wealth star present too
                    bonus -= 2.0  # 比劫夺财更严重

    return bonus


# ============================================================
# Ziwei star-based scoring helpers
# ============================================================
def get_ziwei_marriage_signal(ziwei_data, option_text):
    """Score marriage options based on Ziwei 夫妻宫 star type."""
    s = 0.0
    from tools.tool_integration import ZIWEI_STAR_MARRIAGE_TYPE
    couple_stars = ziwei_data.get("zw_夫妻", [])
    if not couple_stars:
        return 0.0

    types = [ZIWEI_STAR_MARRIAGE_TYPE.get(st, "stable") for st in couple_stars]
    has_volatile = "volatile" in types
    has_stable = "stable" in types
    has_romantic = "romantic" in types

    divorce_kw = re.search(r'离|分居|分手|外遇|情人|出轨|亡|死|早亡|去世', option_text)
    marriage_kw = re.search(r'结婚|已婚|美满|恩爱|稳定|和睦|白头', option_text)
    single_kw = re.search(r'单身|未婚|未嫁|一生未|独身|清心寡欲', option_text)

    # Only apply ziwei signal as supplement, not override八字
    #天机 in夫妻宫 = emotionally variable, not necessarily divorce
    if has_volatile:
        if divorce_kw:
            s += 1.0 if "天机" in couple_stars else 2.0  #天机 weaker divorce signal
        else:
            s -= 0.3
        s += 1.5 if re.search(r'亡|死|早亡|去世', option_text) else 0
        if marriage_kw and not divorce_kw:
            s -= 0.8 if "天机" in couple_stars else 1.5
    if has_stable:
        s += 2.0 if marriage_kw else -0.5
        s -= 1.0 if divorce_kw else 0
    if has_romantic:
        s += 1.0 if re.search(r'外遇|情人|桃花|多情', option_text) else 0
        s += 0.5 if re.search(r'二婚|再婚|多婚', option_text) else 0

    # Special: 破军+廉贞 in 夫妻宫 = extreme volatility (death/divorce)
    if set(couple_stars) & {"破军", "廉贞"} and has_volatile:
        death_kw = re.search(r'亡|死|早亡|去世', option_text)
        if death_kw:
            s += 2.5
        severe_divorce = re.search(r'离婚|已离|离异', option_text)
        if severe_divorce:
            s += 1.5

    return s


def get_ziwei_health_signal(ziwei_data, option_text):
    """Score health options based on Ziwei 疾厄宫 stars."""
    from tools.tool_integration import ZIWEI_HEALTH_ORGANS
    jie_stars = ziwei_data.get("zw_疾厄", [])
    if not jie_stars:
        return 0.0

    s = 0.0
    for star in jie_stars:
        organs = ZIWEI_HEALTH_ORGANS.get(star, [])
        for organ in organs:
            if organ in option_text:
                s += 2.0

    # 疾厄宫破军 = kidney/urinary problems
    if "破军" in jie_stars:
        if re.search(r'肾|泌尿|膀胱|生殖', option_text):
            s += 1.5
    # 贪狼 in 疾厄 = liver/gallbladder
    if "贪狼" in jie_stars:
        if re.search(r'肝|胆', option_text):
            s += 1.5

    return s


def score_year_option(year, chart, cat, q_text, opt_text):
    """For 'which year' questions: evaluate each candidate year."""
    yeval = eval_year(chart, year)
    s = score_option_v2(opt_text, chart, cat, q_text, yeval)
    return s, yeval


def predict(q, chart_cache, qimen_data=None):
    bi = q.get("birth_info", {})
    cat = q.get("category", "运势")
    options = q.get("options", [])
    q_text = q.get("question", "")

    cid = q.get("case_id", "")
    if cid not in chart_cache:
        chart_cache[cid] = compute_chart(bi)
    chart = chart_cache[cid]

    if not chart:
        return random.choice([o["letter"] for o in options]) if options else "A"

    td = _get_tool_data(bi)

    tg = chart.get("十神", {})
    q_year = extract_question_year(q_text)
    opt_years = extract_years_from_options(options)
    is_year_selection = len(opt_years) >= 2 and all(o.get("letter") in opt_years for o in options)

    # Pre-analyze question intent for year-selection questions
    q_context = {}
    if is_year_selection:
        q_lower = q_text.lower()
        q_context["破产"] = bool(re.search(r'破产|赌.*破产|因.*赌.*破产', q_text))
        q_context["手术"] = bool(re.search(r'手术|开刀|切除|癌|肿瘤|硬块', q_text))
        q_context["意外"] = bool(re.search(r'意外|撞车|车祸|交通.*故|骨折|受伤', q_text))
        q_context["去世"] = bool(re.search(r'去世|逝世|死亡|过世', q_text))
        q_context["结婚"] = bool(re.search(r'结婚|成婚|嫁|娶|认识.*妻|认识.*夫', q_text))
        q_context["父"] = "父" in q_text
        q_context["母"] = "母" in q_text

    scores = {}
    for o in options:
        letter = o["letter"]
        text = o.get("text", "")

        if is_year_selection and letter in opt_years:
            yr = opt_years[letter]
            yeval = eval_year(chart, yr)
            scores[letter] = score_option_v2(text, chart, cat, q_text, yeval)

            # Qimen scoring for year-specific options
            if qimen_data:
                scores[letter] += score_qimen_for_option(qimen_data, yr, text, cat)

            yr_gz = year_ganzhi(yr)
            yr_gan = yr_gz[0]
            yr_gan_ss = shen(chart["日主"], yr_gan)
            target_ss_map = {
                "婚姻": ["正财", "偏财"] if chart.get("gender") in ("男", "M", "male") else ["正官", "七杀"],
                "子女": ["食神", "伤官"],
                "财运": ["正财", "偏财"],
                "健康": ["七杀", "伤官"],
                "事业": ["正官", "七杀", "正印"],
                "学业": ["正印", "偏印"],
                "家庭": ["正印", "偏印", "偏财"],
            }
            target = target_ss_map.get(cat, [])
            if yr_gan_ss in target:
                scores[letter] += 3.0
            yr_zhi = yr_gz[1]
            yr_zhi_cang = ZHI_CANG_GAN.get(yr_zhi, [])
            for cg in yr_zhi_cang:
                if shen(chart["日主"], cg) in target:
                    scores[letter] += 1.5

            if yeval.get("he"):
                if cat == "婚姻":
                    scores[letter] += 2.0
                if cat == "家庭":
                    scores[letter] += 1.5
                if cat == "健康":
                    scores[letter] -= 1.0
            if yeval.get("chong"):
                if cat in ("健康", "灾劫"):
                    scores[letter] += 1.5
                if cat == "家庭":
                    scores[letter] += 1.5
                if cat == "婚姻":
                    scores[letter] -= 1.0

            du = yeval.get("du", {})
            ln = yeval.get("ln", {})
            if yeval["ln"].get("is_yong"):
                if cat in ("财运", "事业", "学业", "家庭", "婚姻"):
                    if not (q_context.get("破产") or q_context.get("去世")):
                        scores[letter] += 2.5
                if cat in ("健康", "灾劫"):
                    scores[letter] -= 1.5
            if yeval["ln"].get("is_ji"):
                if cat in ("健康", "灾劫", "官非"):
                    scores[letter] += 2.0
                if cat == "家庭":
                    scores[letter] += 1.5
                    if q_context.get("破产") or q_context.get("去世"):
                        scores[letter] += 2.0
                if cat in ("财运", "事业"):
                    scores[letter] -= 1.0

            if du:
                du_yong = du.get("is_yong", False)
                du_ji = du.get("is_ji", False)
                if du_yong and ln.get("is_yong"):
                    if cat in ("事业", "财运", "学业"):
                        scores[letter] += 1.5
                if du_ji and ln.get("is_ji"):
                    if cat in ("健康", "灾劫"):
                        scores[letter] += 2.0

                # Question-aware year analysis
                if q_context.get("破产") and cat == "家庭":
                    # Check if this year's elements克偏财(父亲星, universally偏财)
                    father_ss = "偏财"
                    if yr_gan_ss == "劫财" or yr_gan_ss == "比肩":
                        scores[letter] += 3.0  # 劫财/比肩=克财/破产
                    for cg_ss in [shen(chart["日主"], c) for c in yr_zhi_cang]:
                        if cg_ss in ("劫财", "比肩"):
                            scores[letter] += 1.5
                    if du_ji and ln.get("is_ji"):
                        scores[letter] += 2.0  # doubly bad =破产
                    if yeval.get("chong") and du_ji:
                        scores[letter] += 2.0
                    # Check害/破 on father星偏财 location
                    father_zhi = None
                    for k, v in tg.items():
                        if father_ss in v and "时" in k:
                            father_zhi = chart["四柱"].get("时柱", "  ")[1:2] if len(chart.get("四柱", {}).get("时柱", "")) >= 2 else None
                        elif father_ss in v and "月" in k:
                            father_zhi = chart["四柱"].get("月柱", "  ")[1:2] if len(chart.get("四柱", {}).get("月柱", "")) >= 2 else None
                    if father_zhi:
                        # Check if流年害/破 father_zhi
                        yr_zhi = yr_gz[1]
                        fn_check = _check_chong_he(father_zhi, yr_zhi)
                        if "六害" in fn_check or "六破" in fn_check:
                            scores[letter] += 3.0  #流年害/破父星
                        if "六冲" in fn_check:
                            scores[letter] += 2.5
                        # Check if大运害/破 father_zhi
                        if du:
                            du_zhi = du.get("zhi", "")
                            if du_zhi:
                                du_check = _check_chong_he(father_zhi, du_zhi)
                                if "六害" in du_check or "六破" in du_check:
                                    scores[letter] += 2.0  #大运害/破父星
                                if "六冲" in du_check:
                                    scores[letter] += 1.5

                if q_context.get("手术") and cat in ("健康", "灾劫"):
                    # Surgery needs:七杀/伤官 (surgery signal) +大运印星 (healing)
                    has_surgery_signal = (yr_gan_ss in ("七杀", "伤官") or
                                          any(shen(chart["日主"], c) in ("七杀", "伤官") for c in yr_zhi_cang))
                    du_has_yin = False
                    du_yin_strength = 0
                    du_yong_bonus = 0
                    du_is_pure_yin = False
                    if du:
                        du_gan_ss = du.get("gan_ss", "")
                        du_zhi_ss = [shen(chart["日主"], c) for c in du.get("zhi_cang", [])]
                        du_has_yin = "正印" in du_zhi_ss or "偏印" in du_zhi_ss or du_gan_ss in ("正印", "偏印")
                        if du_gan_ss in ("正印", "偏印"):
                            du_yin_strength += 2
                        du_yin_strength += sum(1 for s in du_zhi_ss if s in ("正印", "偏印"))
                        if du_yong:
                            du_yong_bonus += 1.5
                        if du_gan_ss in ("正印", "偏印") and all(s in ("正印", "偏印") for s in du_zhi_ss):
                            du_is_pure_yin = True
                            du_yong_bonus += 3.0
                    if has_surgery_signal:
                        scores[letter] += 2.0
                        if du_has_yin:
                            scores[letter] += 2.0 + du_yin_strength * 1.5
                        if du_yong:
                            scores[letter] += du_yong_bonus
                        if du_is_pure_yin:
                            scores[letter] += 2.0
                    # For surgery context:印星大运 should outweigh七杀+伤官 interaction
                    # Pure印大运完全化解七杀伤官→no penalty needed
                    # Non-pure印 only partially化解→cancel most interaction bonus
                    if du_has_yin and not du_is_pure_yin:
                        all_ss_set = yeval.get("all_ss", set())
                        if "七杀" in all_ss_set:
                            scores[letter] -= 3.5  #印星化解七杀带来的凶
                        if "伤官" in all_ss_set:
                            scores[letter] -= 1.5  #印星化解伤官
                        if "七杀" in all_ss_set and "伤官" in all_ss_set:
                            scores[letter] -= 2.5  #额外:印星化解七杀伤官组合

                if q_context.get("意外") and cat in ("健康", "灾劫"):
                    has_injury_signal = (yr_gan_ss in ("七杀", "伤官") or
                                         any(shen(chart["日主"], c) in ("七杀", "伤官") for c in yr_zhi_cang))
                    if has_injury_signal:
                        scores[letter] += 2.5
                    if yeval.get("chong"):
                        scores[letter] += 2.5  #冲=意外/外伤
                    #七杀+劫财 = violent accident
                    all_ss_set = set([yr_gan_ss] + [shen(chart["日主"], c) for c in yr_zhi_cang])
                    if "七杀" in all_ss_set and "劫财" in all_ss_set:
                        scores[letter] += 2.0

                if q_context.get("去世") and cat == "家庭":
                    if du_ji and yeval.get("chong"):
                        scores[letter] += 3.0
                    if du_ji and ln.get("is_ji"):
                        scores[letter] += 2.0

            all_ss = yeval.get("all_ss", set())
            # NOTE: get_interaction_bonus is already called inside score_option_v2,
            # DO NOT double-count it here for year-selection or single-year questions.
            # For q_context surgery, suppress七杀+伤官 interaction in favor of印星
            if not (q_context.get("手术") and du and du.get("gan_ss", "") not in ("正印", "偏印")):
                if not is_year_selection and not q_year:
                    scores[letter] += get_interaction_bonus(all_ss, cat, chart.get("gender", "男"))

            # TCM health bonus for year selections
            if cat in ("健康", "灾劫"):
                scores[letter] += score_tcm_health(chart, text)

        elif q_year:
            if cat in ("健康", "灾劫", "婚姻", "家庭"):
                yeval = eval_year(chart, q_year)
                scores[letter] = score_option_v2(text, chart, cat, q_text, yeval)
                if cat == "婚姻":
                    scores[letter] += _score_chart_level(text, chart, cat, q_year=q_year, ziwei_data=td)
            else:
                scores[letter] = _score_chart_level(text, chart, cat, q_year=q_year, ziwei_data=td)

            # Qimen scoring for focused year
            if qimen_data:
                scores[letter] += score_qimen_for_option(qimen_data, q_year, text, cat)
            # Note: TCM scoring for year questions is already in _score_chart_level
        else:
            scores[letter] = _score_chart_level(text, chart, cat, ziwei_data=td)
            if cat in ("健康",):
                scores[letter] += score_tcm_health(chart, text)

    if not scores:
        return random.choice([o["letter"] for o in options])

    mx = max(scores.values())
    if mx <= 0.01 and len(set(round(v, 2) for v in scores.values())) == 1:
        return _smart_tiebreak(options, chart, cat)

    return max(scores, key=scores.get)


def _smart_tiebreak(options, chart, cat):
    """Deterministic tiebreaker based on chart properties."""
    if not chart:
        return options[0]["letter"]

    day_wx = chart["日主五行"]
    strong = chart["日主强弱"] == "身强"
    wx = chart["五行力量"]
    tg = chart["十神"]
    tg_set = set(tg.values())
    gender = chart.get("gender", "男")

    best_letter = options[0]["letter"]
    best_score = -999

    for o in options:
        text = o.get("text", "")
        s = 0.0

        st = max(wx, key=wx.get)
        wk = min(wx, key=wx.get)

        wx_keywords = {
            "木": ["仁", "直", "木", "长", "条", "东方"],
            "火": ["礼", "明", "火", "热", "红", "南方"],
            "土": ["信", "厚", "土", "稳", "黄", "中央"],
            "金": ["义", "刚", "金", "利", "白", "西方"],
            "水": ["智", "柔", "水", "流", "黑", "北方"],
        }
        for kw in wx_keywords.get(day_wx, []):
            if kw in text: s += 1.0
        for kw in wx_keywords.get(st, []):
            if kw in text: s += 0.5

        if "正官" in tg_set and ("规" in text or "正" in text or "稳" in text): s += 0.5
        if "七杀" in tg_set and ("武" in text or "军" in text or "强" in text): s += 0.5
        if "正印" in tg_set and ("文" in text or "学" in text or "善" in text): s += 0.5
        if "偏印" in tg_set and ("技" in text or "异" in text): s += 0.5
        if "正财" in tg_set and ("勤" in text or "务" in text): s += 0.5
        if "偏财" in tg_set and ("商" in text or "交" in text): s += 0.5
        if "食神" in tg_set and ("和" in text or "乐" in text): s += 0.5
        if "伤官" in tg_set and ("傲" in text or "创" in text): s += 0.5
        if "比肩" in tg_set and ("独" in text or "主" in text): s += 0.5
        if "劫财" in tg_set and ("冲" in text or "赌" in text): s += 0.5

        # Special tiebreaker: very weak spouse star → favor single
        if cat == "婚姻":
            day2spouse = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
            if gender in ("男", "M", "male"):
                sp_key = day2spouse.get(day_wx, "金")
                if wx.get(sp_key, 5) < 1.0:
                    if "独身" in text or "清心寡欲" in text or "单身" in text:
                        s += 5.0
                    if "已婚" in text:
                        s -= 3.0
            elif gender in ("女", "F", "female"):
                f_guan = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}
                sp_key = f_guan.get(day_wx, "水")
                if wx.get(sp_key, 5) < 1.0:
                    if "独身" in text or "单身" in text or "未嫁" in text:
                        s += 4.0
                    if "已婚" in text:
                        s -= 3.0

        if s > best_score:
            best_score = s
            best_letter = o["letter"]

    if best_score < 0.01:
        return random.choice([o["letter"] for o in options])

    return best_letter


def _score_chart_level(text, chart, cat, q_year=None, ziwei_data=None):
    """Chart-level scoring without year context. For personality/description questions."""
    s = 0.0
    day_gan = chart["日主"]
    day_wx = chart["日主五行"]
    strong = chart["日主强弱"] == "身强"
    wx = chart["五行力量"]
    tg = chart["十神"]
    yong = chart["喜用神"]
    ji = chart["忌神"]

    if cat == "性格":
        dp = PERSONALITY_MAP.get(day_gan, {})
        for trait in dp.get("pos", []):
            if trait in text: s += 2.5
        for trait in dp.get("neg", []):
            if trait in text: s += 2.0

        st = max(wx, key=wx.get)
        wk = min(wx, key=wx.get)
        for t in WX_PERSONALITY_EXTRA.get(st + "旺", []):
            if t in text: s += 1.5
        for t in WX_PERSONALITY_EXTRA.get(wk + "弱", []):
            if t in text: s += 1.0

        god_traits = {
            "正官": ["守规矩", "传统", "保守", "正直", "稳重"],
            "七杀": ["好胜", "急躁", "果断", "霸道", "不服输", "勇敢"],
            "正印": ["善良", "仁慈", "文静", "爱学习", "被动", "包容"],
            "偏印": ["多疑", "敏感", "特立独行", "多才"],
            "正财": ["勤恳", "务实", "节俭", "守本分"],
            "偏财": ["大方", "好交际", "重享受"],
            "食神": ["温和", "乐观", "善良", "有口福"],
            "伤官": ["傲气", "叛逆", "口才好", "任性", "不服输"],
            "比肩": ["自尊心强", "独立", "不服输"],
            "劫财": ["冲动", "好赌", "好胜"],
        }
        dg = {}
        for pos, god in tg.items():
            dg[god] = dg.get(god, 0) + 1
        for god, cnt in sorted(dg.items(), key=lambda x: -x[1])[:3]:
            for t in god_traits.get(god, []):
                if t in text: s += 1.2 * min(cnt, 2)

        if not strong:
            if "耳根子软" in text or "不善拒绝" in text: s += 2.0
            if "付出" in text and ("压榨" in text or "欺负" in text): s += 2.0
            if "内向" in text or "沉默" in text: s += 1.0
            if "被动" in text: s += 1.0
            if "胆小" in text or "怕" in text: s += 1.0
            if "忍" in text or "忍耐" in text: s += 0.5
        if strong:
            if "强势" in text or "固执" in text or "有主见" in text: s += 1.5
            if "外向" in text or "胆大" in text: s += 1.0
            if "主动" in text: s += 1.0
            if "不服" in text or "倔强" in text: s += 1.0

        if "小心" in text or "谨慎" in text:
            if day_wx in ("土", "金"): s += 1.5
        if "急" in text or "暴躁" in text:
            if day_wx == "火": s += 1.5
        if "啰嗦" in text or "苦口婆心" in text:
            if "正印" in set(tg.values()) and day_wx == "土": s += 1.5
        if "善交际" in text or "交际能手" in text:
            if day_wx == "水" or "偏财" in set(tg.values()): s += 1.5

    elif cat == "事业":
        tg_set = set(tg.values())
        for ss_name, profs in PROFESSION_TENGOD.items():
            if ss_name in tg_set:
                for p in profs:
                    if p in text: s += 2.0
        if "主妇" in text or "家庭主妇" in text:
            if chart.get("gender") in ("女", "F", "female") and not strong:
                s += 1.5
        if strong:
            if "管理" in text or "老板" in text or "领导" in text: s += 1.5
            if "生意" in text or "创业" in text: s += 1.0
        if not strong:
            if "文员" in text or "职员" in text or "文职" in text: s += 1.0
            if "秘书" in text: s += 1.0
        if "公关" in text:
            if "偏财" in tg_set or "伤官" in tg_set: s += 1.0

        # More career matching
        if "保险" in text:
            if "正官" in tg_set: s += 1.5
        if "建筑" in text:
            if day_wx in ("土", "金") or "偏财" in tg_set: s += 1.5
        if "军人" in text or "警察" in text or "军人" in text:
            if "七杀" in tg_set: s += 1.5
        if "老师" in text or "教师" in text:
            if "正印" in tg_set: s += 1.5
        if "工厂" in text or "工人" in text:
            if "比肩" in tg_set or "劫财" in tg_set or day_wx in ("金", "土"): s += 1.0
        if "运输" in text or "司机" in text or "巴士" in text or "的士" in text:
            if "七杀" in tg_set or day_wx in ("金", "水"): s += 1.0
        if "自由职业" in text or "自由" in text:
            if "伤官" in tg_set or "偏印" in tg_set: s += 1.0
        if "公司" in text and ("职员" in text or "员工" in text):
            if "正官" in tg_set and not strong: s += 1.0
        if "稳定" in text and ("工作" in text or "事业" in text):
            if "正官" in tg_set or "正印" in tg_set: s += 1.0
        if "做生意" in text or "商人" in text or "经营" in text:
            if "偏财" in tg_set or "食神" in tg_set: s += 1.0
        if "护士" in text or "医疗" in text:
            if "正印" in tg_set or "食神" in tg_set: s += 1.0
        if "工厂" in text and "开" in text:
            if "偏财" in tg_set and strong: s += 1.5
        if "有兄弟" in text or "独子" in text:
            if "比肩" not in tg_set and "劫财" not in tg_set:
                if "独" in text: s += 1.0
        if "修理" in text or "维修" in text:
            if "偏印" in tg_set or "伤官" in tg_set: s += 1.0

        # Career level/position
        if "高管" in text or "总监" in text or "经理" in text:
            if strong and "正官" in tg_set: s += 1.5
        if "普通" in text or "基层" in text:
            if not strong: s += 1.0
        if "创业" in text and ("成功" in text or "失败" in text):
            if "偏财" in tg_set and strong: s += 1.0
            if "劫财" in tg_set and not strong: s -= 0.5

        if q_year:
            has_career_pos = bool(re.search(r'升|晋升|提升|创业成功|加薪|提拔|融资|当上|转正', text))
            has_career_neg = bool(re.search(r'失业|倒闭|被辞|失败|降|裁员|破产', text))
            yeval = eval_year(chart, q_year)
            all_ss = yeval["all_ss"]
            is_fav = yeval["ln"].get("is_yong") or yeval.get("du", {}).get("is_yong", False)
            is_unfav = yeval["ln"].get("is_ji") or yeval.get("du", {}).get("is_ji", False)
            if "正官" in all_ss or "七杀" in all_ss:
                if has_career_pos: s += 2.5
            if "正印" in all_ss:
                if has_career_pos: s += 1.0
            if "食神" in all_ss or "伤官" in all_ss:
                if "创业" in text or "技术" in text: s += 1.5
            if is_fav:
                if has_career_pos: s += 2.0
                if has_career_neg: s -= 1.0
            if is_unfav:
                if has_career_neg: s += 1.5
            if yeval.get("chong"):
                if has_career_neg: s += 1.0

    elif cat == "外貌":
        looks = {"木": ["修长", "高", "瘦"], "火": ["红润", "尖"],
                 "土": ["厚", "方", "圆", "胖", "矮", "肥"],
                 "金": ["白", "方", "眉目"], "水": ["黑", "圆", "胖", "丰满"]}
        for t in looks.get(day_wx, []):
            if t in text: s += 2.0
        st = max(wx, key=wx.get)
        for t in looks.get(st, []):
            if t in text: s += 1.5
        if strong and ("肥" in text or "壮" in text): s += 0.5
        if not strong and ("瘦" in text or "瘦削" in text): s += 0.5

    elif cat == "财运":
        has_w = "正财" in set(tg.values()) or "偏财" in set(tg.values())
        has_r = "比肩" in set(tg.values()) or "劫财" in set(tg.values())
        if has_w and not has_r:
            if "理" in text and "财" in text: s += 1.5
            if "积蓄" in text or "购置" in text: s += 1.0
        if has_r:
            if "欠" in text or "债务" in text: s += 1.5
            if "乱花" in text or "投机" in text: s += 1.0
        if not strong:
            if "代为管理" in text or "月光" in text: s += 1.5

        day2cai = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
        wealth_score = wx.get(day2cai.get(day_wx, "金"), 0) + wx.get("土", 0)
        if wealth_score > 40:
            if "大富" in text or "富有" in text or "富裕" in text: s += 2.0
            if "中产" in text: s += 1.0
            if "贫穷" in text or "贫困" in text or "贫穷" in text or "拮据" in text: s -= 1.5
        elif wealth_score < 15:
            if "贫穷" in text or "贫困" in text or "贫穷" in text or "拮据" in text or "清贫" in text: s += 2.0
            if "大富" in text or "富有" in text or "富裕" in text: s -= 1.5

        if has_w and strong:
            if "盈" in text or "盈利" in text or "富" in text: s += 1.5
            if "贫穷" in text or "贫" in text or "穷" in text: s -= 1.0
        if has_r and not has_w:
            if "负债" in text or "破" in text: s += 1.0

    elif cat == "婚姻":
        gender = chart.get("gender", "男")
        spouse_gods = ["正财", "偏财"] if gender in ("男", "M", "male") else ["正官", "七杀"]
        tg_set = set(tg.values())
        has_robber = "比肩" in tg_set or "劫财" in tg_set
        has_shang = "伤官" in tg_set

        # --- Compute spouse star actual strength (not just presence) ---
        day_wx_to_spouse_wx = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
        spouse_wx_key = day_wx_to_spouse_wx.get(day_wx, "金")
        spouse_wx_val = wx.get(spouse_wx_key, 10)
        spouse_positions = [k for k, v in tg.items() if v in spouse_gods]
        spouse_has_root = len(spouse_positions) >= 2 or any("天干" in p for p in spouse_positions)
        spouse_is_strong = spouse_wx_val > 1.2  # reasonable threshold
        spouse_is_viable = spouse_has_root and spouse_is_strong
        # has_spouse means spouse star is genuinely present, not just a whisper in藏干
        has_spouse = any(g in tg_set for g in spouse_gods)

        # Ziwei marriage signal (NEW)
        if ziwei_data:
            s += get_ziwei_marriage_signal(ziwei_data, text)

        if "美满" in text or "恩爱" in text:
            if strong and spouse_is_viable:
                s += 3.0  # boosted: real spouse star + strong = good marriage
            elif strong and has_spouse:
                s += 1.0
            else:
                s -= 0.5
        if "稳定" in text and "婚姻" in text:
            if spouse_is_viable and not has_robber:
                s += 2.5
            elif has_spouse:
                s += 1.0
        if "外遇" in text or "情人" in text:
            if has_robber or has_shang: s += 1.5
        if "离" in text or "分手" in text or "分居" in text:
            if has_robber: s += 1.5
            if has_shang and gender in ("女", "F", "female"): s += 1.5
            # Penalize divorce if spouse star is strong and喜用
            if spouse_is_viable and spouse_wx_key == yong:
                s -= 1.0
        if "单身" in text or "未婚" in text or "未结" in text:
            if not spouse_is_viable: s += 2.0
            elif not has_spouse: s += 1.0
            else: s -= 1.0

        # Special: very weak spouse star -> favor single/never married
        if not spouse_is_viable:
            if "单身" in text or "独身" in text or "清心寡欲" in text or "未嫁" in text:
                s += 4.0  # boosted
            if "已婚" in text or "结婚" in text:
                s -= 2.5  # harder to marry
        if spouse_is_viable:
            if "已婚" in text or "结婚" in text:
                s += 1.0
            if "单身" in text or "独身" in text or "清心寡欲" in text:
                s -= 1.0

        # Check pillar冲 affecting spouse palace
        spouse_zhi = chart.get("四柱", {}).get("日柱", "  ")[1:2] if len(chart.get("四柱", {}).get("日柱", "")) >= 2 else ""
        if spouse_zhi:
            for pillar_name, gz in chart.get("四柱", {}).items():
                if pillar_name == "日柱" or not gz or len(gz) < 2:
                    continue
                pz = gz[1]
                chong_res = _check_chong_he(spouse_zhi, pz)
                if "六冲" in chong_res:
                    if "离" in text or "婚" in text and ("不好" in text or "差" in text):
                        s += 2.0
                    if "美满" in text or "恩爱" in text:
                        s -= 1.5  # spouse palace冲 = unlikely to be美满
                if "六合" in chong_res or "三合" in chong_res:
                    if "美满" in text or "恩爱" in text or "稳定" in text:
                        s += 1.5
        if "同居" in text:
            s += 0.5
        if "已婚" in text or "结婚" in text:
            if strong and has_spouse: s += 1.5
        if "签字" in text and "婚" in text:
            if has_spouse: s += 1.5
        if "一婚" in text or "一次婚" in text or "第1" in text or "第一段" in text:
            if has_spouse and not has_robber: s += 1.0
        if "二婚" in text or "两婚" in text or "第2" in text or "第二" in text:
            if has_robber or (has_shang and gender in ("女", "F", "female")): s += 1.5
        if "多婚" in text or "三婚" in text or "第3" in text or "第三" in text:
            if has_robber and has_shang: s += 1.5
        if "出轨" in text:
            if has_robber or "偏财" in set(tg.values()): s += 1.5
        if "配偶" in text:
            if "赌" in text and "偏财" in set(tg.values()): s += 1.0
            if "普通" in text and not strong: s += 0.5
            if "高职位" in text or "事业有" in text:
                if "正官" in set(tg.values()) or "正印" in set(tg.values()): s += 1.0
            if "商" in text and "偏财" in set(tg.values()): s += 1.0
        if "认识" in text and ("妻" in text or "夫" in text):
            if has_spouse: s += 1.0
        if "稳定" in text and "婚" in text:
            if has_spouse and not has_robber: s += 1.0
        if "23" in text or "20" in text:
            if has_spouse and strong: s += 0.5
        if "33" in text or "30" in text:
            if not has_spouse or not strong: s += 0.5
        if "43" in text or "40" in text:
            if not has_spouse: s += 0.5
        if "没" in text and "结" in text:
            if not has_spouse: s += 1.0
            else: s -= 1.0

        spouse_wx = "金" if gender in ("男", "M", "male") else "水"
        if "商" in text and "人" in text:
            if "偏财" in set(tg.values()): s += 1.0

        if "奉子" in text:
            if "食神" in set(tg.values()) or "伤官" in set(tg.values()): s += 1.5
        if "冲喜" in text:
            s -= 0.5
        if "暴力" in text and "受" in text:
            if "七杀" in set(tg.values()): s += 1.5
        if "暴力" in text and ("命主" in text or "对待" in text):
            if "七杀" in set(tg.values()) or "伤官" in set(tg.values()): s += 1.0

        # Spouse characterization via十神 dominance (fix for ftb_0108)
        shi_shang_strength = wx.get("木", 0) if day_wx in ("火", "土") else (
            wx.get("火", 0) if day_wx in ("土", "金") else (
            wx.get("土", 0) if day_wx in ("金", "水") else (
            wx.get("金", 0) if day_wx in ("水", "木") else wx.get("水", 0))))
        shi_shang_count = sum(1 for v in tg.values() if v in ("食神", "伤官"))
        qi_sha_count = sum(1 for v in tg.values() if v == "七杀")
        cai_count = sum(1 for v in tg.values() if v in ("正财", "偏财"))
        # 食伤旺 = 配偶聪明有才 (key fix for ftb_0108)
        if shi_shang_strength > 2.0 or shi_shang_count >= 3:
            if "聪明" in text or "有才" in text or "才华" in text: s += 2.5
            if "帅" in text or "英俊" in text or "好看" in text: s += 1.5
            if "才" in text and ("气" in text or "华" in text): s += 2.0
            if "吵闹" in text or "吵架" in text or "争执" in text: s += 1.5
            if "修行" in text or "出家人" in text: s += 1.5
        # 七杀旺 = 配偶霸道/大男子主义/家暴
        if qi_sha_count >= 2:
            if "大男人" in text or "大男子" in text: s += 1.5
            if "暴力" in text or "家暴" in text or "打" in text: s += 1.5
            if "霸道" in text or "控制" in text: s += 1.0
        # 财旺 = 配偶有钱
        if cai_count >= 3:
            if "富" in text and ("代" in text or "有钱" in text or "多金" in text): s += 2.0
            if "多金" in text: s += 1.5
        # 财弱 = 配偶不富
        if cai_count <= 1:
            if "富二" in text or "富裕" in text: s -= 1.5
            if "多金" in text: s -= 1.0
        # 食神旺 + 女命 = 丈夫有艺术气质/聪明 (contradicts七杀霸道)
        if "食神" in tg_set and gender in ("女", "F", "female"):
            if "帅" in text or "聪明" in text or "有才" in text: s += 1.5

        if q_year:
            yeval = eval_year(chart, q_year)
            has_marriage_event = bool(re.search(r'结婚|签字|新婚|嫁|娶|成婚|完婚', text))
            has_divorce_event = bool(re.search(r'离婚|分居|分手|签字离婚', text))
            if any(g in yeval["all_ss"] for g in spouse_gods):
                if has_marriage_event: s += 2.5
                if has_divorce_event: s -= 1.0
            if yeval.get("he"):
                if has_marriage_event: s += 2.0
            if yeval["ln"].get("is_yong"):
                if has_marriage_event: s += 1.5
            if yeval["ln"].get("is_ji"):
                if has_divorce_event: s += 1.0

    elif cat == "家庭":
        pillars = chart["四柱"]
        tg_set = set(tg.values())
        has_qisha = "七杀" in tg_set
        has_zhengyin = "正印" in tg_set
        has_pianyin = "偏印" in tg_set
        has_piancai = "偏财" in tg_set
        has_zhengcai = "正财" in tg_set
        has_bijian = "比肩" in tg_set
        has_jiecai = "劫财" in tg_set

        # If question is about marriage+children within家庭 category, run sub-analysis
        if "婚姻" in text or "婚" in text or "嫁" in text or "娶" in text or "妻" in text:
            gender_fam = chart.get("gender", "男")
            fam_spouse_gods = ["正财", "偏财"] if gender_fam in ("男", "M", "male") else ["正官", "七杀"]
            fam_has_spouse = any(g in tg_set for g in fam_spouse_gods)
            fam_has_robber = "比肩" in tg_set or "劫财" in tg_set
            # Check spouse star strength
            fam_d2s = {"木":"土","火":"金","土":"水","金":"木","水":"火"}
            fam_sp_wx = fam_d2s.get(day_wx, "金")
            fam_sp_val = wx.get(fam_sp_wx, 0)
            fam_sp_strong = fam_sp_val > 1.2 and fam_has_spouse
            if "离" in text or "二婚" in text:
                if fam_has_robber and not fam_sp_strong: s += 2.0
                elif fam_has_robber: s += 1.0
                else: s -= 0.5
            if "已婚" in text or "结婚" in text:
                if fam_sp_strong: s += 2.5
                elif fam_has_spouse: s += 1.0
                else: s -= 1.0
            if "二婚" in text:
                if fam_has_robber and fam_sp_strong: s += 1.0
        if "孩子" in text or "子女" in text or "子嗣" in text or "流产" in text or "育有" in text:
            fam_has_child_ss = "食神" in tg_set or "伤官" in tg_set
            # Check子女宫 stars from ziwei
            has_child_stars = False
            if ziwei_data:
                child_stars = ziwei_data.get("zw_子女", [])
                has_child_stars = len(child_stars) > 0
                # 太阳+太阴 in子女宫 = at least 2 children
                if "太阳" in child_stars and "太阴" in child_stars:
                    s += 1.5  # strong children signal
                elif child_stars:
                    s += 0.5  # has children
            if "育有" in text:
                if has_child_stars: s += 1.0
                if fam_has_child_ss: s += 1.0
            if "没有子嗣" in text or "没孩子" in text or "没子女" in text:
                if has_child_stars or fam_has_child_ss:
                    s -= 2.5  # strongly penalize: there ARE children
                else:
                    s += 1.5
            if "孩子" in text and ("个" in text or "名" in text or "位" in text):
                if has_child_stars:
                    s += 1.0
            if "流产" in text:
                if "七杀" in tg_set: s += 1.0
                if has_child_stars: s += 0.5  # miscarriage implies pregnancy capability

        # Family wealth - use correct财星 element
        fam_day_wx_to_cai = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
        fam_cai_wx = fam_day_wx_to_cai.get(day_wx, "金")
        wealth_score = wx.get(fam_cai_wx, 0) + wx.get("土", 0)
        if wealth_score > 40 and strong:
            if "大富" in text or "富有" in text or "富裕" in text or "家境殷实" in text or "中产" in text: s += 2.0
            if "贫穷" in text or "贫困" in text or "清贫" in text or "拮据" in text or "穷" in text: s -= 1.5
        elif wealth_score < 15 or not strong:
            if "贫穷" in text or "贫困" in text or "清贫" in text or "拮据" in text or "穷" in text or "贫" in text: s += 2.0
            if "大富" in text or "富有" in text or "富裕" in text or "家境殷实" in text: s -= 1.5

        if "小康" in text or "小康之家" in text:
            if strong: s += 1.0
            elif not strong and not has_qisha: s += 0.5

        # Parent relationships
        if "父母离婚" in text or "离异" in text:
            if has_qisha or (not has_zhengyin and not has_piancai): s += 1.5
        if "跟" in text and "母" in text and ("生活" in text or "随" in text):
            if not has_piancai: s += 1.5
            if has_zhengyin: s += 1.0
        if "跟" in text and "父" in text and ("生活" in text or "随" in text):
            if has_piancai: s += 1.0
            if not has_zhengyin: s += 1.0
        if "跟祖父母" in text or "跟祖" in text:
            if not has_zhengyin and not has_piancai: s += 1.0

        # Interaction bonus for family
        s += get_interaction_bonus(tg_set, "家庭", chart.get("gender", "男"))

        if "不在父母身边" in text or "吃百家饭" in text or "孤儿" in text:
            if not strong and (has_qisha or has_pianyin): s += 1.5
        if "在孤儿" in text:
            if has_qisha and not has_zhengyin: s += 1.5

        # Parent death
        if "父母去世" in text or "父去世" in text or "母亲去世" in text or "母去世" in text or "父母去" in text:
            if has_qisha and not has_zhengyin: s += 1.5
        if "短寿" in text:
            if has_qisha: s += 1.0
        if "长寿" in text:
            if has_zhengyin: s += 1.0

        # Sibling relationships
        if "融洽" in text:
            if has_bijian and not has_jiecai: s += 1.0
            elif has_jiecai: s -= 0.5
        if "不融洽" in text or "关系不好" in text:
            if has_jiecai: s += 1.5

        # Family stability
        if "贫困" in text and "家庭" in text:
            if not strong and has_qisha: s += 1.5
        if "小康" in text:
            if strong and not has_qisha: s += 1.0
        if "中产" in text:
            if strong and (has_zhengcai or has_piancai): s += 1.0
        if "大富" in text or "豪门" in text:
            if strong and has_piancai and not has_jiecai: s += 1.5

        # Mother-related
        if "母亲" in text and ("住院" in text or "病" in text or "医院" in text):
            if not has_zhengyin or has_qisha: s += 1.0

        # Father-related
        if "父" in text and ("受伤" in text or "住院" in text or "医院" in text):
            if has_qisha or has_jiecai: s += 1.0
        if "父" in text and ("缺" in text or "不在" in text):
            if not has_piancai: s += 1.5

        # General family descriptions
        if "父母" in text and ("恩爱" in text or "和" in text):
            if has_zhengyin and has_zhengcai: s += 1.0
        if "家庭暴力" in text or "家暴" in text:
            if has_qisha: s += 1.5
        if "父母养" in text:
            if has_zhengyin: s += 0.5

        # Year-event family questions
        if q_year:
            yeval = eval_year(chart, q_year)
            has_neg = bool(re.search(r'去世|逝世|死亡|住院|病|医院|受伤|骨折|离婚|入狱|坐牢|破产|负债|意外|车祸|跌倒', text))
            has_pos = bool(re.search(r'出生|添丁|结婚|买房|和睦|团圆', text))
            if yeval.get("chong"):
                if has_neg: s += 2.0
            if yeval["ln"].get("is_ji"):
                if has_neg: s += 1.5
                if has_pos: s -= 1.0
            if yeval["ln"].get("is_yong"):
                if has_pos: s += 1.0
                if has_neg: s -= 0.5

    elif cat == "健康":
        for wx_name, organs in WX_ORGAN.items():
            for organ in organs:
                if organ in text:
                    weak_wx = min(wx, key=wx.get)
                    if wx_name == weak_wx: s += 2.0
                    strong_wx = max(wx, key=wx.get)
                    if wx_name == WUXING_KE.get(strong_wx, ""): s += 1.5

    elif cat == "学业":
        tg_set = set(tg.values())
        has_zhengyin = "正印" in tg_set
        has_pianyin = "偏印" in tg_set
        has_shangguan = "伤官" in tg_set
        has_shishen = "食神" in tg_set
        yin_strength = wx.get("木", 0) if day_wx == "火" else wx.get("水", 0) if day_wx == "木" else wx.get("火", 0) if day_wx == "土" else wx.get("土", 0) if day_wx == "金" else wx.get("金", 0)

        # Education level matching
        if has_zhengyin and yin_strength > 20:
            if "博士" in text: s += 2.0
            if "硕士" in text or "研究生" in text: s += 2.5
            if "大学" in text and ("毕业" in text or "学历" in text or "程度" in text): s += 2.0
            if "中学" in text or "中专" in text or "高中" in text: s -= 1.0
            if "小学" in text and ("毕业" in text or "未" in text): s -= 2.0
            if "文盲" in text: s -= 2.5
        elif has_zhengyin:
            if "大学" in text and ("毕业" in text or "学历" in text or "程度" in text): s += 1.5
            if "硕士" in text or "博士" in text: s += 0.5
            if "专科" in text or "中专" in text: s += 1.0
            if "中学" in text or "高中" in text: s += 0.5
            if "小学" in text: s -= 0.5
        elif has_pianyin:
            if "专科" in text or "中专" in text or "职业" in text: s += 2.0
            if "大学" in text and ("毕业" in text or "学历" in text): s += 1.0
            if "技术" in text or "技工" in text: s += 1.5
            if "中学" in text: s += 0.5
        else:
            if "小学" in text and ("毕业" in text or "未" in text): s += 1.5
            if "中学" in text or "中专" in text: s += 1.0
            if "文盲" in text: s += 1.5
            if "博士" in text or "硕士" in text: s -= 2.0
            if "大学" in text and ("毕业" in text or "学历" in text): s -= 1.0

        if has_shangguan and not has_zhengyin:
            if "小学" in text or "中学" in text or "辍学" in text: s += 1.0
            if "博士" in text or "硕士" in text: s -= 1.5

        if has_shishen and not has_zhengyin:
            if "专科" in text or "中专" in text: s += 1.0
            if "艺术" in text or "文学" in text: s += 1.0

        if strong and has_zhengyin:
            if "博士" in text or "硕士" in text or "研究生" in text: s += 1.0
        if not strong and not has_zhengyin:
            if "小学" in text or "文盲" in text: s += 1.0

        # Study field matching
        if "文学" in text or "文科" in text:
            if day_wx in ("木", "火"): s += 1.0
            if has_zhengyin: s += 0.5
        if "理学" in text or "理科" in text or "理工" in text:
            if day_wx in ("金", "水"): s += 1.0
        if "工学" in text or "工程" in text or "理工" in text:
            if day_wx in ("金", "土"): s += 1.0
            if has_pianyin: s += 0.5
        if "法学" in text:
            if "正官" in tg_set or "七杀" in tg_set: s += 1.0
        if "商" in text or "经济" in text or "金融" in text or "会计" in text or "财务" in text:
            if "正财" in tg_set or "偏财" in tg_set: s += 1.0
        if "医学" in text or "医科" in text or "中医" in text:
            if "七杀" in tg_set or has_pianyin: s += 1.0
        if "艺术" in text or "美术" in text or "音乐" in text or "设计" in text or "表演" in text or "绘画" in text or "舞蹈" in text:
            if has_shishen or has_shangguan: s += 1.0

        # Chart-level art / creativity signals for study field
        _is_art_field = any(kw in text for kw in ("艺术", "美术", "音乐", "设计", "表演", "绘画", "舞蹈"))
        if _is_art_field:
            # Ziwei: 天同在财帛/疾厄/官禄 = artistic talent
            if ziwei_data:
                art_palaces = [ziwei_data.get(p, []) for p in ("zw_财帛", "zw_疾厄", "zw_官禄")]
                if any("天同" in stars for stars in art_palaces):
                    s += 1.0
            # 日支伤官/食神(贴身): 伤官->视觉艺术(美术), 食神->表演艺术(音乐)
            ri_zhi = chart.get("四柱", {}).get("日柱", "")[1:] if len(chart.get("四柱", {}).get("日柱", "")) == 2 else ""
            if ri_zhi:
                ri_zhi_cang = ZHI_CANG_GAN.get(ri_zhi, [])
                for cg in ri_zhi_cang:
                    ss_type = shen(day_gan, cg)
                    if ss_type == "伤官" and any(kw in text for kw in ("美术", "绘画", "设计", "雕塑", "建筑")):
                        s += 0.5
                        break
                    if ss_type == "食神" and any(kw in text for kw in ("音乐", "表演", "舞蹈", "歌唱")):
                        s += 0.5
                        break

        # Year-event study questions
        if q_year:
            yeval = eval_year(chart, q_year)
            has_study_pos = bool(re.search(r'毕业|升学|考上|留学|录取|及格', text))
            has_study_neg = bool(re.search(r'辍学|落榜|没考|退学|退', text))
            if "正印" in yeval["all_ss"] or "偏印" in yeval["all_ss"]:
                if has_study_pos: s += 2.5
                if has_study_neg: s -= 1.0
            if yeval["ln"].get("is_yong"):
                if has_study_pos: s += 2.0
            if yeval["ln"].get("is_ji"):
                if has_study_neg: s += 1.5

    return s


def main():
    with open(os.path.join(os.path.dirname(__file__), "data", "data.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = data["questions"]

    print(f"Loaded {len(questions)} questions")
    chart_cache = {}
    correct = 0
    total = 0
    cat_stats = {}
    results = []
    t0 = time.time()

    for i, q in enumerate(questions):
        pred = predict(q, chart_cache)
        ans = q.get("answer", "")
        cat = q.get("category", "未知")
        ok = pred == ans
        correct += ok
        total += 1
        cat_stats.setdefault(cat, {"total": 0, "correct": 0})
        cat_stats[cat]["total"] += 1
        cat_stats[cat]["correct"] += ok
        results.append({"id": q["id"], "category": cat, "pred": pred, "ans": ans, "ok": ok})
        if (i + 1) % 40 == 0:
            print(f"  [{i+1}/{total}] acc={correct/total:.2%}")

    elapsed = time.time() - t0
    print(f"\n{'='*50}")
    print(f"Rules Engine v2 Results")
    print(f"{'='*50}")
    print(f"Overall: {correct}/{total} = {correct/total:.2%}")
    print(f"Time: {elapsed:.2f}s\n")
    for cat, st in sorted(cat_stats.items()):
        a = st["correct"] / st["total"] if st["total"] else 0
        print(f"  {cat:6s}: {a:6.2%} ({st['correct']}/{st['total']})")

    out = {"overall": correct / total, "correct": correct, "total": total,
           "time": elapsed, "cats": cat_stats, "results": results}
    p = os.path.join(os.path.dirname(__file__), "logs", "tools_rules_v2.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {p}")


if __name__ == "__main__":
    main()
