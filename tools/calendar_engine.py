from __future__ import annotations

import math
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
TIANGAN_IDX = {g: i for i, g in enumerate(TIANGAN)}
DIZHI_IDX = {z: i for i, z in enumerate(DIZHI)}

WUXING_GAN = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
WUXING_ZHI = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

YINYANG_GAN = {g: ("阳" if i % 2 == 0 else "阴") for i, g in enumerate(TIANGAN)}
YINYANG_ZHI = {z: ("阳" if i % 2 == 0 else "阴") for i, z in enumerate(DIZHI)}

WUXING_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WUXING_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
WUXING_BEING_SHENG = {v: k for k, v in WUXING_SHENG.items()}
WUXING_BEING_KE = {v: k for k, v in WUXING_KE.items()}

NAYIN_TABLE = {
    ("甲子", "乙丑"): "海中金", ("丙寅", "丁卯"): "炉中火",
    ("戊辰", "己巳"): "大林木", ("庚午", "辛未"): "路旁土",
    ("壬申", "癸酉"): "剑锋金", ("甲戌", "乙亥"): "山头火",
    ("丙子", "丁丑"): "涧下水", ("戊寅", "己卯"): "城头土",
    ("庚辰", "辛巳"): "白蜡金", ("壬午", "癸未"): "杨柳木",
    ("甲申", "乙酉"): "泉中水", ("丙戌", "丁亥"): "屋上土",
    ("戊子", "己丑"): "霹雳火", ("庚寅", "辛卯"): "松柏木",
    ("壬辰", "癸巳"): "长流水", ("甲午", "乙未"): "砂石金",
    ("丙申", "丁酉"): "山下火", ("戊戌", "己亥"): "平地木",
    ("庚子", "辛丑"): "壁上土", ("壬寅", "癸卯"): "金箔金",
    ("甲辰", "乙巳"): "覆灯火", ("丙午", "丁未"): "天河水",
    ("戊申", "己酉"): "大驿土", ("庚戌", "辛亥"): "钗钏金",
    ("壬子", "癸丑"): "桑柘木", ("甲寅", "乙卯"): "大溪水",
    ("丙辰", "丁巳"): "沙中土", ("戊午", "己未"): "天上火",
    ("庚申", "辛酉"): "石榴木", ("壬戌", "癸亥"): "大海水",
}

ZHI_CANG_GAN = {
    "子": ["癸"], "丑": ["己", "癸", "辛"], "寅": ["甲", "丙", "戊"],
    "卯": ["乙"], "辰": ["戊", "乙", "癸"], "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"], "未": ["己", "丁", "乙"], "申": ["庚", "壬", "戊"],
    "酉": ["辛"], "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"],
}

SHISHEN_MAP = {
    "比肩": "同我者", "劫财": "异我同五行",
    "食神": "我生者同性", "伤官": "我生者异性",
    "偏财": "我克者同性", "正财": "我克者异性",
    "七杀": "克我者同性", "正官": "克我者异性",
    "偏印": "生我者同性", "正印": "生我者异性",
}

CHANGSHENG_12 = [
    "长生", "沐浴", "冠带", "临官", "帝旺", "衰",
    "病", "死", "墓", "绝", "胎", "养",
]

CHANGSHENG_POS = {
    "木": {"甲": 0, "乙": 6, "丙": 10, "丁": 4, "戊": 0, "己": 6, "庚": 8, "辛": 2, "壬": 8, "癸": 2},
    "火": {"甲": 10, "乙": 4, "丙": 0, "丁": 6, "戊": 2, "己": 8, "庚": 6, "辛": 0, "壬": 4, "癸": 10},
    "土": {"甲": 0, "乙": 6, "丙": 2, "丁": 8, "戊": 0, "己": 6, "庚": 8, "辛": 2, "壬": 8, "癸": 2},
    "金": {"甲": 8, "乙": 2, "丙": 6, "丁": 0, "戊": 8, "己": 2, "庚": 0, "辛": 6, "壬": 2, "癸": 8},
    "水": {"甲": 8, "乙": 2, "丙": 4, "丁": 10, "戊": 8, "己": 2, "庚": 2, "辛": 8, "壬": 0, "癸": 6},
}

