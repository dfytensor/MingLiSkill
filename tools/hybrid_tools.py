"""
hybrid_tools.py — 混合路由工具包
工具只提供排盘数据 + 规则引擎建议，最终答案由 agent 推理决定。
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.toolkit_base import Toolkit
from tools.liunian_analyzer import integrate_year_analysis


class HybridMingliToolkit(Toolkit):
    """命理工具包：提供排盘数据和分析建议，agent 做最终推理。"""

    def __init__(self):
        super().__init__(name="hybrid_mingli")
        self._chart_cache = {}

    def analyze_question(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        gender: str,
        category: str,
        question: str,
        options_json: str,
    ) -> str:
        """
        命理分析工具：返回完整排盘数据 + 规则引擎建议。
        最终答案必须由 agent 根据数据推理决定，不可直接采用建议。

        :param year: 出生年（公历）
        :param month: 出生月
        :param day: 出生日
        :param hour: 出生时（0-23）
        :param gender: 性别（男/女）
        :param category: 问题类别（事业/婚姻/财运/健康/子女/学业/家庭/性格/官非/灾劫/外貌/运势）
        :param question: 问题文本
        :param options_json: 选项 JSON，格式 [{"letter":"A","text":"..."},{"letter":"B","text":"..."}]
        :return: JSON 字符串，包含排盘数据、十神分析、规则引擎建议
        """
        try:
            options = json.loads(options_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "options_json 格式错误"}, ensure_ascii=False)

        birth_info = {
            "year": year, "month": month, "day": day,
            "hour": hour, "gender": gender,
        }
        import hashlib
        _case_id = hashlib.md5(
            f"{year}{month}{day}{hour}{gender}".encode()
        ).hexdigest()
        q = {
            "birth_info": birth_info,
            "category": category,
            "question": question,
            "options": options,
            "case_id": _case_id,
        }

        chart_data = self._build_chart_data(q)
        rules_suggestion = self._get_rules_suggestion(q)

        liunian_data = None
        try:
            raw_ln = integrate_year_analysis(
                year=year, month=month, day=day, hour=hour, gender=gender,
                question=question, options_json=options_json,
            )
            ln_parsed = json.loads(raw_ln)
            if ln_parsed.get("年份流年对比"):
                liunian_data = ln_parsed
        except Exception:
            pass

        # Qimen Dunjia integration for year-specific questions
        qimen_data = None
        try:
            from tools.divination_tools import QiMenToolkit
            qm = QiMenToolkit()
            qimen_data = {}
            detected_years = liunian_data.get("检测到的年份", []) if liunian_data else []
            if detected_years:
                for target_year in detected_years:
                    qm_pan = json.loads(qm.build_qimen_pan(year, month, day, hour))
                    if qm_pan.get("success"):
                        qimen_data[str(target_year)] = {
                            "pan": qm_pan,
                            "keji": json.loads(qm.find_qimen_keji(category)),
                        }
        except Exception:
            pass

        result = {
            "category": category,
            "bazi": chart_data.get("bazi", {}),
            "ziwei": chart_data.get("ziwei", {}),
            "career_analysis": chart_data.get("career_analysis"),
            "marriage_analysis": chart_data.get("marriage_analysis"),
            "liunian": liunian_data,
            "qimen": qimen_data,
            "rules_suggestion": rules_suggestion,
            "note": "请根据以上排盘数据，结合命理知识推理出答案。rules_suggestion 仅供参考，不保证正确。",
        }
        # Include all additional analyses from chart_data
        for key in ("health_analysis", "wealth_analysis", "education_analysis",
                     "huoyuan_analysis", "family_analysis"):
            if key in chart_data:
                result[key] = chart_data[key]
        result = {k: v for k, v in result.items() if v is not None}
        return json.dumps(result, ensure_ascii=False)

    def _build_chart_data(self, q: dict) -> dict:
        """构建完整排盘数据。"""
        from tools.tool_integration import build_tool_data
        from engine.run_tools_engine import compute_chart

        bi = q["birth_info"]
        y, m, d, h = bi["year"], bi["month"], bi["day"], bi.get("hour", 12)
        g = bi.get("gender", "男")

        chart = compute_chart(bi)
        tool_data = {}
        try:
            tool_data = build_tool_data(y, m, d, h, g)
        except Exception:
            pass

        result = {}

        if chart:
            result["bazi"] = {
                "日主": chart.get("日主", ""),
                "日主五行": chart.get("日主五行", ""),
                "日主强弱": chart.get("日主强弱", ""),
                "五行力量": chart.get("五行力量", {}),
                "十神": chart.get("十神", {}),
                "喜用神": chart.get("喜用神", []),
                "忌神": chart.get("忌神", []),
                "空亡": chart.get("空亡", ""),
                "纳音": chart.get("纳音", ""),
                "四柱": chart.get("四柱", {}),
                "大运": chart.get("大运", []),
                "日主阴阳": chart.get("日主阴阳", ""),
                "五行占比": chart.get("五行占比", {}),
            }

        if tool_data.get("ziwei"):
            zw = tool_data["ziwei"]
            result["ziwei"] = {
                "命宫主星": tool_data.get("zw_命宫", []),
                "身宫": tool_data.get("zw_body_palace", ""),
                "五行局": tool_data.get("zw_ju", ""),
                "官禄宫主星": tool_data.get("zw_官禄", []),
                "夫妻宫主星": tool_data.get("zw_夫妻", []),
                "财帛宫主星": tool_data.get("zw_财帛", []),
                "疾厄宫主星": tool_data.get("zw_疾厄", []),
                "子女宫主星": tool_data.get("zw_子女", []),
                "迁移宫主星": tool_data.get("zw_迁移", []),
                "父母宫主星": tool_data.get("zw_父母", []),
                "田宅宫主星": tool_data.get("zw_田宅", []),
            }

        if tool_data.get("bz_career"):
            result["career_analysis"] = tool_data["bz_career"]
        if tool_data.get("bz_marriage"):
            result["marriage_analysis"] = tool_data["bz_marriage"]
        if tool_data.get("bz_health"):
            result["health_analysis"] = tool_data["bz_health"]
        if tool_data.get("bz_wealth"):
            result["wealth_analysis"] = tool_data["bz_wealth"]
        if tool_data.get("bz_education"):
            result["education_analysis"] = tool_data["bz_education"]
        if tool_data.get("bz_huoyuan"):
            result["huoyuan_analysis"] = tool_data["bz_huoyuan"]

        # Generate family_analysis from chart data if category needs it
        if q.get("category") == "家庭" and chart:
            pillars = chart.get("四柱", {})
            tg = chart.get("十神", {})
            wx = chart.get("五行力量", {})
            day_gan = chart.get("日主", "")

            # Year pillar = ancestry/family background
            ygz = pillars.get("年柱", "")
            # Month pillar = parents
            mgz = pillars.get("月柱", "")

            # Find father star (偏财 for male, 正财 can also be father)
            father_positions = [k for k, v in tg.items() if v in ("偏财", "正财") and "年" in k]
            # Find mother star (正印 for male, 偏印 can be mother)
            mother_positions = [k for k, v in tg.items() if v in ("正印", "偏印") and ("年" in k or "月" in k)]

            result["family_analysis"] = {
                "年柱": ygz,
                "月柱": mgz,
                "父母星位置_父亲": father_positions,
                "父母星位置_母亲": mother_positions,
                "五行力量": wx,
                "日主强弱": chart.get("日主强弱", ""),
                "喜用神": chart.get("喜用神", []),
            }

        return result

    def _get_rules_suggestion(self, q: dict) -> dict:
        """规则引擎建议（仅供参考）。"""
        from engine.run_tools_engine import predict, compute_chart

        bi = q["birth_info"]
        chart = compute_chart(bi)

        try:
            pred = predict(q, self._chart_cache)
        except Exception:
            pred = "?"

        return {
            "suggested_answer": pred,
            "confidence": "仅供参考，不保证正确",
            "日主": chart.get("日主", ""),
            "日主强弱": chart.get("日主强弱", ""),
            "喜用神": chart.get("喜用神", []),
        }

    def get_bazi_chart(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        gender: str,
    ) -> str:
        """
        获取完整八字排盘数据。

        :param year: 出生年（公历）
        :param month: 出生月
        :param day: 出生日
        :param hour: 出生时（0-23）
        :param gender: 性别（男/女）
        :return: JSON 字符串，包含四柱、五行、十神、喜用神、大运等
        """
        from engine.run_tools_engine import compute_chart

        bi = {"year": year, "month": month, "day": day, "hour": hour, "gender": gender}
        chart = compute_chart(bi)
        if not chart:
            return json.dumps({"error": "无法排盘，请检查出生信息"}, ensure_ascii=False)

        return json.dumps({
            "四柱": chart.get("四柱", {}),
            "日主": chart.get("日主", ""),
            "日主五行": chart.get("日主五行", ""),
            "日主强弱": chart.get("日主强弱", ""),
            "五行力量": chart.get("五行力量", {}),
            "十神": chart.get("十神", {}),
            "喜用神": chart.get("喜用神", []),
            "忌神": chart.get("忌神", []),
            "空亡": chart.get("空亡", ""),
            "纳音": chart.get("纳音", ""),
            "大运": chart.get("大运", []),
        }, ensure_ascii=False)
