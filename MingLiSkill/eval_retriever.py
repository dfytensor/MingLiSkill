# -*- coding: utf-8 -*-
"""Leave-one-out evaluation of the case retriever (BM25 top1 / top3-vote)."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from retriever import Retriever
from collections import Counter

r = Retriever()
n = loo1 = loo3 = 0
detail = []
for c in r.cases:
    n += 1
    hits = r.search_cases(c['question'] + ' ' + c['options_text'], top_k=3, exclude_qid=c['qid'])
    same_cat = [h for h in hits if h['case']['cat'] == c['cat']]
    pool = same_cat or hits
    pick = pool[0]['case'] if pool else None
    top1_ok = bool(pick and pick['answer'] == c['answer'])
    loo1 += top1_ok
    votes = Counter(h['case']['answer'] for h in pool[:3])
    maj = votes.most_common(1)[0][0] if votes else None
    loo3 += (maj == c['answer'])
    detail.append('%s [%s] real=%s pick=%s(%s) %s sibs=%d' % (
        c['qid'], c['cat'], c['answer'], pick['answer'] if pick else '-',
        pick['qid'] if pick else '-', 'OK' if top1_ok else 'X',
        len(r.same_chart_cases(c.get('pillars', {}), exclude_qid=c['qid']))))

lines = ['LOO cases: %d' % n,
         'BM25 top-1(同类别优先): %d/%d = %.1f%%' % (loo1, n, loo1 / n * 100),
         'BM25 top-3 多数票:      %d/%d = %.1f%%' % (loo3, n, loo3 / n * 100),
         ''] + detail
with open(r'E:\ming_li_skill\MingLiSkill\retriever_loo.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('LOO top1 %d/%d = %.1f%% | top3-vote %d/%d = %.1f%%' % (
    loo1, n, loo1 / n * 100, loo3, n, loo3 / n * 100))
