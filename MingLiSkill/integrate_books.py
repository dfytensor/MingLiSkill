# -*- coding: utf-8 -*-
"""
integrate_books.py — 解析下载的书籍/案例/数据表，提取结构化断语和规则
沉淀进 knowledge_base + retriever + skill 工具链
"""
import io, sys, os, re, json
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BOOKS = r'E:\ming_li_skill\MingLiSkill\books'
OUT = r'E:\ming_li_skill\MingLiSkill'

all_entries = []  # {source, topic, condition, assertion, keywords}

def add_entry(source, topic, condition, assertion, keywords):
    all_entries.append({
        'source': source, 'topic': topic,
        'condition': condition, 'assertion': assertion,
        'keywords': keywords,
    })

# ============ 1. 解析子平真诠（格局成败救应） ============
zp_path = os.path.join(BOOKS, 'books__zipingzhenquan.md')
if os.path.exists(zp_path):
    txt = open(zp_path, encoding='utf-8', errors='replace').read()
    # 按章节切分
    chapters = re.split(r'\n(?=# )', txt)
    for ch in chapters:
        # 提取章节标题
        title_match = re.match(r'#\s*(.+)', ch)
        title = title_match.group(1).strip() if title_match else '未知'
        
        # 按句号切分断语
        sentences = re.split(r'[。！]', ch)
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 20 or len(sent) > 300:
                continue
            # 提取关键断语（包含格局/成败/喜忌/用神的句子）
            keywords = []
            for kw in ['正官', '七杀', '正财', '偏财', '正印', '偏印', '食神', '伤官',
                       '比肩', '劫财', '格局', '成败', '救应', '喜', '忌', '用神',
                       '清', '浊', '纯', '杂', '顺', '逆', '旺', '衰']:
                if kw in sent:
                    keywords.append(kw)
            if len(keywords) >= 2:
                add_entry('子平真诠', title, '、'.join(keywords[:5]), sent, keywords)

# ============ 2. 解析穷通宝鉴（调候） ============
qt_path = os.path.join(BOOKS, 'books__穷通宝鉴.md')
if os.path.exists(qt_path):
    txt = open(qt_path, encoding='utf-8', errors='replace').read()
    # 按日主×月令分段
    sections = re.split(r'\n(?=三|四|五|六|七|八|九|十|十一|十二月)', txt)
    for sec in sections:
        # 查找日主标记
        for gan in '甲乙丙丁戊己庚辛壬癸':
            if gan in sec[:50]:
                sentences = re.split(r'[。！]', sec)
                for sent in sentences:
                    sent = sent.strip()
                    if len(sent) < 15 or len(sent) > 200:
                        continue
                    keywords = []
                    for kw in ['调候', '喜', '忌', '用', '火', '水', '木', '金', '土', '暖', '寒', '燥', '湿']:
                        if kw in sent:
                            keywords.append(kw)
                    if len(keywords) >= 2:
                        add_entry('穷通宝鉴', '调候-%s' % gan, '日主%s' % gan, sent, keywords)
                break

# ============ 3. 解析命例案例 ============
example_files = [
    ('books__examples__guan.md', '官格案例'),
    ('books__examples__shangguan.md', '伤官案例'),
    ('books__examples__cai.md', '财格案例'),
    ('books__examples__pianguan.md', '偏官案例'),
]
for fn, topic in example_files:
    fp = os.path.join(BOOKS, fn)
    if not os.path.exists(fp):
        continue
    txt = open(fp, encoding='utf-8', errors='replace').read()
    # 按命例切分（通常以"乾造"/"坤造"开头）
    cases = re.split(r'(?=乾造|坤造)', txt)
    for case in cases:
        if len(case) < 50:
            continue
        # 提取八字
        gz_match = re.findall(r'([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])', case)
        if len(gz_match) < 4:
            continue
        pillars = gz_match[:4]
        
        # 提取分析断语
        sentences = re.split(r'[。！]', case)
        analysis = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        # 提取关键词
        keywords = []
        for kw in ['富', '贵', '贫', '贱', '寿', '夭', '婚', '子', '官', '伤',
                   '病', '灾', '成', '败', '大运', '流年', '格局', '用神']:
            for s in analysis:
                if kw in s:
                    keywords.append(kw)
                    break
        
        if keywords:
            add_entry(topic, topic + '-' + ''.join(pillars[:2]),
                      '四柱:' + ' '.join(pillars),
                      ' | '.join(analysis[:5]),
                      keywords)

# ============ 4. 解析 datas.py（结构化数据表） ============
datas_path = os.path.join(BOOKS, 'datas.py')
if os.path.exists(datas_path):
    txt = open(datas_path, encoding='utf-8', errors='replace').read()
    # 查找字典/列表定义
    # 找变量名和注释
    var_blocks = re.findall(r'(\w+)\s*=\s*\{', txt)
    # 提取注释中的断语
    comments = re.findall(r'#\s*(.+)', txt)
    for comment in comments:
        comment = comment.strip()
        if len(comment) > 10 and any(kw in comment for kw in ['十神', '神煞', '类象', '宫位', '五行']):
            add_entry('datas.py', '数据表', '注释', comment, [c for c in comment if '\u4e00' <= c <= '\u9fff'][:10])
    
    # 提取字符串中的断语
    strings = re.findall(r"['\"]([\u4e00-\u9fff][^'\"]{10,80})['\"]", txt)
    for s in strings:
        s = s.strip()
        keywords = []
        for kw in ['正官', '七杀', '正财', '偏财', '正印', '偏印', '食神', '伤官',
                   '比肩', '劫财', '神煞', '桃花', '驿马', '贵人', '羊刃', '禄']:
            if kw in s:
                keywords.append(kw)
        if keywords:
            add_entry('datas.py', '数据表', '、'.join(keywords[:3]), s, keywords)

# ============ 5. 解析命学真典 ============
mx_path = os.path.join(BOOKS, 'mingxue__SKILL.md')
if os.path.exists(mx_path):
    txt = open(mx_path, encoding='utf-8', errors='replace').read()
    sentences = re.split(r'[。！\n]', txt)
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 20 or len(sent) > 200:
            continue
        keywords = []
        for kw in ['格局', '用神', '喜忌', '大运', '流年', '十神', '宫位', '旺衰',
                   '事业', '婚姻', '财运', '健康', '性格', '子女']:
            if kw in sent:
                keywords.append(kw)
        if len(keywords) >= 2:
            add_entry('命学真典', keywords[0], '、'.join(keywords[:3]), sent, keywords)

# ============ 汇总 ============
print('Total entries extracted: %d' % len(all_entries))
by_source = Counter(e['source'] for e in all_entries)
for src, cnt in by_source.items():
    print('  %s: %d entries' % (src, cnt))

# Save
with open(os.path.join(OUT, 'extracted_knowledge.json'), 'w', encoding='utf-8') as f:
    json.dump(all_entries, f, ensure_ascii=False, indent=1)

# Also create a flat text file for BM25 indexing
flat_lines = []
for i, e in enumerate(all_entries):
    flat_lines.append('[%d] [%s] [%s] %s | 关键词: %s' % (
        i, e['source'], e['topic'], e['assertion'][:100], ','.join(e['keywords'][:8])))

with open(os.path.join(OUT, 'extracted_knowledge.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(flat_lines))

print('saved extracted_knowledge.json + extracted_knowledge.txt')
