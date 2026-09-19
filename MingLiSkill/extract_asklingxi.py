# -*- coding: utf-8 -*-
"""extract_asklingxi.py — 提取asklingxi全部17届官方答案(通过CSS高亮标记)"""
import subprocess, re, json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

YEARS = list(range(2010, 2027))
out_all = {}
detail_all = {}

for y in YEARS:
    url = 'https://asklingxi.com/mingli-dasai/%d' % y
    r = subprocess.run(['curl', '-s', '-L', '--max-time', '90', url], capture_output=True)
    h = r.stdout.decode('utf-8', errors='replace')
    # 每个高亮span前的字母 = 官方答案
    # 结构: <span class="...bg-primary text-white...">A</span>
    hits = re.findall(r'rounded-full ([^"]*?bg-primary text-white[^"]*?)">([A-E])</span>', h)
    answers = [L for _, L in hits]
    out_all[str(y)] = answers
    detail_all[str(y)] = {'n_questions': h.count('Q<!-- -->'), 'n_highlight': len(answers)}
    print('%d: %d answers extracted' % (y, len(answers)))

json.dump({
    'source': 'asklingxi.com/mingli-dasai (CSS高亮标记提取)',
    'note': 'bg-primary text-white 高亮的选项 = 官方正确答案',
    'answers': out_all,
}, open(r'E:\ming_li_skill\MingLiSkill\data_archive\asklingxi_answers.json', 'w', encoding='utf-8'),
    ensure_ascii=False, indent=1)
print('saved asklingxi_answers.json')
