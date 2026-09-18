from __future__ import annotations

import json
import math
from typing import Dict, List, Optional

from .toolkit_base import Toolkit

from .calendar_engine import (
    TIANGAN, DIZHI, TIANGAN_IDX, DIZHI_IDX,
    WUXING_GAN, WUXING_ZHI, year_ganzhi, animal_year,
)


MAJOR_STARS = [
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府",
    "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
]

MINOR_STARS = [
    "文昌", "文曲", "左辅", "右弼", "天魁", "天钺",
    "禄存", "天马", "擎羊", "陀罗", "火星", "铃星",
    "地空", "地劫", "天刑", "天姚", "解神", "天巫",
    "天月", "天哭", "天虚", "龙池", "凤阁", "红鸾", "天喜",
]

PALACE_ORDER = [
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "仆役", "官禄", "田宅", "福德", "父母",
]

PALACE_ASPECTS = {
    "命宫": "性格、外貌、一生总体运势",
    "兄弟": "兄弟姊妹关系、合伙人",
    "夫妻": "婚姻、感情、配偶状况",
    "子女": "子女、下属、晚辈",
    "财帛": "收入、理财能力",
    "疾厄": "健康、灾厄",
    "迁移": "出行、社交、外在表现",
    "仆役": "朋友、下属、人际关系",
    "官禄": "事业、学业、地位",
    "田宅": "不动产、家庭环境",
    "福德": "精神生活、兴趣爱好、寿元",
    "父母": "父母、长辈、上司",
}

WUXING_JU_MAP = {
    ("水二局", "木三局"): 0, ("木三局", "金四局"): 0, ("金四局", "土五局"): 0,
    ("土五局", "火六局"): 0,
}

JU_TABLE = {
    "子": {"甲": "水二局", "己": "水二局", "乙": "木三局", "庚": "木三局", "丙": "火六局", "辛": "火六局", "丁": "土五局", "壬": "土五局", "戊": "金四局", "癸": "金四局"},
    "丑": {"甲": "金四局", "己": "金四局", "乙": "土五局", "庚": "土五局", "丙": "水二局", "辛": "水二局", "丁": "木三局", "壬": "木三局", "戊": "火六局", "癸": "火六局"},
    "寅": {"甲": "木三局", "己": "木三局", "乙": "火六局", "庚": "火六局", "丙": "土五局", "辛": "土五局", "丁": "金四局", "壬": "金四局", "戊": "水二局", "癸": "水二局"},
    "卯": {"甲": "金四局", "己": "金四局", "乙": "木三局", "庚": "木三局", "丙": "火六局", "辛": "火六局", "丁": "土五局", "壬": "土五局", "戊": "水二局", "癸": "水二局"},
    "辰": {"甲": "土五局", "己": "土五局", "乙": "金四局", "庚": "金四局", "丙": "木三局", "辛": "木三局", "丁": "火六局", "壬": "火六局", "戊": "水二局", "癸": "水二局"},
    "巳": {"甲": "木三局", "己": "木三局", "乙": "火六局", "庚": "火六局", "丙": "土五局", "辛": "土五局", "丁": "金四局", "壬": "金四局", "戊": "水二局", "癸": "水二局"},
    "午": {"甲": "金四局", "己": "金四局", "乙": "木三局", "庚": "木三局", "丙": "火六局", "辛": "火六局", "丁": "土五局", "壬": "土五局", "戊": "水二局", "癸": "水二局"},
    "未": {"甲": "土五局", "己": "土五局", "乙": "金四局", "庚": "金四局", "丙": "木三局", "辛": "木三局", "丁": "火六局", "壬": "火六局", "戊": "水二局", "癸": "水二局"},
    "申": {"甲": "火六局", "己": "火六局", "乙": "土五局", "庚": "土五局", "丙": "金四局", "辛": "金四局", "丁": "木三局", "壬": "木三局", "戊": "水二局", "癸": "水二局"},
    "酉": {"甲": "水二局", "己": "水二局", "乙": "木三局", "庚": "木三局", "丙": "火六局", "辛": "火六局", "丁": "土五局", "壬": "土五局", "戊": "金四局", "癸": "金四局"},
    "戌": {"甲": "火六局", "己": "火六局", "乙": "土五局", "庚": "土五局", "丙": "金四局", "辛": "金四局", "丁": "木三局", "壬": "木三局", "戊": "水二局", "癸": "水二局"},
    "亥": {"甲": "火六局", "己": "火六局", "乙": "土五局", "庚": "土五局", "丙": "金四局", "辛": "金四局", "丁": "木三局", "壬": "木三局", "戊": "水二局", "癸": "水二局"},
}


