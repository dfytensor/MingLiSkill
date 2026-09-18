# -*- coding: utf-8 -*-
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from knowledge_base import query_kb, format_kb_results

feats = {"十神": ["伤官", "正官"], "神煞": ["红鸾"], "流年": ["比劫透干"], "宫位": ["配偶宫空亡"]}
res = query_kb(feats)
out = '\n'.join(format_kb_results(res))
with open(r'E:\ming_li_skill\MingLiSkill\kb_test.txt', 'w', encoding='utf-8') as f:
    f.write(out)
print('entries matched: %d' % len(res))
