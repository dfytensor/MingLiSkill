"""
hybrid_router.py — 混合路由策略
按类别选择最优方法（规则引擎 vs LLM+工具），合并生成最终结果。
"""
import json
import sys
import os

RULES_PATH = r"F:\牛逼模型\MingLi-Bench\logs\skill_v3_best.json"
LLM_PATH = r"F:\牛逼模型\MingLi-Bench\logs\enhanced_merged.json"
DATA_PATH = r"F:\牛逼模型\MingLi-Bench\data\data.json"

RULES_CATEGORIES = {"健康", "灾劫", "婚姻", "家庭", "运势", "官非"}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    rules = load_json(RULES_PATH)
    llm = load_json(LLM_PATH)
    data = load_json(DATA_PATH)
    questions = data.get("questions", data if isinstance(data, list) else [])

    rules_by_id = {}
    for item in rules["results"]:
        rules_by_id[item["id"]] = item

    llm_by_id = llm["results"]

    hybrid_results = {}
    cat_stats = {}

    for q in questions:
        qid = q.get("id") or q.get("question_id", "")
        cat = q.get("category", q.get("cat", ""))
        ans = q.get("answer", q.get("ans", ""))

        if not qid or not cat:
            continue

        if cat not in cat_stats:
            cat_stats[cat] = {"total": 0, "correct": 0, "rules_used": 0, "llm_used": 0}

        cat_stats[cat]["total"] += 1

        chosen_pred = None
        method = None

        if cat in RULES_CATEGORIES:
            r = rules_by_id.get(qid)
            if r:
                chosen_pred = r["pred"]
                method = "rules"
                cat_stats[cat]["rules_used"] += 1
            else:
                l = llm_by_id.get(qid)
                if l:
                    chosen_pred = l["pred"]
                    method = "llm_fallback"
                    cat_stats[cat]["llm_used"] += 1
        else:
            l = llm_by_id.get(qid)
            if l:
                chosen_pred = l["pred"]
                method = "llm"
                cat_stats[cat]["llm_used"] += 1
            else:
                r = rules_by_id.get(qid)
                if r:
                    chosen_pred = r["pred"]
                    method = "rules_fallback"
                    cat_stats[cat]["rules_used"] += 1

        if chosen_pred is None:
            continue

        ok = (chosen_pred == ans)
        if ok:
            cat_stats[cat]["correct"] += 1

        hybrid_results[qid] = {
            "pred": chosen_pred,
            "ans": ans,
            "ok": ok,
            "cat": cat,
            "method": method,
        }

    total = len(hybrid_results)
    correct = sum(1 for v in hybrid_results.values() if v["ok"])
    accuracy = correct / total if total else 0

    print(f"\n{'='*60}")
    print(f"  HYBRID ROUTING RESULTS")
    print(f"{'='*60}")
    print(f"  Total:   {total}/160")
    print(f"  Correct: {correct}")
    print(f"  Accuracy: {accuracy*100:.2f}%")
    print(f"{'='*60}")

    print(f"\n{'Category':<8} {'Total':>5} {'Correct':>7} {'Acc%':>6} {'Rules':>6} {'LLM':>4}")
    print("-" * 45)
    for cat in sorted(cat_stats.keys()):
        s = cat_stats[cat]
        acc = s["correct"] / s["total"] * 100 if s["total"] else 0
        print(f"{cat:<8} {s['total']:>5} {s['correct']:>7} {acc:>5.1f}% {s['rules_used']:>6} {s['llm_used']:>4}")

    out = {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "cats": {cat: {"total": s["total"], "correct": s["correct"]} for cat, s in cat_stats.items()},
        "results": hybrid_results,
    }

    out_path = os.path.join(os.path.dirname(RULES_PATH), "hybrid_merged.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