def _find_ming_gong_zhi(month: int, hour_zhi_idx: int) -> int:
    return (2 + month - 1 - hour_zhi_idx) % 12


def _find_shen_gong_zhi(month: int, hour_zhi_idx: int) -> int:
    return (2 + month - 1 + hour_zhi_idx) % 12


def _find_wuxing_ju(ming_gong_zhi: str, year_gan: str) -> str:
    table = JU_TABLE.get(ming_gong_zhi, {})
    return table.get(year_gan, "土五局")


def _ju_number(ju: str) -> int:
    return {"水二局": 2, "木三局": 3, "金四局": 4, "土五局": 5, "火六局": 6}.get(ju, 5)


def _place_ziwei(ju_num: int, day: int) -> int:
    quotient = (day - 1) // ju_num
    remainder = (day - 1) % ju_num
    if remainder == 0:
        return (2 + quotient - 1) % 12
    else:
        return (2 + quotient) % 12


ZIWEI_FOLLOWERS = {
    0: [0, 11], 1: [1, 10], 2: [2, 9], 3: [3, 8],
    4: [4, 7], 5: [5, 6], 6: [6, 5], 7: [7, 4],
    8: [8, 3], 9: [9, 2], 10: [10, 1], 11: [11, 0],
}

STAR_NAMES_IN_SYSTEM = {
    "紫微星系": ["紫微", "天机", "太阳", "武曲", "天同", "廉贞"],
    "天府星系": ["天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"],
}

ZIWEI_SERIES = ["紫微", "天机", "太阳", "武曲", "天同", "廉贞"]
ZIWEI_OFFSETS = [0, -1, -3, -4, -5, -8]

TIANFU_SERIES = ["天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"]
TIANFU_OFFSETS = [0, 1, 2, 3, 4, 5, 6, 10]


