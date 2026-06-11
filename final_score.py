"""Final validation with all calibrated fixes."""
import json, sys, os

sys.path.insert(0, r'E:\ming_li_skill')
sys.path.insert(0, r'E:\ming_li_skill\engine')

from predict_mingli import predict_with_tools

with open(r'F:\牛逼模型\MingLi-Bench\data\data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

questions = data['questions']
chart_cache, tool_cache = {}, {}
correct, total = 0, 0
cat_stats = {}

for q in questions:
    cat = q.get('category', '')
    pred = predict_with_tools(q, chart_cache, tool_cache)
    real_ans = q['answer']
    ok = pred == real_ans
    total += 1
    correct += ok
    cat_stats.setdefault(cat, {'total': 0, 'correct': 0})
    cat_stats[cat]['total'] += 1
    cat_stats[cat]['correct'] += ok

print('=== FINAL Full 160Q ===')
print(f'Overall: {correct}/{total} = {correct/total*100:.2f}%')
print()
for cat, st in sorted(cat_stats.items()):
    acc = st['correct'] / st['total'] * 100 if st['total'] else 0
    print(f'  {cat}: {st["correct"]}/{st["total"]} = {acc:.1f}%')
