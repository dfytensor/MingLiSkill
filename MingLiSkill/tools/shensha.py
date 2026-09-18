# -*- coding: utf-8 -*-
"""
shensha.py — 神煞工具（标准查表，非可调参数）
桃花(咸池)/红鸾/天喜/驿马/文昌/华盖/羊刃/三刑/六害
"""
SANHE_GROUP = {
    frozenset("申子辰"): "水局",
    frozenset("寅午戌"): "火局",
    frozenset("巳酉丑"): "金局",
    frozenset("亥卯未"): "木局",
}

def _group(zhi):
    for g, name in SANHE_GROUP.items():
        if zhi in g:
            return g
    return None

# 桃花(咸池): 申子辰在酉, 寅午戌在卯, 巳酉丑在午, 亥卯未在子
TAOHUA = {"申": "酉", "子": "酉", "辰": "酉", "寅": "卯", "午": "卯", "戌": "卯",
          "巳": "午", "酉": "午", "丑": "午", "亥": "子", "卯": "子", "未": "子"}
# 驿马: 申子辰在寅, 寅午戌在申, 巳酉丑在亥, 亥卯未在巳
YIMA = {"申": "寅", "子": "寅", "辰": "寅", "寅": "申", "午": "申", "戌": "申",
        "巳": "亥", "酉": "亥", "丑": "亥", "亥": "巳", "卯": "巳", "未": "巳"}
# 华盖: 三合库位
HUAGAI = {"申": "辰", "子": "辰", "辰": "辰", "寅": "戌", "午": "戌", "戌": "戌",
          "巳": "丑", "酉": "丑", "丑": "丑", "亥": "未", "卯": "未", "未": "未"}
# 红鸾: 子年卯逆行; 天喜 = 红鸾对冲
HONGluAN = {"子": "卯", "丑": "寅", "寅": "丑", "卯": "子", "辰": "亥", "巳": "戌",
            "午": "酉", "未": "申", "申": "未", "酉": "午", "戌": "巳", "亥": "辰"}
CHONG_PAIR = [("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]
DUI = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
       "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
# 文昌: 甲巳 乙午 丙戊申 丁己酉 庚亥 辛子 壬寅 癸卯
WENCHANG = {"甲": "巳", "乙": "午", "丙": "申", "戊": "申", "丁": "酉", "己": "酉",
            "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯"}
# 三刑
SAN_XING_GROUPS = [frozenset("寅巳申"), frozenset("丑戌未"), frozenset("子卯")]
ZI_XING = ["辰", "午", "酉", "亥"]


def _chong(a, b):
    return (a, b) in CHONG_PAIR or (b, a) in CHONG_PAIR


def natal_shensha(year_zhi: str, day_zhi: str, day_gan: str) -> dict:
    """原局神煞（以年支+日支查）。"""
    seen = set()
    def add(pos, name, base):
        seen.add((pos, name, base))
    for base, zhi in (("年支", year_zhi), ("日支", day_zhi)):
        add(TAOHUA[zhi], "桃花", base)
        add(YIMA[zhi], "驿马", base)
        add(HUAGAI[zhi], "华盖", base)
        hong = HONGluAN[zhi]
        add(hong, "红鸾", base)
        add(DUI[hong], "天喜", base)
    add(WENCHANG.get(day_gan, ""), "文昌", "日干")
    return {"positions": dict(((p, n) for p, n, _ in seen)),
            "list": sorted(set("%s(%s%s)" % (p, n, b) for p, n, b in seen))}


def year_shensha(year_zhi_natal: str, day_zhi_natal: str, liunian_zhi: str,
                 natal_zhis) -> list:
    """流年触发神煞：流年地支 == 原局神煞位 → 该神煞被引动。"""
    hits = []
    for base, zhi in (("年支", year_zhi_natal), ("日支", day_zhi_natal)):
        if liunian_zhi == TAOHUA[zhi]:
            hits.append("桃花(%s查)" % base)
        if liunian_zhi == YIMA[zhi]:
            hits.append("驿马(%s查)" % base)
        if liunian_zhi == HUAGAI[zhi]:
            hits.append("华盖(%s查)" % base)
        hong = HONGluAN[zhi]
        if liunian_zhi == hong:
            hits.append("红鸾(%s查)" % base)
        if liunian_zhi == DUI[hong]:
            hits.append("天喜(%s查)" % base)
    # 流年支与原局四支构成三刑
    allz = list(natal_zhis) + [liunian_zhi]
    for g in SAN_XING_GROUPS:
        if g.issubset(set(allz)):
            hits.append("三刑(%s)" % "".join(sorted(g)))
    for z in natal_zhis:
        if z == liunian_zhi and z in ZI_XING:
            hits.append("自刑(%s)" % z)
    return hits


def year_ganzhi(zhi: str) -> bool:
    return True
