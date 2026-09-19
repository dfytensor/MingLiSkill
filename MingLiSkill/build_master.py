# -*- coding: utf-8 -*-
"""build_master.py — 解析asklingxi全部17届HTML → 结构化主数据集(题+八字+官方答案)"""
import subprocess, re, json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CACHE = r'E:\ming_li_skill\MingLiSkill\data_archive\asklingxi_html'
os.makedirs(CACHE, exist_ok=True)

def get_html(y):
    fp = os.path.join(CACHE, '%d.html' % y)
    if os.path.exists(fp) and os.path.getsize(fp) > 50000:
        return open(fp, encoding='utf-8').read()
    r = subprocess.run(['curl', '-s', '-L', '--max-time', '90',
                        'https://asklingxi.com/mingli-dasai/%d' % y], capture_output=True)
    h = r.stdout.decode('utf-8', errors='replace')
    open(fp, 'w', encoding='utf-8').write(h)
    return h

# 高亮span = 官方答案
HILITE = re.compile(r'rounded-full ([^"]*?)">(?:<!-- -->)?([A-E])(?:<!-- -->)?</span>')

def parse_year(y):
    h = get_html(y)
    # 命例块: 坤造/乾造 + 干支
    blocks = re.split(r'命例[一二三四五六七八九十]', h)
    persons = []
    for bi, blk in enumerate(blocks[1:], 1):
        # 四柱: 乾造/坤造后连续8个干支(4柱×2字)
        m = re.search(r'(乾造|坤造)((?:[甲乙丙丁戊己庚辛壬癸]{2}\s*){4})', blk)
        pillars = None
        if m:
            raw = m.group(2)
            pillars = re.findall(r'[甲乙丙丁戊己庚辛壬癸]{2}', raw)[:4]
        # 该命例的题目: 从块首到下一个命例分隔
        nxt = blocks[bi] if bi < len(blocks) - 1 else blk
        qmarks = [(mm.start(), mm.group(1)) for mm in re.finditer(r'Q<!-- -->(\d+)', blk)]
        opts = [(mm.start(), mm.group(2)) for mm in HILITE.finditer(blk)]
        qs = []
        for qi, (pos, qnum) in enumerate(qmarks):
            end = qmarks[qi + 1][0] if qi + 1 < len(qmarks) else len(blk)
            seg = blk[pos:end]
            # 该题选项字母按顺序
            letters = re.findall(r'(?:<!-- -->)?([A-E])(?:<!-- -->)?</span><span', seg)
            # 官方答案 = 该题段内高亮span的字母
            hi = re.findall(r'rounded-full [^"]*?bg-primary text-white[^"]*?">(?:<!-- -->)?([A-E])', seg)
            # 题干文本: 第一个<p>内
            qtext = re.search(r'<p[^>]*>([^<]{5,200})', seg)
            # 选项文本
            opt_texts = re.findall(r'font-medium">([A-E])</span><span[^>]*>([^<]{2,150})', seg)
            qs.append({
                'qnum': int(qnum),
                'qtext': qtext.group(1) if qtext else '',
                'options': opt_texts,
                'highlighted': hi,
            })
        persons.append({'block': bi, 'pillars': pillars, 'questions': qs})
    return persons

master = {}
for y in range(2010, 2027):
    try:
        persons = parse_year(y)
        master[str(y)] = persons
        nq = sum(len(p['questions']) for p in persons)
        nans = sum(1 for p in persons for q in p['questions'] if q['highlighted'])
        print('%d: %d persons, %d questions, %d with answer-mark' % (y, len(persons), nq, nans))
    except Exception as e:
        print('%d: ERR %s' % (y, e))

json.dump(master, open(r'E:\ming_li_skill\MingLiSkill\data_archive\master_raw.json', 'w', encoding='utf-8'),
          ensure_ascii=False)
print('saved master_raw.json')
