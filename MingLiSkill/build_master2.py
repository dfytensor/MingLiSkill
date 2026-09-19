# -*- coding: utf-8 -*-
"""build_master2.py — 剥标签后解析"""
import subprocess, re, json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CACHE = r'E:\ming_li_skill\MingLiSkill\data_archive\asklingxi_html'
GANSET = '甲乙丙丁戊己庚辛壬癸'

def strip_tags(h):
    return re.sub(r'<[^>]+>', '', h)

def parse_year(y):
    h = open(os.path.join(CACHE, '%d.html' % y), encoding='utf-8').read()
    text = strip_tags(h)
    # 官方答案(从原始HTML高亮提取, 顺序对应题目顺序)
    hits = re.findall(r'rounded-full [^"]*?bg-primary text-white[^"]*?">(?:<!-- -->)?([A-E])(?:<!-- -->)?</span>', h)
    # 题号顺序(原始HTML中 Q<!-- -->N)
    qnums = re.findall(r'Q<!-- -->(\d+)', h)
    # 文本中找命例块
    blocks = re.split(r'命例[一二三四五六七八九十]', text)
    persons = []
    for blk in blocks[1:]:
        m = re.search(r'(?:乾造|坤造)([' + GANSET + r'][' + '子丑寅卯辰巳午未申酉戌亥' + r']){4}', blk)
        pillars = None
        if m:
            s = m.group(0)[2:]
            pillars = [s[i*2:(i+1)*2] for i in range(4)]
        # 该块内的题目文本(Q1...选项A...)
        qs = re.findall(r'Q(\d+)([^Q]{20,600}?)A([^\n]{2,120}?)B([^\n]{2,120}?)C([^\n]{2,120}?)D([^\n]{2,150})', blk)
        persons.append({'pillars': pillars, 'questions': qs})
    return persons, hits, qnums

master = {}
for y in range(2010, 2027):
    persons, hits, qnums = parse_year(y)
    master[str(y)] = {'persons': persons, 'answers': hits, 'qnums': qnums}
    np = sum(1 for p in persons if p['pillars'])
    print('%d: persons-with-pillars=%d, answers=%d, qblocks=%d' % (y, np, len(hits), sum(len(p['questions']) for p in persons)))

json.dump(master, open(r'E:\ming_li_skill\MingLiSkill\data_archive\master2.json', 'w', encoding='utf-8'),
          ensure_ascii=False)
print('saved master2.json')
