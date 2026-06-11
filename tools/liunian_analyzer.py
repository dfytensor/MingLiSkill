"""
liunian_analyzer.py — 流年决策分析辅助工具
给定出生信息和目标年份，输出详细的流年分析，供 agent 推理使用。
支持：单年分析、多年对比、自动从问题文本检测年份。
"""
from __future__ import annotations

import json
import os
import sys
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.run_tools_engine import (
    eval_year, compute_chart, year_ganzhi_detail, get_dayun_at,
    shen, wuxing_relation,
)
from tools.calendar_engine import (
    TIANGAN, DIZHI, WUXING_GAN, WUXING_ZHI,
    ZHI_CANG_GAN, WUXING_SHENG, year_ganzhi,
)


def extract_years(text: str) -> list[int]:
    """从问题文本中提取年份（4位数字）。"""
    years = []
    for m in re.finditer(r'(1[89]\d{2}|20\d{2})', text):
        y = int(m.group())
        if 1800 <= y <= 2099:
            years.append(y)
    return sorted(set(years))


def analyze_single_year(chart: dict, year: int) -> dict:
    """对单个年份做详细分析，返回人类可读的中文字段。"""
    ev = eval_year(chart, year)
    ln = ev["ln"]
    du = ev.get("du") or {}
    day_gan = ev["day_gan"]

    result = {
        "年份": year,
        "流年干支": f"{ln['gan']}{ln['zhi']}",
        "流年天干": ln["gan"],
        "流年地支": ln["zhi"],
        "天干五行": ln["gan_wx"],
        "地支五行": ln["zhi_wx"],
        "天干十神": ln.get("gan_ss", ""),
        "地支藏干": ln.get("zhi_cang", []),
        "地支藏干十神": ln.get("zhi_cang_ss", []),
        "该年是喜用神年": ln.get("is_yong", False),
        "该年是忌神年": ln.get("is_ji", False),
    }

    if du:
        result["当前大运"] = {
            "大运干支": du.get("ganzhi", ""),
            "起运年龄": du.get("start_age", 0),
            "大运天干十神": du.get("gan_ss", ""),
            "大运是喜用神": du.get("is_yong", False),
            "大运是忌神": du.get("is_ji", False),
        }

    if ev["chong"]:
        result["冲"] = [f"{a}冲{b}({c})" for a, b, c in ev["chong"]]

    if ev["he"]:
        result["合"] = [f"{a}合{b}({c})" for a, b, c in ev["he"]]

    result["流年十神集合"] = list(ev["all_ss"])

    result["喜用神"] = ev["yong"]
    result["忌神"] = ev["ji"]

    return result


def analyze_years(chart: dict, years: list[int]) -> dict:
    """对多年进行对比分析。"""
    results = []
    for y in years:
        results.append(analyze_single_year(chart, y))
    return {
        "日主": chart.get("日主", ""),
        "日主强弱": chart.get("日主强弱", ""),
        "喜用神": chart.get("喜用神", []),
        "忌神": chart.get("忌神", []),
        "四柱": chart.get("四柱", {}),
        "年份分析": results,
    }


def format_year_analysis(chart: dict, year: int) -> str:
    """格式化输出单个年份的分析（人类可读文本）。"""
    a = analyze_single_year(chart, year)
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"  {year}年 流年分析")
    lines.append(f"{'='*60}")
    lines.append(f"  流年干支: {a['流年干支']} (天干{a['天干五行']} / 地支{a['地支五行']})")
    lines.append(f"  天干十神: {a['天干十神']}")
    lines.append(f"  地支藏干: {a['地支藏干']} → 十神: {a['地支藏干十神']}")

    if a.get("当前大运"):
        du = a["当前大运"]
        lines.append(f"  当前大运: {du['大运干支']} (起运{du['起运年龄']}岁) 天干十神: {du['大运天干十神']}")

    tag_yong = "★喜用神年★" if a["该年是喜用神年"] else ""
    tag_ji = "⚠忌神年⚠" if a["该年是忌神年"] else ""
    tag = tag_yong or tag_ji or "平年"
    lines.append(f"  年运属性: {tag}")

    if a.get("冲"):
        lines.append(f"  冲: {'; '.join(a['冲'])} (冲主动荡/变动/冲突)")
    if a.get("合"):
        lines.append(f"  合: {'; '.join(a['合'])} (合主合作/结合/牵绊)")

    lines.append(f"  出现十神: {a['流年十神集合']}")
    return "\n".join(lines)


