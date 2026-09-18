# -*- coding: utf-8 -*-
"""
marriage_scorer.py — 婚期评分器（SKILL.md 婚期多候选排序规则的机械化实现）

评分规则（源自 SKILL.md 2.2 婚姻节 + v5 修正）:
  +3  流年天干 = 正配偶星 (男命正财 / 女命正官)
  +1  流年天干 = 偏配偶星 (男命偏财 / 女命七杀)
  +1  流年地支本气藏干 = 正配偶星 (+0.5 若偏配偶星)
  +2  流年支与日支(配偶宫)六合 / 三合(含第三支); 半合 +1
  ±0  流年支冲日支(动婚, 需配偶星同现, 否则 -2)
  -2  流年支冲年支/月支; -1 冲时支
  +1  流年伏吟日柱
  +1/-1  喜用年 / 忌神年 (双标签抵消=0)
  -3  大运冲年支或月支
  -3  女命流年天干=伤官(克夫年); 男命流年天干=比肩/劫财(争财年) -2
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

LIUHE = [("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")]
CHONG = [("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]
SANHE_GROUPS = [("申", "子", "辰"), ("亥", "卯", "未"), ("寅", "午", "戌"), ("巳", "酉", "丑")]


def _pair(a, b, table):
    return (a, b) in table or (b, a) in table


def _liuhe(a, b):
    return _pair(a, b, LIUHE)


def _chong(a, b):
    return _pair(a, b, CHONG)


def _sanhe_hits(year_zhi, day_zhi, all_zhis):
    """returns (full_he, half_he)"""
    for g in SANHE_GROUPS:
        if year_zhi in g and day_zhi in g:
            third = [x for x in g if x not in (year_zhi, day_zhi)]
            if any(z in third for z in all_zhis):
                return True, False
            return False, True
    return False, False


def spouse_stars(day_gan, gender):
    """return (zheng, pian) 十神 names for the spouse star."""
    from tools.calendar_engine import shi_shen
    male = gender in ("男", "M", "male")
    # scan all 10 stems to find which produces 正财/偏财 (male) or 正官/七杀 (female)
    from tools.calendar_engine import TIANGAN
    zheng = pian = None
    targets = ("正财", "偏财") if male else ("正官", "七杀")
    for g in TIANGAN:
        ss = shi_shen(day_gan, g)
        if ss == targets[0]:
            zheng = ss
        elif ss == targets[1]:
            pian = ss
    return zheng, pian


def score_marriage_year(chart, year_entry, birth_year=None):
    """year_entry: dict from liunian_analyzer.analyze_single_year (年份/流年干支/天干十神/地支藏干十神/tags...)."""
    day_gan = chart["日主"]
    gender = chart.get("gender", "男")
    pillars = chart["四柱"]
    day_zhi = pillars["日柱"][1]
    year_zhi = pillars["年柱"][1]
    month_zhi = pillars["月柱"][1]
    hour_zhi = pillars["时柱"][1]
    all_zhis = [year_zhi, month_zhi, day_zhi, hour_zhi]

    zheng, pian = spouse_stars(day_gan, gender)
    male = gender in ("男", "M", "male")

    y = year_entry
    gz = y.get("流年干支") or y.get("干支") or ""
    if not gz or len(gz) < 2:
        return None
    lz_gan, lz_zhi = gz[0], gz[1]
    s = 0
    notes = []

    gan_ss = y.get("天干十神", "")
    if zheng and gan_ss == zheng:
        s += 3
        notes.append("正偶星透干+3")
    elif pian and gan_ss == pian:
        s += 1
        notes.append("偏偶星透干+1")

    zhi_cang_ss = y.get("地支藏干十神", [])
    if zheng and zhi_cang_ss and zhi_cang_ss[0] == zheng:
        s += 1
        notes.append("正偶星藏本气+1")
    elif pian and zhi_cang_ss and zhi_cang_ss[0] == pian:
        s += 0.5
        notes.append("偏偶星藏本气+0.5")

    spouse_star_present = (zheng and (gan_ss == zheng or (zhi_cang_ss and zheng in zhi_cang_ss))) or \
                          (pian and (gan_ss == pian or (zhi_cang_ss and pian in zhi_cang_ss)))

    full, half = _sanhe_hits(lz_zhi, day_zhi, all_zhis)
    if _liuhe(lz_zhi, day_zhi):
        s += 2
        notes.append("流年合配偶宫+2")
    elif full:
        s += 2
        notes.append("流年三合配偶宫+2")
    elif half:
        s += 1
        notes.append("流年半合配偶宫+1")

    if _chong(lz_zhi, day_zhi):
        if spouse_star_present:
            notes.append("冲配偶宫(动婚)±0")
        else:
            s -= 2
            notes.append("冲配偶宫无配偶星-2")

    if _chong(lz_zhi, year_zhi):
        s -= 2
        notes.append("流年冲年支-2")
    if _chong(lz_zhi, month_zhi):
        s -= 2
        notes.append("流年冲月支-2")
    if _chong(lz_zhi, hour_zhi):
        s -= 1
        notes.append("流年冲时支-1")

    if lz_zhi == day_zhi:
        s += 1
        notes.append("伏吟日柱+1")

    tags = y.get("标签", [])
    is_yong = any("喜用" in t for t in tags)
    is_ji = any("忌神" in t for t in tags)
    if is_yong and not is_ji:
        s += 1
        notes.append("喜用年+1")
    elif is_ji and not is_yong:
        s -= 1
        notes.append("忌神年-1")
    elif is_yong and is_ji:
        notes.append("喜忌抵消±0")

    # 大运冲命
    du = y.get("当前大运", {})
    du_gz = du.get("大运干支", "")
    if du_gz and len(du_gz) >= 2:
        du_zhi = du_gz[1]
        if _chong(du_zhi, year_zhi) or _chong(du_zhi, month_zhi):
            s -= 3
            notes.append("大运冲年/月柱-3")
        elif _chong(du_zhi, day_zhi):
            notes.append("大运冲日支(动婚)±0")

    # 女命伤官透干 = 克夫年, 非婚; 男命比劫透干 = 争财
    if not male and gan_ss == "伤官":
        s -= 3
        notes.append("女命伤官透干-3")
    if male and gan_ss in ("比肩", "劫财"):
        s -= 2
        notes.append("男命比劫透干-2")

    return {"year": y.get("年份"), "ganzhi": gz, "score": s, "notes": notes}


def rank_years(chart, liunian_data):
    """liunian_data: dict with 年份流年对比 list. Returns sorted list of scored years (desc)."""
    out = []
    for yi in liunian_data.get("年份流年对比", []):
        r = score_marriage_year(chart, yi)
        if r:
            out.append(r)
    out.sort(key=lambda x: -x["score"])
    return out
