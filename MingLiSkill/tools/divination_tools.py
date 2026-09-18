from __future__ import annotations

import json
import math
import random
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

from .toolkit_base import Toolkit

from .calendar_engine import (
    TIANGAN, DIZHI, TIANGAN_IDX, DIZHI_IDX,
    WUXING_GAN, WUXING_ZHI, year_ganzhi, day_ganzhi_from_date,
    BAGUA, HEXAGRAMS, LIUYAO_LIUQIN, LIUYAO_LIUSHEN,
)

TRIGRAM_LINES = {
    "乾": [1, 1, 1], "兑": [1, 1, 0], "离": [1, 0, 1], "震": [0, 0, 1],
    "巽": [1, 1, 0], "坎": [0, 1, 0], "艮": [1, 0, 0], "坤": [0, 0, 0],
}

YAO_SYMBOL = {0: "⚋", 1: "⚊", 2: "⚏"}

LIUYAO_NAJIA_GAN = {
    "乾": ["壬", "壬", "壬", "壬", "甲", "甲"],
    "坎": ["戊", "戊", "戊", "戊", "戊", "戊"],
    "艮": ["丙", "丙", "丙", "丙", "丙", "丙"],
    "震": ["庚", "庚", "庚", "庚", "庚", "庚"],
    "巽": ["辛", "辛", "辛", "辛", "辛", "辛"],
    "离": ["己", "己", "己", "己", "己", "己"],
    "坤": ["乙", "乙", "乙", "乙", "癸", "癸"],
    "兑": ["丁", "丁", "丁", "丁", "丁", "丁"],
}

LIUYAO_NAJIA_ZHI = {
    "乾": ["子", "寅", "辰", "午", "申", "戌"],
    "坎": ["寅", "辰", "午", "申", "戌", "子"],
    "艮": ["辰", "午", "申", "戌", "子", "寅"],
    "震": ["子", "寅", "辰", "午", "申", "戌"],
    "巽": ["丑", "亥", "酉", "未", "巳", "卯"],
    "离": ["卯", "丑", "亥", "酉", "未", "巳"],
    "坤": ["未", "巳", "卯", "丑", "亥", "酉"],
    "兑": ["巳", "卯", "丑", "亥", "酉", "未"],
}

LIUYAO_LIUQIN_ORDER = ["父母", "兄弟", "子孙", "妻财", "官鬼"]

QIMEN_JIUXING = [
    "天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英",
]
QIMEN_BAMEN = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]
QIMEN_BASHEN = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
QIMEN_JIUGONG = [1, 2, 3, 4, 5, 6, 7, 8, 9]
QIMEN_GONG_POSITIONS = {
    1: (0, 2), 2: (0, 1), 3: (0, 0),
    4: (1, 2), 5: (1, 1), 6: (1, 0),
    7: (2, 2), 8: (2, 1), 9: (2, 0),
}