def format_years_compare(chart: dict, years: list[int]) -> str:
    """格式化多年对比分析。"""
    lines = []
    lines.append(f"\n{'#'*60}")
    lines.append(f"  多年流年对比分析")
    lines.append(f"  日主: {chart.get('日主','')}({chart.get('日主五行','')}) | {chart.get('日主强弱','')}")
    lines.append(f"  喜用: {chart.get('喜用神',[])} | 忌: {chart.get('忌神',[])}")
    lines.append(f"  四柱: {chart.get('四柱',{})}")
    lines.append(f"{'#'*60}")

    for y in years:
        a = analyze_single_year(chart, y)
        tags = []
        if a["该年是喜用神年"]:
            tags.append("喜用")
        if a["该年是忌神年"]:
            tags.append("忌神")
        if a.get("冲"):
            tags.append("冲")
        if a.get("合"):
            tags.append("合")
        tag_str = ",".join(tags) if tags else "—"

        du_info = ""
        if a.get("当前大运"):
            du = a["当前大运"]
            du_info = f" 大运:{du['大运干支']}({du['天干十神']})"

        lines.append(
            f"  {y}: {a['流年干支']} "
            f"天干{a['天干十神']} {a['地支藏干十神']}"
            f"  [{tag_str}]{du_info}"
        )

    return "\n".join(lines)


def integrate_year_analysis(
    year: int, month: int, day: int, hour: int, gender: str,
    question: str, options_json: str,
) -> str:
    """
    自动检测问题中的年份，附加年份分析到排盘数据中。
    这是 analyze_question 的增强版。
    """
    years = extract_years(question)
    if options_json:
        try:
            opts = json.loads(options_json)
            for o in opts:
                years.extend(extract_years(o.get("text", "")))
        except json.JSONDecodeError:
            pass
    years = sorted(set(years))

    bi = {"year": year, "month": month, "day": day, "hour": hour, "gender": gender}
    chart = compute_chart(bi)

    if not years or not chart:
        return json.dumps({
            "note": "未检测到年份或无法排盘",
            "years_detected": years,
        }, ensure_ascii=False)

    analysis = analyze_years(chart, years)

    summary = []
    for a in analysis["年份分析"]:
        y = a["年份"]
        tags = []
        if a["该年是喜用神年"]:
            tags.append("喜用年(吉利)")
        if a["该年是忌神年"]:
            tags.append("忌神年(不利)")
        if a.get("冲"):
            tags.append(f"冲:{', '.join(a['冲'])}")
        if a.get("合"):
            tags.append(f"合:{', '.join(a['合'])}")

        du_str = ""
        if a.get("当前大运"):
            du_str = f" 大运:{a['当前大运']['大运干支']}"

        summary.append({
            "年份": y,
            "干支": f"{a['流年干支']}",
            "天干十神": a["天干十神"],
            "地支藏干十神": a["地支藏干十神"],
            "十神集合": a["流年十神集合"],
            "标签": tags,
            "大运": du_str.strip() if du_str else "",
        })

    return json.dumps({
        "检测到的年份": years,
        "日主": chart.get("日主", ""),
        "日主强弱": chart.get("日主强弱", ""),
        "喜用神": chart.get("喜用神", []),
        "忌神": chart.get("忌神", []),
        "年份流年对比": summary,
    }, ensure_ascii=False)
