# -*- coding: utf-8 -*-
"""Test Ziwei interpretation: does it provide signal for benchmark questions?"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from ziwei_interpret import query_ziwei_interpret

# Test with a real chart: ftb_0117 (2007-01-31 male, 出身贫富)
# We know: ziwei has 天府 in 命宫
palaces = {
    '命宫': ['天府'],
    '官禄': [],
    '夫妻': ['廉贞', '贪狼'],
    '财帛': ['天相'],
    '疾厄': ['天同', '天梁'],
    '子女': ['巨门'],
    '迁移': ['武曲', '七杀'],
    '父母': [],
    '田宅': ['天机'],
}

results = query_ziwei_interpret(palaces)
out = []
out.append('=== Ziwei Interpretation Test (ftb_0117, 出身贫富, real=C 富贵) ===')
for desc, source in results:
    out.append('[%s] %s' % (source, desc))
out.append('')
out.append('Analysis: 天府=库星坐命 → 善积累、稳 重 → 偏向富贵/小康')
out.append('Answer should be C (富贵) or B (小康) based on 天府坐命')

with open(r'E:\ming_li_skill\MingLiSkill\ziwei_test.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('results: %d' % len(results))