LUNAR_MONTH_DAYS = {
    1900: [0, 29, 30, 29, 29, 30, 29, 30, 29, 30, 29, 30, 29],
    1901: [0, 30, 29, 30, 29, 30, 29, 29, 30, 29, 30, 29, 30],
    1902: [0, 29, 30, 29, 30, 29, 29, 30, 29, 30, 29, 30, 29],
    1903: [0, 30, 29, 30, 29, 30, 29, 29, 30, 29, 30, 29, 30],
    1904: [0, 29, 30, 29, 30, 30, 29, 29, 30, 29, 30, 29, 29],
    1905: [0, 30, 29, 30, 29, 30, 30, 29, 29, 30, 29, 29, 30],
    1906: [0, 29, 30, 29, 29, 30, 30, 29, 30, 29, 29, 30, 29],
    1907: [0, 30, 29, 30, 29, 29, 30, 29, 30, 29, 30, 29, 30],
    1908: [0, 29, 30, 29, 30, 29, 29, 30, 29, 30, 29, 30, 29],
    1909: [0, 30, 29, 30, 29, 29, 30, 29, 30, 29, 30, 29, 30],
    1910: [0, 29, 30, 29, 30, 29, 29, 30, 29, 30, 29, 30, 29],
}

LUNAR_LEAP_MONTHS = {1900: 8, 1903: 5, 1906: 4, 1909: 2, 1911: 6,
                     1914: 5, 1917: 2, 1920: 7, 1922: 5, 1925: 4,
                     1928: 2, 1930: 6, 1933: 5, 1936: 3, 1938: 7,
                     1941: 6, 1944: 4, 1947: 2, 1949: 7, 1952: 5,
                     1955: 3, 1957: 8, 1960: 6, 1963: 4, 1966: 3,
                     1968: 7, 1971: 5, 1974: 4, 1976: 8, 1979: 6,
                     1982: 4, 1984: 10, 1987: 6, 1990: 5, 1993: 3,
                     1995: 8, 1998: 5, 2001: 4, 2004: 2, 2006: 7,
                     2009: 5, 2012: 4, 2014: 9, 2017: 6, 2020: 4,
                     2023: 2, 2025: 6, 2028: 5, 2031: 3, 2033: 7,
                     2036: 6, 2039: 5, 2042: 2, 2044: 7, 2047: 5}


def ganzhi_from_offset(offset: int) -> str:
    return TIANGAN[offset % 10] + DIZHI[offset % 12]


# ============================================================
# Solar term calculation
# ============================================================

SOLAR_TERM_NAMES = [
    "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
    "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑",
    "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至",
]

_solar_term_cache = {}


def _get_solar_term_date(year: int, term_index: int) -> Tuple[int, int]:
    """Return (month, day) for the given solar term in the given year.
    term_index: 0=小寒, 1=大寒, 2=立春, ..., 23=冬至
    Uses cnlunar library for accurate astronomical calculation.
    Falls back to simplified formula if cnlunar unavailable.
    """
    cache_key = (year, term_index)
    if cache_key in _solar_term_cache:
        return _solar_term_cache[cache_key]

    try:
        import cnlunar
        import datetime as _dt
        l = cnlunar.Lunar(_dt.datetime(year, 6, 15, 12, 0))
        st_list = l.getSolarTermsDateList(year)
        dt_obj = st_list[term_index]
        if hasattr(dt_obj, 'month'):
            result = (dt_obj.month, dt_obj.day)
        else:
            result = (dt_obj[0], dt_obj[1])
    except Exception:
        result = _get_solar_term_date_fallback(year, term_index)

    _solar_term_cache[cache_key] = result
    return result


