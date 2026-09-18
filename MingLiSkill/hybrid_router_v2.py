"""
hybrid_router_v2.py — 类别路由混合策略 v2（基于 57 题严格盲测证据）

证据（pooled, 2026-09-18）：
  agent 强项: 事业40%/性格67%/子女60%/婚姻50%/家庭38%/外貌100%
  agent 弱项: 学业25%(规则75%)/财运17%(规则33%)/健康20%(规则40%)/运势0%(规则100%)

路由规则:
  AGENT_CATEGORIES -> 用 agent 盲测答案（LLM 推理）
  RULES_CATEGORIES -> 用 rules_suggestion（规则引擎，analyze_question 自带）
"""
import json

# agent 显著强于规则引擎的类别
AGENT_CATEGORIES = {"事业", "性格", "子女", "婚姻", "家庭", "外貌"}
# agent 弱于规则引擎的类别（defer）
RULES_CATEGORIES = {"学业", "财运", "健康", "运势"}


def route_answer(category: str, agent_answer: str, rules_suggestion: str) -> tuple:
    """返回 (final_answer, source)。"""
    if category in RULES_CATEGORIES:
        if rules_suggestion:
            return rules_suggestion, "rules"
        return agent_answer, "agent_fallback"
    # agent 类别或未知类别
    return agent_answer, "agent"


def evaluate(charts_path: str, answers_path: str, key: dict):
    """回顾评估：对一组已提交的盲测数据计算混合路由得分。"""
    with open(charts_path, encoding="utf-8") as f:
        charts = {c["id"]: c for c in json.load(f)}
    with open(answers_path, encoding="utf-8") as f:
        mine = json.load(f)

    correct = total = 0
    cat_stats = {}
    detail = []
    for qid, a in mine.items():
        real = key[qid]["answer"]
        cat = key[qid].get("category", "?")
        rs = charts[qid]["chart_data"].get("rules_suggestion", {}).get("suggested_answer", "")
        final, source = route_answer(cat, a["answer"], rs)
        ok = final == real
        total += 1
        correct += ok
        cat_stats.setdefault(cat, {"t": 0, "c": 0, "rules": 0})
        cat_stats[cat]["t"] += 1
        cat_stats[cat]["c"] += ok
        cat_stats[cat]["rules"] += (source == "rules")
        detail.append((qid, cat, a["answer"], rs, final, real, "OK" if ok else "X", source))
    return correct, total, cat_stats, detail
