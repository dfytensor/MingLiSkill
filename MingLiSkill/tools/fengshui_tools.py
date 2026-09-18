from __future__ import annotations

import json
from typing import Dict, List, Optional

from .toolkit_base import Toolkit

from .calendar_engine import (
    TIANGAN, DIZHI, TIANGAN_IDX, DIZHI_IDX,
    WUXING_GAN, WUXING_ZHI, year_ganzhi, BAGUA,
)


BAZHAI_BAGUA_MAP = {
    "坎": {"伏位": "坎", "生气": "离", "天医": "震", "延年": "巽",
           "绝命": "坤", "五鬼": "艮", "六煞": "乾", "祸害": "兑"},
    "坤": {"伏位": "坤", "生气": "艮", "天医": "兑", "延年": "乾",
           "绝命": "坎", "五鬼": "巽", "六煞": "离", "祸害": "震"},
    "震": {"伏位": "震", "生气": "巽", "天医": "坎", "延年": "离",
           "绝命": "兑", "五鬼": "乾", "六煞": "艮", "祸害": "坤"},
    "巽": {"伏位": "巽", "生气": "震", "天医": "离", "延年": "坎",
           "绝命": "艮", "五鬼": "坤", "六煞": "乾", "祸害": "兑"},
    "乾": {"伏位": "乾", "生气": "坤", "天医": "艮", "延年": "兑",
           "绝命": "离", "五鬼": "震", "六煞": "坎", "祸害": "巽"},
    "兑": {"伏位": "兑", "生气": "乾", "天医": "坤", "延年": "艮",
           "绝命": "震", "五鬼": "巽", "六煞": "离", "祸害": "坎"},
    "艮": {"伏位": "艮", "生气": "坤", "天医": "乾", "延年": "兑",
           "绝命": "巽", "五鬼": "离", "六煞": "震", "祸害": "乾"},
    "离": {"伏位": "离", "生气": "坎", "天医": "巽", "延年": "震",
           "绝命": "乾", "五鬼": "兑", "六煞": "坤", "祸害": "艮"},
}

FANGWEI_BAGUA = {
    "北": "坎", "东北": "艮", "东": "震", "东南": "巽",
    "南": "离", "西南": "坤", "西": "兑", "西北": "乾",
}

JI_FANG = ["生气", "天医", "延年", "伏位"]
XIONG_FANG = ["绝命", "五鬼", "六煞", "祸害"]

XUANKONG_PERIOD_STARS = {
    1: [1, 2, 3, 4, 5, 6, 7, 8, 9],
    2: [2, 3, 4, 5, 6, 7, 8, 9, 1],
    3: [3, 4, 5, 6, 7, 8, 9, 1, 2],
    4: [4, 5, 6, 7, 8, 9, 1, 2, 3],
    5: [5, 6, 7, 8, 9, 1, 2, 3, 4],
    6: [6, 7, 8, 9, 1, 2, 3, 4, 5],
    7: [7, 8, 9, 1, 2, 3, 4, 5, 6],
    8: [8, 9, 1, 2, 3, 4, 5, 6, 7],
    9: [9, 1, 2, 3, 4, 5, 6, 7, 8],
}

FEIXING_LOUSHU_ORDER = [5, 6, 7, 8, 9, 1, 2, 3, 4]
GONG_POSITIONS = {
    "中": 5, "乾": 6, "兑": 7, "艮": 8, "离": 9,
    "坎": 1, "坤": 2, "震": 3, "巽": 4,
}

STAR_MEANING = {
    1: {"名": "一白", "五行": "水", "吉凶": "吉", "主": "官贵、桃花、智慧"},
    2: {"名": "二黑", "五行": "土", "吉凶": "凶", "主": "病符、小人"},
    3: {"名": "三碧", "五行": "木", "吉凶": "凶", "主": "是非、官灾"},
    4: {"名": "四绿", "五行": "木", "吉凶": "吉", "主": "文昌、学业"},
    5: {"名": "五黄", "五行": "土", "吉凶": "大凶", "主": "灾厄、疾病"},
    6: {"名": "六白", "五行": "金", "吉凶": "吉", "主": "武贵、权力"},
    7: {"名": "七赤", "五行": "金", "吉凶": "凶", "主": "口舌、盗贼"},
    8: {"名": "八白", "五行": "土", "吉凶": "吉", "主": "财帛、置业"},
    9: {"名": "九紫", "五行": "火", "吉凶": "吉", "主": "喜庆、姻缘"},
}