class LiuYaoToolkit(Toolkit):
    def __init__(self, **kwargs):
        tools = [
            self.cast_hexagram,
            self.analyze_hexagram,
            self.load_najia,
            self.find_yong_shen,
            self.check_sheng_ke,
            self.interpret_result,
        ]
        super().__init__(name="liuyao_tools", tools=tools, **kwargs)

    def cast_hexagram(self, method: str = "三硬币法", coins: str = "") -> str:
        """
        起六爻卦：使用三硬币法或数字法起出一个六爻卦象。

        Args:
            method: 起卦方法 ("三硬币法" 或 "数字法")
            coins: 六次摇币结果，每次三个数字用逗号分隔，六次用分号分隔。
                   数字含义：2=字(阳) 3=背(阴)。如 "2,2,3;1,2,3;2,3,3;2,2,2;1,3,3;2,2,3"
                   留空则自动随机生成。
        """
        try:
            if coins.strip():
                groups = coins.split(";")
                if len(groups) != 6:
                    return json.dumps({"success": False, "error": "需要6组数据，用分号分隔"}, ensure_ascii=False)
                yao_values = []
                for g in groups:
                    nums = [int(x.strip()) for x in g.split(",")]
                    total = sum(nums)
                    yao_values.append(total)
            else:
                yao_values = []
                for _ in range(6):
                    coins_list = [random.choice([2, 3]) for _ in range(3)]
                    yao_values.append(sum(coins_list))

            yaos = []
            for val in yao_values:
                if val % 2 == 0:
                    yao_type = "阳"
                    is_changing = (val == 6)
                else:
                    yao_type = "阴"
                    is_changing = (val == 9)
                yaos.append({"value": val, "type": yao_type, "changing": is_changing})

            lower = [1 if y["type"] == "阳" else 0 for y in yaos[:3]]
            upper = [1 if y["type"] == "阳" else 0 for y in yaos[3:]]
            lower_gua = self._match_trigram(lower)
            upper_gua = self._match_trigram(upper)

            hex_num = self._trigrams_to_hexagram(upper_gua, lower_gua)
            hex_name = HEXAGRAMS.get(hex_num, f"第{hex_num}卦")

            changed_yaos = [i for i, y in enumerate(yaos) if y["changing"]]
            if changed_yaos:
                changed_lower = list(lower)
                changed_upper = list(upper)
                for idx in changed_yaos:
                    if idx < 3:
                        changed_lower[idx] = 1 - changed_lower[idx]
                    else:
                        changed_upper[idx - 3] = 1 - changed_upper[idx - 3]
                changed_lower_gua = self._match_trigram(changed_lower)
                changed_upper_gua = self._match_trigram(changed_upper)
                changed_hex_num = self._trigrams_to_hexagram(changed_upper_gua, changed_lower_gua)
                changed_hex_name = HEXAGRAMS.get(changed_hex_num, f"第{changed_hex_num}卦")
            else:
                changed_hex_name = "无变卦"
                changed_hex_num = 0

            return json.dumps({
                "success": True,
                "本卦": hex_name,
                "卦序": hex_num,
                "上卦": upper_gua,
                "下卦": lower_gua,
                "变卦": changed_hex_name,
                "变卦序": changed_hex_num,
                "六爻": [{"爻位": i+1, **y} for i, y in enumerate(yaos)],
                "动爻位置": [i+1 for i, y in enumerate(yaos) if y["changing"]],
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def analyze_hexagram(self, hexagram_name: str, question_type: str = "通用") -> str:
        """
        分析卦象含义：查询六十四卦的基本含义。

        Args:
            hexagram_name: 卦名 (如 "乾", "泰", "既济")
            question_type: 问题类型 ("事业", "婚姻", "财运", "健康", "通用")
        """
        try:
            hex_info = {
                "乾": {"象": "天行健，君子以自强不息", "吉凶": "吉", "含义": "刚健中正，万物之始"},
                "坤": {"象": "地势坤，君子以厚德载物", "吉凶": "吉", "含义": "柔顺包容，厚德载物"},
                "屯": {"象": "云雷屯，君子以经纶", "吉凶": "小凶", "含义": "初创艰难，需坚持"},
                "蒙": {"象": "山下出泉，蒙", "吉凶": "平", "含义": "启蒙教化，需引导"},
                "需": {"象": "云上于天，需", "吉凶": "平", "含义": "等待时机，守正则吉"},
                "讼": {"象": "天与水违行，讼", "吉凶": "凶", "含义": "争讼不宜，宜和解"},
                "泰": {"象": "天地交，泰", "吉凶": "大吉", "含义": "上下通泰，万物通"},
                "否": {"象": "天地不交，否", "吉凶": "大凶", "含义": "闭塞不通，需隐忍"},
                "既济": {"象": "水在火上，既济", "吉凶": "吉", "含义": "事已成就，守成为要"},
                "未济": {"象": "火在水上，未济", "吉凶": "平", "含义": "事未完成，仍需努力"},
            }
            info = hex_info.get(hexagram_name, {"象": "未收录", "吉凶": "未知", "含义": "待查"})

            return json.dumps({
                "success": True,
                "卦名": hexagram_name,
                "问题类型": question_type,
                **info,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def load_najia(self, upper_gua: str, lower_gua: str, day_ganzhi: str) -> str:
        """
        装卦纳甲：为六爻卦装配纳甲（天干地支）、六亲、六神。

        Args:
            upper_gua: 上卦名 (如 "乾", "坤")
            lower_gua: 下卦名 (如 "坎", "离")
            day_ganzhi: 测卦日的干支 (如 "甲子")
        """
        try:
            lines = []
            for i in range(6):
                if i < 3:
                    gua = lower_gua
                    pos = i
                else:
                    gua = upper_gua
                    pos = i - 3

                gan_list = LIUYAO_NAJIA_GAN.get(gua, ["?"] * 6)
                zhi_list = LIUYAO_NAJIA_ZHI.get(gua, ["?"] * 6)
                gan = gan_list[pos]
                zhi = zhi_list[pos]
                wx = WUXING_ZHI.get(zhi, "?")

                liuqin = self._get_liuqin(day_ganzhi[0], zhi)
                liushen_idx = DIZHI_IDX.get(day_ganzhi[1], 0) % 6
                liushen = LIUYAO_LIUSHEN[(liushen_idx + i) % 6]

                lines.append({
                    "爻位": 6 - i,
                    "纳甲": f"{gan}{zhi}",
                    "地支": zhi,
                    "五行": wx,
                    "六亲": liuqin,
                    "六神": liushen,
                })

            return json.dumps({"success": True, "纳甲六爻": lines}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def find_yong_shen(self, question_type: str) -> str:
        """
        取用神：根据所问事项确定六爻预测中的用神（六亲）。

        Args:
            question_type: 问题类型 ("父母", "兄弟", "子孙", "妻财", "官鬼",
                          "事业", "婚姻女", "婚姻男", "考试", "疾病", "失物", "官司")
        """
        try:
            yongshen_map = {
                "父母": "父母爻", "兄弟": "兄弟爻", "子孙": "子孙爻",
                "妻财": "妻财爻", "官鬼": "官鬼爻",
                "事业": "官鬼爻", "婚姻女": "官鬼爻", "婚姻男": "妻财爻",
                "考试": "父母爻", "疾病": "官鬼爻", "失物": "妻财爻",
                "官司": "官鬼爻", "房屋": "父母爻", "出行": "官鬼爻",
                "求财": "妻财爻", "子嗣": "子孙爻",
            }
            ys = yongshen_map.get(question_type, "官鬼爻")
            yuan_shen = {"父母爻": "兄弟爻", "兄弟爻": "父母爻", "子孙爻": "兄弟爻",
                         "妻财爻": "子孙爻", "官鬼爻": "妻财爻"}
            ji_shen = {"父母爻": "子孙爻", "兄弟爻": "官鬼爻", "子孙爻": "官鬼爻",
                       "妻财爻": "兄弟爻", "官鬼爻": "子孙爻"}

            return json.dumps({
                "success": True,
                "问题类型": question_type,
                "用神": ys,
                "原神": yuan_shen.get(ys, "未知"),
                "忌神": ji_shen.get(ys, "未知"),
                "仇神": "克原神、生忌神者",
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def check_sheng_ke(self, yong_wuxing: str, yao_wuxing: str) -> str:
        """
        查五行生克：判断用神与爻之间的五行生克关系。

        Args:
            yong_wuxing: 用神五行 (如 "木")
            yao_wuxing: 爻五行 (如 "金")
        """
        try:
            from .calendar_engine import WUXING_SHENG, WUXING_KE
            if yong_wuxing == yao_wuxing:
                rel = "比和"
            elif WUXING_SHENG.get(yao_wuxing) == yong_wuxing:
                rel = "爻生用神（有益）"
            elif WUXING_SHENG.get(yong_wuxing) == yao_wuxing:
                rel = "用神生爻（泄气）"
            elif WUXING_KE.get(yao_wuxing) == yong_wuxing:
                rel = "爻克用神（不利）"
            elif WUXING_KE.get(yong_wuxing) == yao_wuxing:
                rel = "用神克爻（有利）"
            else:
                rel = "无关"

            return json.dumps({
                "success": True,
                "用神五行": yong_wuxing,
                "爻五行": yao_wuxing,
                "关系": rel,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def interpret_result(self, yong_shen_status: str, dong_yao_count: int) -> str:
        """
        断卦原则：根据用神状态和动爻数量给出初步判断框架。

        Args:
            yong_shen_status: 用神状态 ("旺相", "休囚", "受克", "空亡", "伏藏")
            dong_yao_count: 动爻数量 (0-6)
        """
        try:
            status_interpret = {
                "旺相": "用神有力，事可成",
                "休囚": "用神无力，需等待时机",
                "受克": "用神受克，事多阻碍",
                "空亡": "用神空亡，事多虚幻或延迟",
                "伏藏": "用神伏藏，需寻找方可成",
            }

            dong_interpret = {
                0: "无动爻，以卦辞断",
                1: "一个动爻，以该爻爻辞断",
                2: "两个动爻，以上面动爻爻辞为主",
                3: "三个动爻，以本卦卦辞为主",
                4: "四个动爻，以变卦中不变爻断",
                5: "五个动爻，以变卦中不变爻断",
                6: "六个动爻，乾坤特殊断法，余以变卦断",
            }

            return json.dumps({
                "success": True,
                "用神状态": yong_shen_status,
                "用神解读": status_interpret.get(yong_shen_status, "待分析"),
                "动爻数": dong_yao_count,
                "断卦法则": dong_interpret.get(dong_yao_count, "待分析"),
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def _match_trigram(self, lines: List[int]) -> str:
        trigram_map = {
            (1, 1, 1): "乾", (0, 0, 0): "坤", (1, 0, 0): "震",
            (0, 1, 1): "巽", (0, 1, 0): "坎", (1, 0, 1): "离",
            (1, 1, 0): "兑", (0, 0, 1): "艮",
        }
        return trigram_map.get(tuple(lines), "乾")

    def _trigrams_to_hexagram(self, upper: str, lower: str) -> int:
        upper_map = {"坤": 0, "震": 1, "坎": 2, "兑": 3, "艮": 4, "离": 5, "巽": 6, "乾": 7}
        lower_map = {"坤": 0, "震": 8, "坎": 16, "兑": 24, "艮": 32, "离": 40, "巽": 48, "乾": 56}
        idx = upper_map.get(upper, 0) + lower_map.get(lower, 0)
        return idx + 1

    def _get_liuqin(self, day_gan: str, zhi: str) -> str:
        day_wx = WUXING_GAN[day_gan]
        zhi_wx = WUXING_ZHI[zhi]
        wx_order = ["木", "火", "土", "金", "水"]
        lq_order = LIUYAO_LIUQIN_ORDER

        day_idx = wx_order.index(day_wx)
        zhi_idx = wx_order.index(zhi_wx)
        diff = (zhi_idx - day_idx) % 5
        return lq_order[diff]


class MeiHuaToolkit(Toolkit):
    def __init__(self, **kwargs):
        tools = [
            self.cast_meihua,
            self.analyze_ti_yong,
            self.interpret_wuxing_relation,
        ]
        super().__init__(name="meihua_tools", tools=tools, **kwargs)

    def cast_meihua(self, number1: int, number2: int, year: int = 0,
                    month: int = 0, day: int = 0) -> str:
        """
        梅花易数起卦：根据两个数字（或时间）起出上卦和下卦。

        Args:
            number1: 第一数（起上卦）
            number2: 第二数（起下卦）
            year: 年份（可选，用于计算动爻）
            month: 月份（可选）
            day: 日期（可选）
        """
        try:
            upper_idx = number1 % 8
            if upper_idx == 0:
                upper_idx = 8
            lower_idx = number2 % 8
            if lower_idx == 0:
                lower_idx = 8

            gua_map = {1: "乾", 2: "兑", 3: "离", 4: "震", 5: "巽", 6: "坎", 7: "艮", 8: "坤"}
            upper_gua = gua_map[upper_idx]
            lower_gua = gua_map[lower_idx]

            if year and month and day:
                dong_yao = (year + month + day + number1 + number2) % 6
                if dong_yao == 0:
                    dong_yao = 6
            else:
                dong_yao = (number1 + number2) % 6
                if dong_yao == 0:
                    dong_yao = 6

            upper_wx = BAGUA[upper_gua]["五行"]
            lower_wx = BAGUA[lower_gua]["五行"]

            return json.dumps({
                "success": True,
                "上卦": upper_gua,
                "上卦五行": upper_wx,
                "上卦象": BAGUA[upper_gua]["象"],
                "下卦": lower_gua,
                "下卦五行": lower_wx,
                "下卦象": BAGUA[lower_gua]["象"],
                "动爻": dong_yao,
                "上卦数": upper_idx,
                "下卦数": lower_idx,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def analyze_ti_yong(self, upper_gua: str, lower_gua: str, dong_yao: int) -> str:
        """
        分析体用关系：根据梅花易数的动爻确定体卦和用卦，分析体用五行生克。

        Args:
            upper_gua: 上卦名
            lower_gua: 下卦名
            dong_yao: 动爻位置 (1-6, 1-3为下卦，4-6为上卦)
        """
        try:
            if dong_yao <= 3:
                ti_gua = upper_gua
                yong_gua = lower_gua
            else:
                ti_gua = lower_gua
                yong_gua = upper_gua

            ti_wx = BAGUA[ti_gua]["五行"]
            yong_wx = BAGUA[yong_gua]["五行"]

            from .calendar_engine import WUXING_SHENG, WUXING_KE
            if ti_wx == yong_wx:
                relation = "比和"
                judge = "中性，力量相当"
            elif WUXING_SHENG.get(yong_wx) == ti_wx:
                relation = "用生体"
                judge = "大吉，有助益"
            elif WUXING_KE.get(yong_wx) == ti_wx:
                relation = "用克体"
                judge = "不吉，有阻碍"
            elif WUXING_SHENG.get(ti_wx) == yong_wx:
                relation = "体生用"
                judge = "泄气，精力消耗"
            elif WUXING_KE.get(ti_wx) == yong_wx:
                relation = "体克用"
                judge = "劳而有获"
            else:
                relation = "无关"
                judge = "待分析"

            return json.dumps({
                "success": True,
                "体卦": ti_gua,
                "体卦五行": ti_wx,
                "用卦": yong_gua,
                "用卦五行": yong_wx,
                "体用关系": relation,
                "判断": judge,
                "动爻": dong_yao,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def interpret_wuxing_relation(self, wx1: str, wx2: str) -> str:
        """
        解读五行关系：判断两个五行之间的生克关系。

        Args:
            wx1: 第一个五行 (如 "木")
            wx2: 第二个五行 (如 "火")
        """
        try:
            from .calendar_engine import WUXING_SHENG, WUXING_KE
            if wx1 == wx2:
                rel = "比和"
            elif WUXING_SHENG.get(wx1) == wx2:
                rel = f"{wx1}生{wx2}"
            elif WUXING_SHENG.get(wx2) == wx1:
                rel = f"{wx2}生{wx1}"
            elif WUXING_KE.get(wx1) == wx2:
                rel = f"{wx1}克{wx2}"
            elif WUXING_KE.get(wx2) == wx1:
                rel = f"{wx2}克{wx1}"
            else:
                rel = "无关"

            return json.dumps({
                "success": True,
                "五行1": wx1,
                "五行2": wx2,
                "关系": rel,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})


class QiMenToolkit(Toolkit):
    def __init__(self, **kwargs):
        tools = [
            self.build_qimen_pan,
            self.analyze_qimen_geju,
            self.find_qimen_keji,
        ]
        super().__init__(name="qimen_tools", tools=tools, **kwargs)

    def build_qimen_pan(self, year: int, month: int, day: int, hour: int) -> str:
        """
        排奇门遁甲盘：根据公历时间排出奇门遁甲九宫格局（简化版时家奇门）。

        Args:
            year: 公历年份
            month: 月份
            day: 日期
            hour: 时辰 (0-23)
        """
        try:
            from .calendar_engine import _hour_to_zhi, ganzhi_from_offset
            hour_zhi = _hour_to_zhi(hour)

            day_gz = day_ganzhi_from_date(date(year, month, day))
            day_gan_idx = TIANGAN_IDX[day_gz[0]]
            day_zhi_idx = DIZHI_IDX[day_gz[1]]

            fu_tou = day_gan_idx % 9
            current_jieqi = self._get_jieqi(month, day)

            yang_dun = month in (12, 1, 2, 3, 4, 5, 6)
            ju = (fu_tou + day_zhi_idx) % 9 + 1

            jiuxing_positions = list(range(9))
            bamen_offset = (day_zhi_idx) % 8
            bashen_offset = hour_zhi % 8

            gong_data = {}
            for i in range(9):
                gong_num = i + 1
                xing = QIMEN_JIUXING[(i + fu_tou) % 9]
                men = QIMEN_BAMEN[(i + bamen_offset) % 8]
                shen = QIMEN_BASHEN[(i + bashen_offset) % 8] if i < 8 else "天禽"

                gong_data[gong_num] = {
                    "九星": xing,
                    "八门": men,
                    "八神": shen,
                    "宫位": gong_num,
                }

            return json.dumps({
                "success": True,
                "时间": f"{year}-{month}-{day} {hour}时",
                "日干支": day_gz,
                "节气": current_jieqi,
                "局数": ju,
                "阴阳遁": "阳遁" if yang_dun else "阴遁",
                "值符": TIANGAN[fu_tou],
                "九宫布局": gong_data,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def analyze_qimen_geju(self, geju_name: str) -> str:
        """
        分析奇门格局：查询常见奇门格局的含义。

        Args:
            geju_name: 格局名称 (如 "吉格", "凶格", "伏吟", "反吟", "马星")
        """
        try:
            geju_info = {
                "吉格": ["天遁", "地遁", "人遁", "神遁", "龙遁", "虎遁", "风遁", "云遁"],
                "凶格": ["大格", "小格", "刑格", "悖格", "飞宫格", "时格"],
                "伏吟": "星门不动，主停滞、等待",
                "反吟": "星门对冲，主反复、变动",
                "马星": "主动态、奔波、变化",
                "空亡": "主虚、不成、待填实",
                "击刑": "主灾祸、意外",
                "入墓": "主暗昧、困顿",
            }
            info = geju_info.get(geju_name, "未收录此格局")
            return json.dumps({
                "success": True,
                "格局": geju_name,
                "含义": info if isinstance(info, str) else info,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def find_qimen_keji(self, question_type: str) -> str:
        """
        奇门用神取法：根据所问事项确定奇门遁甲中的用神宫位。

        Args:
            question_type: 问题类型 ("事业", "婚姻", "求财", "出行", "官司", "考试", "失物", "疾病")
        """
        try:
            keji_map = {
                "事业": {"用神": "开门", "辅助": "生门、官星", "说明": "开门主事业，看落宫吉凶"},
                "婚姻": {"用神": "六合", "辅助": "乙奇、庚奇", "说明": "六合主婚姻，乙为女庚为男"},
                "求财": {"用神": "生门", "辅助": "戊、甲子戊", "说明": "生门主财运，戊主资本"},
                "出行": {"用神": "驿马星", "辅助": "日干落宫", "说明": "看出行方向吉凶"},
                "官司": {"用神": "惊门", "辅助": "值符、值使", "说明": "惊门主口舌是非"},
                "考试": {"用神": "景门", "辅助": "天辅星", "说明": "景门主文章，天辅主考运"},
                "失物": {"用神": "玄武", "辅助": "时干落宫", "说明": "玄武主盗贼失物"},
                "疾病": {"用神": "天芮星", "辅助": "死门", "说明": "天芮主病，死门主凶"},
            }
            info = keji_map.get(question_type, {"用神": "日干", "辅助": "时干", "说明": "通用参考"})
            return json.dumps({"success": True, "问题类型": question_type, **info}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def _get_jieqi(self, month: int, day: int) -> str:
        jieqi_table = [
            (1, 6, "小寒"), (1, 20, "大寒"), (2, 4, "立春"), (2, 19, "雨水"),
            (3, 6, "惊蛰"), (3, 21, "春分"), (4, 5, "清明"), (4, 20, "谷雨"),
            (5, 6, "立夏"), (5, 21, "小满"), (6, 6, "芒种"), (6, 21, "夏至"),
            (7, 7, "小暑"), (7, 23, "大暑"), (8, 7, "立秋"), (8, 23, "处暑"),
            (9, 8, "白露"), (9, 23, "秋分"), (10, 8, "寒露"), (10, 23, "霜降"),
            (11, 7, "立冬"), (11, 22, "小雪"), (12, 7, "大雪"), (12, 22, "冬至"),
        ]
        current = "冬至"
        for m, d, name in jieqi_table:
            if (month, day) >= (m, d):
                current = name
        return current


class LiuRenToolkit(Toolkit):
    def __init__(self, **kwargs):
        tools = [
            self.build_liuren_pan,
            self.analyze_sike,
            self.analyze_sanchuan,
        ]
        super().__init__(name="liuren_tools", tools=tools, **kwargs)

    def build_liuren_pan(self, year: int, month: int, day: int, hour: int) -> str:
        """
        排大六壬四课三传：根据公历时间排出大六壬天地盘、四课和三传。

        Args:
            year: 公历年份
            month: 月份
            day: 日期
            hour: 时辰 (0-23)
        """
        try:
            from .calendar_engine import _hour_to_zhi, ganzhi_from_offset

            day_gz = day_ganzhi_from_date(date(year, month, day))
            day_gan = day_gz[0]
            day_zhi = day_gz[1]
            hour_zhi_idx = _hour_to_zhi(hour)
            hour_zhi = DIZHI[hour_zhi_idx]

            month_jiang_map = {
                0: "丑", 1: "子", 2: "亥", 3: "戌", 4: "酉", 5: "申",
                6: "未", 7: "午", 8: "巳", 9: "辰", 10: "卯", 11: "寅",
            }
            month_num = (month - 1) % 12
            yue_jiang = month_jiang_map[month_num]

            ti_pan = list(DIZHI)
            di_pan = list(DIZHI)
            tian_pan = [DIZHI[(DIZHI_IDX[z] + DIZHI_IDX[yue_jiang]) % 12] for z in ti_pan]

            sike = self._build_sike(day_gan, day_zhi, tian_pan, ti_pan)
            sanchuan = self._build_sanchuan(sike)

            return json.dumps({
                "success": True,
                "日干支": day_gz,
                "时辰": hour_zhi,
                "月将": yue_jiang,
                "天盘": tian_pan,
                "地盘": ti_pan,
                "四课": sike,
                "三传": sanchuan,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def analyze_sike(self, sike_json: str) -> str:
        """
        分析四课：解读大六壬四课的含义。

        Args:
            sike_json: 四课数据的 JSON 字符串
        """
        try:
            sike = json.loads(sike_json)
            analysis = []
            for ke in sike:
                analysis.append({
                    "课名": ke.get("name", ""),
                    "上神": ke.get("upper", ""),
                    "下神": ke.get("lower", ""),
                    "关系": "上克下" if ke.get("relation") == "ke_down" else
                             "下克上" if ke.get("relation") == "ke_up" else
                             "上生下" if ke.get("relation") == "sheng_down" else
                             "下生上" if ke.get("relation") == "sheng_up" else "比和",
                })
            return json.dumps({"success": True, "四课分析": analysis}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def analyze_sanchuan(self, sanchuan_json: str) -> str:
        """
        分析三传：解读大六壬三传（初传、中传、末传）的含义。

        Args:
            sanchuan_json: 三传数据的 JSON 字符串
        """
        try:
            sc = json.loads(sanchuan_json)
            return json.dumps({
                "success": True,
                "初传": sc.get("first", ""),
                "中传": sc.get("second", ""),
                "末传": sc.get("third", ""),
                "说明": "初传主事始，中传主事中，末传主事终",
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def _build_sike(self, day_gan: str, day_zhi: str, tian_pan: list, ti_pan: list) -> list:
        from .calendar_engine import WUXING_GAN, WUXING_ZHI, WUXING_KE
        gan_zhi_map = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
                       "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
        day_gan_zhi = gan_zhi_map.get(day_gan, "寅")

        sike = []
        pairs = [
            ("日干阳神", day_gan_zhi, day_gan),
            ("日干阴神", "", day_gan),
            ("日支阳神", day_zhi, day_zhi),
            ("日支阴神", "", day_zhi),
        ]

        for name, base, ref in pairs:
            if not base:
                base = day_zhi
            idx = DIZHI_IDX.get(base, 0)
            upper = tian_pan[idx]
            lower = base
            upper_wx = WUXING_ZHI.get(upper, "土")
            lower_wx = WUXING_ZHI.get(lower, "土")

            if upper_wx == lower_wx:
                rel = "bihe"
            elif WUXING_KE.get(upper_wx) == lower_wx:
                rel = "ke_down"
            elif WUXING_KE.get(lower_wx) == upper_wx:
                rel = "ke_up"
            else:
                rel = "sheng"

            sike.append({"name": name, "upper": upper, "lower": lower, "relation": rel})

        return sike

    def _build_sanchuan(self, sike: list) -> dict:
        chuan_list = []
        for ke in sike:
            if ke["relation"] in ("ke_down", "ke_up"):
                chuan_list.append(ke["upper"])

        first = chuan_list[0] if len(chuan_list) > 0 else sike[0]["upper"]
        first_idx = DIZHI_IDX.get(first, 0)
        second = DIZHI[(first_idx + 4) % 12]
        third = DIZHI[(first_idx + 8) % 12]

        return {"first": first, "second": second, "third": third}