def _get_solar_term_date_fallback(year: int, term_index: int) -> Tuple[int, int]:
    """Fallback: simplified formula when cnlunar is not available."""
    _c = [
        5.4055, 20.12, 3.87, 18.73, 5.63, 20.646, 4.81, 20.1,
        5.52, 21.04, 5.678, 21.37, 7.108, 22.83, 7.5, 23.13,
        7.646, 23.042, 8.318, 23.438, 7.438, 22.36, 7.18, 21.94,
    ]
    _c21 = [
        5.4055, 20.12, 4.81, 18.73, 5.63, 20.646, 4.81, 20.1,
        5.52, 21.04, 5.52, 21.52, 7.25, 22.95, 7.34, 23.13,
        7.84, 23.13, 8.318, 23.438, 7.438, 22.36, 7.04, 21.94,
    ]
    _bm = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12]

    c = _c21[term_index] if year >= 2000 else _c[term_index]
    base_month = _bm[term_index]
    day_f = c + 0.2422 * (year - 1900) - ((year - 1900) // 4)
    day = int(day_f + 0.5)
    if day < 1:
        day = 1
    if day > 31:
        base_month += 1
        day -= 31
    from calendar import monthrange
    _, max_day = monthrange(year, base_month)
    if day > max_day:
        day = max_day
    return (base_month, day)


def _get_bazi_month(year: int, month: int, day: int) -> int:
    """Return Bazi month index (0=寅, 1=卯, ..., 11=丑) based on solar terms.
    Each Bazi month spans two solar terms, e.g. 寅月 = 立春~惊蛰.
    """
    dt = date(year, month, day)
    for i in range(24):
        st_month, st_day = _get_solar_term_date(year, i)
        st_date = date(year, st_month, st_day)
        if dt < st_date:
            before = (i - 1) % 24
            return (before // 2 + 11) % 12
    return 10


def _get_bazi_year(year: int, month: int, day: int) -> int:
    """Return the Bazi year (adjusted for 立春 boundary).
    If the date is before 立春, it belongs to the previous year in Bazi terms."""
    lichun_m, lichun_d = _get_solar_term_date(year, 2)
    if month < lichun_m or (month == lichun_m and day < lichun_d):
        return year - 1
    return year


def year_ganzhi(year: int, month: int = 1, day: int = 1) -> str:
    """Return year pillar, accounting for 立春 boundary when month/day provided."""
    bazi_year = _get_bazi_year(year, month, day)
    idx = (bazi_year - 4) % 60
    return ganzhi_from_offset(idx)


MONTH_GAN_BASE = {
    "甲": 2, "己": 2, "乙": 4, "庚": 4, "丙": 6, "辛": 6,
    "丁": 8, "壬": 8, "戊": 0, "癸": 0,
}


def month_ganzhi(year_gan: str, month_idx: int) -> str:
    """Return month pillar for Bazi month index (0=寅, 1=卯, ..., 11=丑)."""
    start = MONTH_GAN_BASE[year_gan]
    gan_idx = (start + month_idx) % 10
    zhi_idx = (month_idx + 2) % 12
    return TIANGAN[gan_idx] + DIZHI[zhi_idx]


def day_ganzhi_from_date(dt: date) -> str:
    ref = date(1900, 1, 1)
    delta = (dt - ref).days
    return ganzhi_from_offset(delta % 60 + 10)


def hour_ganzhi(day_gan: str, hour: int) -> str:
    zhi_idx = _hour_to_zhi(hour)
    day_gan_idx = TIANGAN_IDX[day_gan]
    gan_idx = (day_gan_idx % 5 * 2 + zhi_idx) % 10
    return TIANGAN[gan_idx] + DIZHI[zhi_idx]


def _hour_to_zhi(hour: int) -> int:
    if 23 <= hour or hour < 1:
        return 0
    return (hour + 1) // 2


def shi_shen(day_gan: str, other_gan: str) -> str:
    if other_gan == day_gan:
        return "比肩"
    dw = WUXING_GAN[day_gan]
    ow = WUXING_GAN[other_gan]
    same_yinyang = (TIANGAN_IDX[day_gan] % 2) == (TIANGAN_IDX[other_gan] % 2)

    if WUXING_SHENG.get(dw) == ow:
        return "食神" if same_yinyang else "伤官"
    if WUXING_KE.get(dw) == ow:
        return "偏财" if same_yinyang else "正财"
    if WUXING_SHENG.get(ow) == dw:
        return "偏印" if same_yinyang else "正印"
    if WUXING_KE.get(ow) == dw:
        return "七杀" if same_yinyang else "正官"
    if dw == ow:
        return "比肩" if same_yinyang else "劫财"
    return "未知"


def changsheng_state(day_gan: str, zhi: str) -> str:
    month_wx = WUXING_ZHI[zhi]
    pos_map = CHANGSHENG_POS.get(month_wx, {})
    pos = pos_map.get(day_gan, 0)
    return CHANGSHENG_12[pos % 12]


def nayin(ganzhi: str) -> str:
    for pair, name in NAYIN_TABLE.items():
        if ganzhi in pair:
            return name
    return "未知"


def kong_wang(day_ganzhi: str) -> List[str]:
    gan_idx = TIANGAN_IDX[day_ganzhi[0]]
    zhi_idx = DIZHI_IDX[day_ganzhi[1]]
    start = zhi_idx + 1
    result = []
    for i in range(10):
        gi = (gan_idx + i + 1) % 10
        zi = (start + i) % 12
        if gi >= zhi_idx + 1 or (gan_idx + i + 1) % 10 != (start + i) % 12:
            pass
    xun_head_gan = gan_idx
    xun_head_zhi = (zhi_idx - gan_idx) % 12
    if xun_head_zhi < 0:
        xun_head_zhi += 12
    void1 = (xun_head_zhi + 10) % 12
    void2 = (xun_head_zhi + 11) % 12
    return [DIZHI[void1], DIZHI[void2]]


def five_element_strength(pillars: Dict[str, str]) -> Dict[str, int]:
    scores = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for pillar_name, ganzhi in pillars.items():
        if not ganzhi or len(ganzhi) < 2:
            continue
        gan = ganzhi[0]
        zhi = ganzhi[1]
        scores[WUXING_GAN[gan]] += 1.0
        cang = ZHI_CANG_GAN.get(zhi, [])
        for ci, cg in enumerate(cang):
            weight = 1.0 if ci == 0 else (0.5 if ci == 1 else 0.3)
            scores[WUXING_GAN[cg]] += weight
    return {k: round(v, 1) for k, v in scores.items()}


def wuxing_relation(wx1: str, wx2: str) -> str:
    if wx1 == wx2:
        return "比助"
    if WUXING_SHENG.get(wx1) == wx2:
        return "我生"
    if WUXING_KE.get(wx1) == wx2:
        return "我克"
    if WUXING_SHENG.get(wx2) == wx1:
        return "生我"
    if WUXING_KE.get(wx2) == wx1:
        return "克我"
    return "无关"


def animal_year(year: int) -> str:
    animals = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
    return animals[(year - 4) % 12]


def build_four_pillars(year: int, month: int, day: int, hour: int,
                       is_lunar: bool = False, gender: str = "男") -> Dict:
    ygz = year_ganzhi(year, month, day)
    bazi_month = _get_bazi_month(year, month, day)
    day_gz = day_ganzhi_from_date(date(year, month, day))
    ygan = ygz[0]
    mgz = month_ganzhi(ygan, bazi_month)
    hgz = hour_ganzhi(day_gz[0], hour)

    pillars = {"年柱": ygz, "月柱": mgz, "日柱": day_gz, "时柱": hgz}
    day_gan = day_gz[0]

    ten_gods = {}
    for pname, gz in pillars.items():
        if pname == "日柱":
            continue
        ten_gods[pname + "天干"] = shi_shen(day_gan, gz[0])
        for ci, cg in enumerate(ZHI_CANG_GAN.get(gz[1], [])):
            label = "本气" if ci == 0 else ("中气" if ci == 1 else "余气")
            ten_gods[f"{pname}地支{label}"] = shi_shen(day_gan, cg)

    wuxing_score = five_element_strength(pillars)
    day_wx = WUXING_GAN[day_gan]

    total = sum(wuxing_score.values()) or 1
    wx_percent = {k: round(v / total * 100, 1) for k, v in wuxing_score.items()}

    strong = wuxing_score.get(day_wx, 0) >= total / 5
    if strong:
        xi = WUXING_KE[day_wx]
        yong = WUXING_KE[day_wx]
    else:
        xi = WUXING_SHENG[day_wx]
        yong = WUXING_BEING_SHENG.get(day_wx, day_wx)

    void = kong_wang(day_gz)

    changsheng_map = {}
    for pname, gz in pillars.items():
        changsheng_map[pname] = changsheng_state(day_gan, gz[1])

    nayin_map = {}
    for pname, gz in pillars.items():
        nayin_map[pname] = nayin(gz)

    return {
        "四柱": pillars,
        "日主": day_gan,
        "日主五行": day_wx,
        "日主阴阳": YINYANG_GAN[day_gan],
        "生肖": animal_year(year),
        "十神": ten_gods,
        "五行力量": wuxing_score,
        "五行占比": wx_percent,
        "日主强弱": "身强" if strong else "身弱",
        "喜用神": yong,
        "喜神": xi,
        "忌神": WUXING_KE.get(yong, "未知"),
        "空亡": void,
        "十二长生": changsheng_map,
        "纳音": nayin_map,
        "地支藏干": {pname: ZHI_CANG_GAN.get(gz[1], []) for pname, gz in pillars.items()},
    }


def build_dayun(gender: str, year_ganzhi: str, month_ganzhi: str,
                start_age: int = 1) -> List[Dict]:
    yin_yang = TIANGAN_IDX[year_ganzhi[0]] % 2
    male = gender in ("男", "M", "male")
    forward = (male and yin_yang == 0) or (not male and yin_yang == 1)

    month_gan_idx = TIANGAN_IDX[month_ganzhi[0]]
    month_zhi_idx = DIZHI_IDX[month_ganzhi[1]]

    dayun_list = []
    for i in range(8):
        if forward:
            g = (month_gan_idx + i + 1) % 10
            z = (month_zhi_idx + i + 1) % 12
        else:
            g = (month_gan_idx - i - 1) % 10
            z = (month_zhi_idx - i - 1) % 12
        age_start = start_age + i * 10
        age_end = age_start + 9
        dayun_list.append({
            "大运": TIANGAN[g] + DIZHI[z],
            "起运年龄": age_start,
            "止运年龄": age_end,
            "天干五行": WUXING_GAN[TIANGAN[g]],
            "地支五行": WUXING_ZHI[DIZHI[z]],
        })
    return dayun_list


def build_liunian(year: int, count: int = 10) -> List[Dict]:
    result = []
    for i in range(count):
        y = year + i
        gz = year_ganzhi(y)
        result.append({
            "年份": y,
            "流年干支": gz,
            "天干五行": WUXING_GAN[gz[0]],
            "地支五行": WUXING_ZHI[gz[1]],
            "生肖": animal_year(y),
        })
    return result


HEXAGRAMS = {
    1: "乾", 2: "坤", 3: "屯", 4: "蒙", 5: "需", 6: "讼", 7: "师", 8: "比",
    9: "小畜", 10: "履", 11: "泰", 12: "否", 13: "同人", 14: "大有", 15: "谦", 16: "豫",
    17: "随", 18: "蛊", 19: "临", 20: "观", 21: "噬嗑", 22: "贲", 23: "剥", 24: "复",
    25: "无妄", 26: "大畜", 27: "颐", 28: "大过", 29: "坎", 30: "离", 31: "咸", 32: "恒",
    33: "遯", 34: "大壮", 35: "晋", 36: "明夷", 37: "家人", 38: "睽", 39: "蹇", 40: "解",
    41: "损", 42: "益", 43: "夬", 44: "姤", 45: "萃", 46: "升", 47: "困", 48: "井",
    49: "革", 50: "鼎", 51: "震", 52: "艮", 53: "渐", 54: "归妹", 55: "丰", 56: "旅",
    57: "巽", 58: "兑", 59: "涣", 60: "节", 61: "中孚", 62: "小过", 63: "既济", 64: "未济",
}

BAGUA = {
    "乾": {"数": 1, "五行": "金", "象": "天", "方位": "西北"},
    "兑": {"数": 2, "五行": "金", "象": "泽", "方位": "西"},
    "离": {"数": 3, "五行": "火", "象": "火", "方位": "南"},
    "震": {"数": 4, "五行": "木", "象": "雷", "方位": "东"},
    "巽": {"数": 5, "五行": "木", "象": "风", "方位": "东南"},
    "坎": {"数": 6, "五行": "水", "象": "水", "方位": "北"},
    "艮": {"数": 7, "五行": "土", "象": "山", "方位": "东北"},
    "坤": {"数": 8, "五行": "土", "象": "地", "方位": "西南"},
}

LIUYAO_LIUQIN = ["父母", "兄弟", "子孙", "妻财", "官鬼"]
LIUYAO_LIUSHEN = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]

WUXING_LIUYIN = {"木": "寅卯", "火": "巳午", "土": "辰戌丑未", "金": "申酉", "水": "亥子"}
