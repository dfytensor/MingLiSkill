"""
MingLi-Bench Unified Predictor v4 — Standalone
Combines: Bazi rules engine + Tool data + (optional) LLM
Location: E:\\ming_li_skill\\predict_mingli.py
"""
from __future__ import annotations
import json, os, sys, time, re, random, argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from run_tools_engine import (
    predict, compute_chart, score_option_v2, _score_chart_level,
    eval_year, extract_question_year, extract_years_from_options,
    year_ganzhi, ZHI_CANG_GAN, shen, _smart_tiebreak,
)
from tools.tool_integration import build_tool_data
from tools.calendar_engine import WUXING_GAN


def _enhanced_career_score(text, chart, td):
    s = 0.0
    day_wx = chart["日主五行"]
    strong = chart["日主强弱"] == "身强"
    tg = chart["十神"]
    tg_set = set(tg.values())

    EXTRA_PROFS = {
        "正印": ["护士", "社工", "家教", "幼师"],
        "偏印": ["技工", "修理", "维修", "占卜"],
        "食神": ["餐饮", "食品", "厨师", "烘焙", "饮料", "矿泉水", "茶", "休闲",
                  "儿童培训", "幼教", "才艺"],
        "伤官": ["设计", "广告", "媒体", "记者", "编剧", "导演", "主持人"],
        "偏财": ["房地产", "中介", "代理", "外贸", "进出口", "证券", "投资"],
        "正财": ["出纳", "收银", "统计", "仓管", "质检"],
        "比肩": ["工人", "工厂", "生产线", "操作工"],
        "劫财": ["推销", "业务员", "直销"],
        "正官": ["公务员", "干部", "主任", "局长", "科长"],
        "七杀": ["保安", "城管", "飞行员", "导游"],
    }
    for ss_name, profs in EXTRA_PROFS.items():
        if ss_name in tg_set:
            for p in profs:
                if p in text:
                    s += 1.5

    gender = chart.get("gender", "男")
    if "主妇" in text or "家庭主妇" in text or "全职太太" in text:
        if gender in ("女", "F", "female") and not strong:
            s += 3.0
    if "打工" in text and ("稳定" in text or "收入" in text):
        if "正财" in tg_set or "正官" in tg_set:
            s += 1.5
    if "稳定" in text and ("工作" in text or "职业" in text):
        if "正官" in tg_set or "正印" in tg_set or "正财" in tg_set:
            s += 1.5
    if "管理岗" in text or "管理层" in text:
        if strong and "正官" in tg_set:
            s += 2.0
    return s


def _enhanced_wealth_score(text, chart):
    s = 0.0
    strong = chart["日主强弱"] == "身强"
    tg = chart["十神"]
    tg_set = set(tg.values())
    wx = chart["五行力量"]

    has_w = "正财" in tg_set or "偏财" in tg_set
    has_r = "比肩" in tg_set or "劫财" in tg_set

    if "千万" in text or "亿万" in text:
        if strong and has_w and not has_r:
            s += 3.0
        else:
            s -= 1.5
    if "百万" in text or "100万" in text:
        if has_w:
            s += 2.0
    if "几千" in text or "千" in text:
        if not strong or has_r:
            s += 1.5
    if "负债" in text or "欠" in text:
        if has_r and not strong:
            s += 2.0
    return s


def predict_with_tools(q, chart_cache, tool_cache):
    bi = q.get("birth_info", {})
    cat = q.get("category", "运势")
    options = q.get("options", [])
    q_text = q.get("question", "")

    cid = q.get("case_id", "")
    if cid not in chart_cache:
        chart_cache[cid] = compute_chart(bi)
    chart = chart_cache[cid]

    if cid not in tool_cache:
        y, m, d, h = bi.get("year"), bi.get("month"), bi.get("day"), bi.get("hour") or 12
        g = bi.get("gender") or "男"
        tool_cache[cid] = build_tool_data(y, m, d, h, g) if y and m and d else {}
    td = tool_cache[cid]

    if not chart:
        return random.choice([o["letter"] for o in options]) if options else "A"

    # Delegate to the unified predict() in run_tools_engine which has all fixes
    cat_map = {
        "运势": True, "事业": True, "婚姻": True, "财运": True,
        "健康": True, "子女": True, "学业": True, "家庭": True,
        "性格": True, "官非": True, "灾劫": True, "外貌": True,
    }
    # Only use enhanced scores for non-year-selection事业/财运
    q_year = extract_question_year(q_text)
    opt_years = extract_years_from_options(options)
    is_year_selection = len(opt_years) >= 2 and all(o.get("letter") in opt_years for o in options)

    # Use the unified predict() from run_tools_engine for all cases
    pred = predict(q, chart_cache)
    
    # Apply enhanced career/wealth scoring for non-year questions
    if pred and not is_year_selection and not q_year:
        scores = {}
        for o in options:
            letter = o["letter"]
            text = o.get("text", "")
            s = _score_chart_level(text, chart, cat, ziwei_data=td)
            if cat == "事业":
                s += _enhanced_career_score(text, chart, td)
            elif cat == "财运":
                s += _enhanced_wealth_score(text, chart)
            scores[letter] = s
        if scores:
            return max(scores, key=scores.get)

    return pred


def run_batch(data_file, output_file=None):
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = data.get("questions", data) if isinstance(data, dict) else data
    chart_cache, tool_cache, results = {}, {}, []
    correct, total, cat_stats = 0, 0, {}

    for q in questions:
        pred = predict_with_tools(q, chart_cache, tool_cache)
        ans = q.get("answer", "")
        cat = q.get("category", "未知")
        ok = pred == ans
        correct += ok; total += 1
        cat_stats.setdefault(cat, {"total": 0, "correct": 0})
        cat_stats[cat]["total"] += 1; cat_stats[cat]["correct"] += ok
        results.append({"id": q.get("id", ""), "category": cat, "pred": pred, "ans": ans, "ok": ok})

    output = {"overall": correct / total if total else 0, "correct": correct, "total": total,
              "cats": cat_stats, "results": results}
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    for cat, st in sorted(cat_stats.items()):
        a = st["correct"] / st["total"] if st["total"] else 0
        print(f"  {cat}: {a:.2%} ({st['correct']}/{st['total']})")
    print(f"\nOverall: {correct}/{total} = {correct/total:.2%}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", help="Batch data JSON file")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()
    if args.batch:
        run_batch(args.batch, args.output)
    else:
        print("Use --batch <file>")