class ZiweiToolkit(Toolkit):
    def __init__(self, **kwargs):
        tools = [
            self.paipan,
            self.analyze_palace,
            self.analyze_career,
            self.analyze_marriage,
            self.analyze_wealth,
            self.analyze_health,
            self.analyze_personality,
            self.find_major_periods,
            find_star_info := None,
            self.star_info,
            self.palace_aspects,
        ]
        super().__init__(name="ziwei_tools", tools=[t for t in tools if t is not None], **kwargs)

    def paipan(self, year: int, month: int, day: int, hour: int,
               gender: str = "男") -> str:
        """
        排紫微斗数命盘：根据公历出生时间排出完整的紫微斗数命盘，包含十二宫主星和辅星。

        Args:
            year: 公历年份
            month: 公历月份 (农历月份可直接传)
            day: 出生日期
            hour: 出生时辰 (0-23)
            gender: 性别 ("男" 或 "女")
        """
        try:
            hour_zhi_idx = self._hour_to_zhi(hour)
            year_gz = year_ganzhi(year)
            year_gan = year_gz[0]

            ming_gong_idx = _find_ming_gong_zhi(month, hour_zhi_idx)
            shen_gong_idx = _find_shen_gong_zhi(month, hour_zhi_idx)

            ming_gong_zhi = DIZHI[ming_gong_idx]
            wuxing_ju = _find_wuxing_ju(ming_gong_zhi, year_gan)
            ju_num = _ju_number(wuxing_ju)

            ziwei_pos = _place_ziwei(ju_num, day)
            tianfu_pos = (4 - ziwei_pos) % 12

            stars_in_palaces = {i: [] for i in range(12)}

            for star, offset in zip(ZIWEI_SERIES, ZIWEI_OFFSETS):
                pos = (ziwei_pos + offset) % 12
                stars_in_palaces[pos].append(star)

            for star, offset in zip(TIANFU_SERIES, TIANFU_OFFSETS):
                pos = (tianfu_pos + offset) % 12
                stars_in_palaces[pos].append(star)

            changsheng_pos = self._changsheng_start(year_gan, gender)
            changsheng_in_palace = {}
            for i in range(12):
                from .calendar_engine import CHANGSHENG_12
                idx = (changsheng_pos + i) % 12
                changsheng_in_palace[i] = CHANGSHENG_12[idx]

            palaces = {}
            for i, palace_name in enumerate(PALACE_ORDER):
                palace_zhi_idx = (ming_gong_idx + i) % 12
                palace_zhi = DIZHI[palace_zhi_idx]
                palaces[palace_name] = {
                    "宫位地支": palace_zhi,
                    "主星": stars_in_palaces[palace_zhi_idx],
                    "十二长生": changsheng_in_palace.get(palace_zhi_idx, ""),
                }

            body_palace_name = PALACE_ORDER[(shen_gong_idx - ming_gong_idx) % 12]
            if body_palace_name not in palaces:
                body_palace_name = "命宫"

            return json.dumps({
                "success": True,
                "出生信息": f"{year}年{month}月{day}日{hour}时",
                "性别": gender,
                "年干支": year_gz,
                "生肖": animal_year(year),
                "命宫": {
                    "地支": ming_gong_zhi,
                    "位置索引": ming_gong_idx,
                },
                "身宫": body_palace_name,
                "五行局": wuxing_ju,
                "十二宫": palaces,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def analyze_palace(self, palace_name: str, stars_json: str) -> str:
        """
        分析单个宫位：根据宫位名称和所含星曜，提供该宫位的含义解读基础。

        Args:
            palace_name: 宫位名称 (如 "命宫", "夫妻宫")
            stars_json: 该宫位星曜列表的 JSON 数组 (如 '["紫微", "天相"]')
        """
        try:
            stars = json.loads(stars_json)
            aspects = PALACE_ASPECTS.get(palace_name, "未知宫位")

            star_nature = {}
            for star in stars:
                nature = self._star_nature(star)
                star_nature[star] = nature

            return json.dumps({
                "success": True,
                "宫位": palace_name,
                "主管范畴": aspects,
                "所含星曜": stars,
                "星曜属性": star_nature,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def analyze_career(self, guanlu_stars_json: str, ming_stars_json: str) -> str:
        """
        分析紫微斗数事业运：根据官禄宫和命宫星曜分析事业倾向。

        Args:
            guanlu_stars_json: 官禄宫星曜的 JSON 数组
            ming_stars_json: 命宫星曜的 JSON 数组
        """
        try:
            guanlu_stars = json.loads(guanlu_stars_json)
            ming_stars = json.loads(ming_stars_json)

            leadership = ["紫微", "天府", "太阳", "武曲", "天相"]
            creative = ["天机", "贪狼", "廉贞", "破军"]
            stable = ["天同", "太阴", "天梁"]

            traits = []
            for star in guanlu_stars + ming_stars:
                if star in leadership:
                    traits.append(f"{star}(领导型)")
                elif star in creative:
                    traits.append(f"{star}(开创型)")
                elif star in stable:
                    traits.append(f"{star}(支援型)")

            return json.dumps({
                "success": True,
                "官禄宫星曜": guanlu_stars,
                "命宫星曜": ming_stars,
                "事业特质": traits,
                "领导型星曜": [s for s in guanlu_stars + ming_stars if s in leadership],
                "开创型星曜": [s for s in guanlu_stars + ming_stars if s in creative],
                "支援型星曜": [s for s in guanlu_stars + ming_stars if s in stable],
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def analyze_marriage(self, couple_stars_json: str) -> str:
        """
        分析紫微斗数婚姻：根据夫妻宫星曜分析感情婚姻倾向。

        Args:
            couple_stars_json: 夫妻宫星曜的 JSON 数组
        """
        try:
            stars = json.loads(couple_stars_json)

            romantic = ["贪狼", "廉贞", "破军", "太阴"]
            stable_marriage = ["天府", "天相", "天梁", "天同"]
            volatile = ["七杀", "破军", "贪狼"]

            traits = []
            for star in stars:
                if star in romantic:
                    traits.append(f"{star}(桃花型)")
                elif star in stable_marriage:
                    traits.append(f"{star}(稳定型)")
                elif star in volatile:
                    traits.append(f"{star}(波折型)")

            return json.dumps({
                "success": True,
                "夫妻宫星曜": stars,
                "感情特质": traits,
                "桃花星": [s for s in stars if s in romantic],
                "稳定星": [s for s in stars if s in stable_marriage],
                "波折星": [s for s in stars if s in volatile],
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def analyze_wealth(self, caibo_stars_json: str) -> str:
        """
        分析紫微斗数财运：根据财帛宫星曜分析财运倾向。

        Args:
            caibo_stars_json: 财帛宫星曜的 JSON 数组
        """
        try:
            stars = json.loads(caibo_stars_json)

            financial = ["天府", "武曲", "太阴", "天相"]
            speculative = ["贪狼", "破军", "廉贞", "七杀"]

            return json.dumps({
                "success": True,
                "财帛宫星曜": stars,
                "理财型星曜": [s for s in stars if s in financial],
                "投机型星曜": [s for s in stars if s in speculative],
                "财运倾向": "稳健理财" if any(s in financial for s in stars) else
                             "大胆进取" if any(s in speculative for s in stars) else "平稳",
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def analyze_health(self, jie_stars_json: str) -> str:
        """
        分析紫微斗数健康：根据疾厄宫星曜分析健康倾向。

        Args:
            jie_stars_json: 疾厄宫星曜的 JSON 数组
        """
        try:
            stars = json.loads(jie_stars_json)
            star_health = {
                "紫微": "脾胃", "天机": "肝胆神经", "太阳": "心脏眼睛",
                "武曲": "呼吸系统", "天同": "泌尿系统", "廉贞": "心血管",
                "天府": "脾胃", "太阴": "肾脏眼目", "贪狼": "肝胆泌尿",
                "巨门": "口喉呼吸道", "天相": "皮肤肠胃", "天梁": "骨骼",
                "七杀": "肺呼吸外伤", "破军": "肾脏泌尿生殖",
            }
            organs = []
            for s in stars:
                if s in star_health:
                    organs.append({"星曜": s, "对应部位": star_health[s]})

            return json.dumps({
                "success": True,
                "疾厄宫星曜": stars,
                "对应健康关注": organs,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def analyze_personality(self, ming_stars_json: str) -> str:
        """
        分析紫微斗数性格：根据命宫星曜分析性格特征。

        Args:
            ming_stars_json: 命宫星曜的 JSON 数组
        """
        try:
            stars = json.loads(ming_stars_json)
            star_traits = {
                "紫微": {"性格": "威严、大方、领袖气质", "类型": "领导型"},
                "天机": {"性格": "聪明、善变、思考灵活", "类型": "智慧型"},
                "太阳": {"性格": "热情、大方、乐于助人", "类型": "奉献型"},
                "武曲": {"性格": "刚毅、果断、重实际", "类型": "实干型"},
                "天同": {"性格": "温和、随和、享受生活", "类型": "享受型"},
                "廉贞": {"性格": "能干、好胜、多才多艺", "类型": "开创型"},
                "天府": {"性格": "稳重、保守、善理财", "类型": "领导型"},
                "太阴": {"性格": "温柔、敏感、重视感情", "类型": "浪漫型"},
                "贪狼": {"性格": "多才多艺、交际广泛、欲望强", "类型": "桃花型"},
                "巨门": {"性格": "口才好、多疑、分析力强", "类型": "研究型"},
                "天相": {"性格": "随和、善于协调、重视形象", "类型": "服务型"},
                "天梁": {"性格": "正直、慈悲、好为人师", "类型": "助人型"},
                "七杀": {"性格": "勇敢、独立、冲劲十足", "类型": "开创型"},
                "破军": {"性格": "破坏力强、善变、不墨守成规", "类型": "开创型"},
            }

            personality = []
            for s in stars:
                if s in star_traits:
                    personality.append({"星曜": s, **star_traits[s]})

            return json.dumps({
                "success": True,
                "命宫星曜": stars,
                "性格分析": personality,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def find_major_periods(self, wuxing_ju: str, gender: str) -> str:
        """
        排大限：根据五行局和性别排出紫微斗数十二宫大限年龄段。

        Args:
            wuxing_ju: 五行局 (如 "水二局", "木三局")
            gender: 性别 ("男" 或 "女")
        """
        try:
            ju_num = _ju_number(wuxing_ju)
            start_age = ju_num
            male = gender in ("男", "M", "male")

            periods = []
            for i, palace_name in enumerate(PALACE_ORDER):
                age_start = start_age + i * 10
                age_end = age_start + 9
                direction = "顺行" if male else "逆行"
                periods.append({
                    "宫位": palace_name,
                    "起运年龄": age_start,
                    "止运年龄": age_end,
                    "大限走向": direction,
                })

            return json.dumps({
                "success": True,
                "五行局": wuxing_ju,
                "性别": gender,
                "起运年龄": start_age,
                "大限": periods,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def star_info(self, star_name: str) -> str:
        """
        查询星曜信息：查询紫微斗数中某颗星曜的基本属性（五行、阴阳、星系等）。

        Args:
            star_name: 星曜名称 (如 "紫微", "贪狼")
        """
        try:
            star_attrs = {
                "紫微": {"五行": "阴土", "星系": "紫微星系", "类别": "主星", "特点": "帝座，主官禄，化气为尊"},
                "天机": {"五行": "阴木", "星系": "紫微星系", "类别": "主星", "特点": "益算之宿，化气为善"},
                "太阳": {"五行": "阳火", "星系": "紫微星系", "类别": "主星", "特点": "日之精，化气为贵"},
                "武曲": {"五行": "阴金", "星系": "紫微星系", "类别": "主星", "特点": "财星，化气为财"},
                "天同": {"五行": "阳水", "星系": "紫微星系", "类别": "主星", "特点": "福星，化气为福"},
                "廉贞": {"五行": "阴火", "星系": "紫微星系", "类别": "主星", "特点": "囚星，化气为囚"},
                "天府": {"五行": "阳土", "星系": "天府星系", "类别": "主星", "特点": "令星，主财帛"},
                "太阴": {"五行": "阴水", "星系": "天府星系", "类别": "主星", "特点": "月之精，化气为富"},
                "贪狼": {"五行": "阳木", "星系": "天府星系", "类别": "主星", "特点": "桃花星，化气为桃花"},
                "巨门": {"五行": "阴土", "星系": "天府星系", "类别": "主星", "特点": "暗星，化气为暗"},
                "天相": {"五行": "阳水", "星系": "天府星系", "类别": "主星", "特点": "印星，化气为印"},
                "天梁": {"五行": "阳土", "星系": "天府星系", "类别": "主星", "特点": "荫星，化气为荫"},
                "七杀": {"五行": "阴金", "星系": "天府星系", "类别": "主星", "特点": "将星，化气为将"},
                "破军": {"五行": "阴水", "星系": "天府星系", "类别": "主星", "特点": "耗星，化气为耗"},
                "文昌": {"五行": "阳金", "星系": "辅星", "类别": "六吉星", "特点": "主科甲，文才"},
                "文曲": {"五行": "阴水", "星系": "辅星", "类别": "六吉星", "特点": "主才艺，异路功名"},
                "左辅": {"五行": "阳土", "星系": "辅星", "类别": "六吉星", "特点": "助力，善辅佐"},
                "右弼": {"五行": "阴水", "星系": "辅星", "类别": "六吉星", "特点": "助力，善辅佐"},
                "天魁": {"五行": "阳火", "星系": "辅星", "类别": "六吉星", "特点": "昼贵人"},
                "天钺": {"五行": "阴火", "星系": "辅星", "类别": "六吉星", "特点": "夜贵人"},
                "禄存": {"五行": "阴土", "星系": "辅星", "类别": "吉星", "特点": "主财禄"},
                "擎羊": {"五行": "阳金", "星系": "辅星", "类别": "六煞星", "特点": "主刑伤"},
                "陀罗": {"五行": "阴金", "星系": "辅星", "类别": "六煞星", "特点": "主拖延"},
                "火星": {"五行": "阳火", "星系": "辅星", "类别": "六煞星", "特点": "主暴败"},
                "铃星": {"五行": "阴火", "星系": "辅星", "类别": "六煞星", "特点": "主暗耗"},
                "地空": {"五行": "阴火", "星系": "辅星", "类别": "六煞星", "特点": "主虚空"},
                "地劫": {"五行": "阳火", "星系": "辅星", "类别": "六煞星", "特点": "主劫耗"},
            }
            info = star_attrs.get(star_name)
            if not info:
                return json.dumps({"success": False, "error": f"未找到星曜 '{star_name}'"}, ensure_ascii=False)
            return json.dumps({"success": True, "星曜": star_name, **info}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def palace_aspects(self) -> str:
        """
        列出紫微斗数十二宫位及其主管范畴。无需参数。
        """
        return json.dumps({"success": True, "十二宫位": PALACE_ASPECTS}, ensure_ascii=False)

    def _hour_to_zhi(self, hour: int) -> int:
        if 23 <= hour or hour < 1:
            return 0
        return (hour + 1) // 2

    def _changsheng_start(self, year_gan: str, gender: str) -> int:
        wx = WUXING_GAN[year_gan]
        starts = {"木": 2, "火": 5, "土": 5, "金": 8, "水": 9}
        pos = starts.get(wx, 0)
        yin_yang = TIANGAN_IDX[year_gan] % 2
        male = gender in ("男", "M", "male")
        if (male and yin_yang == 0) or (not male and yin_yang == 1):
            return pos
        else:
            return (12 - pos) % 12

    def _star_nature(self, star: str) -> Dict:
        natures = {
            "紫微": {"属性": "帝星", "吉凶": "吉"},
            "天机": {"属性": "善星", "吉凶": "吉"},
            "太阳": {"属性": "贵星", "吉凶": "吉"},
            "武曲": {"属性": "财星", "吉凶": "吉"},
            "天同": {"属性": "福星", "吉凶": "吉"},
            "廉贞": {"属性": "囚星", "吉凶": "半吉半凶"},
            "天府": {"属性": "令星", "吉凶": "吉"},
            "太阴": {"属性": "富星", "吉凶": "吉"},
            "贪狼": {"属性": "桃花", "吉凶": "半吉半凶"},
            "巨门": {"属性": "暗星", "吉凶": "凶"},
            "天相": {"属性": "印星", "吉凶": "吉"},
            "天梁": {"属性": "荫星", "吉凶": "吉"},
            "七杀": {"属性": "将星", "吉凶": "凶"},
            "破军": {"属性": "耗星", "吉凶": "凶"},
        }
        return natures.get(star, {"属性": "未知", "吉凶": "未知"})