class FengShuiToolkit(Toolkit):
    def __init__(self, **kwargs):
        tools = [
            self.bazhai_minggua,
            self.bazhai_fangwei,
            self.xuankong_period,
            self.xuankong_feixing,
            self.star_meaning,
            self.direction_analysis,
            self.wuxing_shape,
            self.suggest_layout,
        ]
        super().__init__(name="fengshui_tools", tools=tools, **kwargs)

    def bazhai_minggua(self, year: int, gender: str = "男") -> str:
        """
        八宅命卦：根据出生年份和性别计算命卦（东四命或西四命）。

        Args:
            year: 出生年份 (公历)
            gender: 性别 ("男" 或 "女")
        """
        try:
            digits = [int(d) for d in str(year)]
            total = sum(digits)
            while total > 9:
                total = sum(int(d) for d in str(total))

            male = gender in ("男", "M", "male")
            if male:
                gua_num = 11 - total
            else:
                gua_num = total + 4

            gua_num = gua_num % 9
            if gua_num == 0:
                gua_num = 9

            num_gua = {1: "坎", 2: "坤", 3: "震", 4: "巽", 5: "坤" if male else "艮",
                       6: "乾", 7: "兑", 8: "艮", 9: "离"}
            gua_name = num_gua.get(gua_num, "坤")

            dong_si = {"坎", "离", "震", "巽"}
            xi_si = {"乾", "坤", "艮", "兑"}
            ming_group = "东四命" if gua_name in dong_si else "西四命"

            return json.dumps({
                "success": True,
                "出生年": year,
                "性别": gender,
                "命卦数": gua_num,
                "命卦": gua_name,
                "命组": ming_group,
                "吉方": {k: v for k, v in BAZHAI_BAGUA_MAP[gua_name].items() if k in JI_FANG},
                "凶方": {k: v for k, v in BAZHAI_BAGUA_MAP[gua_name].items() if k in XIONG_FANG},
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def bazhai_fangwei(self, ming_gua: str, direction: str) -> str:
        """
        八宅方位吉凶：查询命卦在某一方位的吉凶属性。

        Args:
            ming_gua: 命卦 (如 "坎", "离", "震", "乾")
            direction: 方位 (如 "北", "南", "东", "西", "东北", "东南", "西北", "西南")
        """
        try:
            target_gua = FANGWEI_BAGUA.get(direction)
            if not target_gua:
                return json.dumps({"success": False, "error": f"未知方位 '{direction}'"}, ensure_ascii=False)

            gua_map = BAZHAI_BAGUA_MAP.get(ming_gua)
            if not gua_map:
                return json.dumps({"success": False, "error": f"未知命卦 '{ming_gua}'"}, ensure_ascii=False)

            for star_name, gua in gua_map.items():
                if gua == target_gua:
                    is_ji = star_name in JI_FANG
                    return json.dumps({
                        "success": True,
                        "命卦": ming_gua,
                        "方位": direction,
                        "对应卦": target_gua,
                        "星名": star_name,
                        "吉凶": "吉" if is_ji else "凶",
                        "含义": self._star_meaning_bazhai(star_name),
                    }, ensure_ascii=False)

            return json.dumps({"success": False, "error": "未找到对应关系"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def xuankong_period(self, year: int) -> str:
        """
        玄空元运：根据年份确定当前所处的三元九运。

        Args:
            year: 年份
        """
        try:
            period_7_end = 2003
            base_period = 7
            base_year = 1864

            total_periods = (year - base_year) // 20
            current_period = (base_period + total_periods - 6) % 9
            if current_period == 0:
                current_period = 9

            period_start = base_year + (total_periods) * 20
            period_end = period_start + 19

            yuan = {1: "上元", 2: "上元", 3: "上元",
                    4: "中元", 5: "中元", 6: "中元",
                    7: "下元", 8: "下元", 9: "下元"}

            return json.dumps({
                "success": True,
                "年份": year,
                "当前运": f"第{current_period}运",
                "三元": yuan.get(current_period, "未知"),
                "运期": f"{period_start}-{period_end}",
                "当运星": current_period,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def xuankong_feixing(self, period: int, facing_direction: str) -> str:
        """
        玄空飞星排盘：根据运数和朝向排出九宫飞星盘。

        Args:
            period: 运数 (1-9)
            facing_direction: 房屋朝向 ("子"=北, "午"=南, "卯"=东, "酉"=西, 
                             "丑"=东北偏北, "寅"=东北偏东, "辰"=东南偏东, "巳"=东南偏南,
                             "未"=西南偏南, "申"=西南偏西, "戌"=西北偏西, "亥"=西北偏北)
        """
        try:
            facing_map = {
                "子": 1, "午": 9, "卯": 3, "酉": 7,
                "丑": 8, "寅": 8, "辰": 4, "巳": 4,
                "未": 2, "申": 2, "戌": 6, "亥": 6,
            }
            facing_num = facing_map.get(facing_direction, 1)

            star_sequence = [period]
            for i in range(8):
                next_star = star_sequence[-1] % 9 + 1
                star_sequence.append(next_star)

            gong_order = ["中", "乾", "兑", "艮", "离", "坎", "坤", "震", "巽"]

            feixing = {}
            for i, gong in enumerate(gong_order):
                feixing[gong] = {
                    "宫位": gong,
                    "山星": star_sequence[i % 9],
                    "向星": star_sequence[(i + facing_num - 1) % 9],
                }

            return json.dumps({
                "success": True,
                "运数": period,
                "朝向": facing_direction,
                "飞星盘": feixing,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def star_meaning(self, star_num: int) -> str:
        """
        飞星含义：查询玄空飞星中某一星曜的含义。

        Args:
            star_num: 星数 (1-9)
        """
        try:
            info = STAR_MEANING.get(star_num)
            if not info:
                return json.dumps({"success": False, "error": f"星数范围1-9"}, ensure_ascii=False)
            return json.dumps({"success": True, "星数": star_num, **info}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def direction_analysis(self, direction: str) -> str:
        """
        方位分析：查询某一方位对应的后天八卦、五行及风水属性。

        Args:
            direction: 方位 ("北", "南", "东", "西", "东北", "东南", "西北", "西南")
        """
        try:
            gua = FANGWEI_BAGUA.get(direction)
            if not gua:
                return json.dumps({"success": False, "error": f"未知方位 '{direction}'"}, ensure_ascii=False)

            gua_info = BAGUA[gua]
            family_map = {"乾": "父亲", "坤": "母亲", "震": "长男", "巽": "长女",
                          "坎": "中男", "离": "中女", "艮": "少男", "兑": "少女"}

            return json.dumps({
                "success": True,
                "方位": direction,
                "对应卦": gua,
                "象": gua_info["象"],
                "五行": gua_info["五行"],
                "洛书数": gua_info["数"],
                "家庭成员": family_map.get(gua, "未知"),
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def wuxing_shape(self, shape: str) -> str:
        """
        五行形煞：根据建筑或地形形状判断五行属性。

        Args:
            shape: 形状 ("方形", "圆形", "长形", "尖形", "波浪形")
        """
        try:
            shape_wx = {
                "方形": {"五行": "土", "特征": "稳重厚实", "影响": "主稳定"},
                "圆形": {"五行": "金", "特征": "圆润流畅", "影响": "主圆满"},
                "长形": {"五行": "木", "特征": "高耸挺拔", "影响": "主生长"},
                "尖形": {"五行": "火", "特征": "尖锐突出", "影响": "主冲动"},
                "波浪形": {"五行": "水", "特征": "流动弯曲", "影响": "主动态"},
            }
            info = shape_wx.get(shape)
            if not info:
                return json.dumps({"success": False, "error": f"未收录 '{shape}'"}, ensure_ascii=False)
            return json.dumps({"success": True, "形状": shape, **info}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def suggest_layout(self, room_type: str, gua_position: str) -> str:
        """
        风水布局建议：根据房间类型和所在宫位给出基本风水布局建议。

        Args:
            room_type: 房间类型 ("大门", "卧室", "厨房", "卫生间", "书房", "客厅", "财位")
            gua_position: 所在宫位/方位 ("北", "南", "东", "西", "东北", "东南", "西北", "西南")
        """
        try:
            suggestions = {
                "大门": {"宜": "方正明亮、开在吉方", "忌": "正对楼梯、电梯、直路冲射"},
                "卧室": {"宜": "安静、方正、床头靠实墙", "忌": "横梁压顶、镜子对床、门冲床"},
                "厨房": {"宜": "通风明亮、水火不相对", "忌": "灶对大门、灶背靠窗"},
                "卫生间": {"宜": "通风干燥、保持清洁", "忌": "正对大门、在房屋中心"},
                "书房": {"宜": "文昌位、背靠实墙、光线充足", "忌": "背门而坐、横梁压顶"},
                "客厅": {"宜": "宽敞明亮、沙发靠实墙", "忌": "穿堂风、开门见阳台"},
                "财位": {"宜": "明亮整洁、放吉祥物或绿植", "忌": "堆放杂物、昏暗污秽"},
            }

            info = suggestions.get(room_type)
            if not info:
                return json.dumps({"success": False, "error": f"未收录 '{room_type}'"}, ensure_ascii=False)

            gua = FANGWEI_BAGUA.get(gua_position, "")
            return json.dumps({
                "success": True,
                "房间": room_type,
                "方位": gua_position,
                "对应卦": gua,
                "宜": info["宜"],
                "忌": info["忌"],
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def _star_meaning_bazhai(self, star: str) -> str:
        meanings = {
            "生气": "最吉方，主生机勃勃，利于求财、生子",
            "天医": "吉方，主健康、治愈，利于祛病",
            "延年": "吉方，主长寿、和谐，利于婚姻人际",
            "伏位": "平稳方，主安定、守成",
            "绝命": "大凶方，主破财、疾病、官非",
            "五鬼": "凶方，主口舌、是非、邪祟",
            "六煞": "凶方，主桃花劫、纠纷",
            "祸害": "小凶方，主疾病、口舌",
        }
        return meanings.get(star, "未知")
