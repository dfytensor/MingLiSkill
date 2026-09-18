# -*- coding: utf-8 -*-
"""
kb333_engine.py — 用扩充后的 333 条知识库重跑 160 题
每个 KB 条目检查其关键词是否在选项文本中出现。
"""
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from knowledge_base import KB
from knowledge_ext import KB_EXT

# Merge all KB
FULL_KB = KB + KB_EXT

# Load extracted knowledge
extracted = json.load(open(r'E:\ming_li_skill\MingLiSkill\extracted_knowledge.json', encoding='utf-8'))
for e in extracted:
    FULL_KB.append({
        '主题': e['topic'],
        '触发': {'关键词': e['keywords']},
        '断语': e['assertion'],
        '关键词': e['keywords'],
    })

print('Full KB: %d entries' % len(FULL_KB))

HTK = HybridMingliToolkit()
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'


def kw_in(text, kw):
    try:
        return bool(re.search(kw, text))
    except:
        return kw in text


def score_with_kb333(question, chart, category):
    """用333条KB打分选项。每条KB条目的关键词匹配选项文本。"""
    b = chart.get('bazi', {})
    z = chart.get('ziwei', {})
    ss = b.get('十神', {})
    wx = b.get('五行力量', {})
    day_gan = b.get('日主', '')
    day_wx = b.get('日主五行', '')
    
    # 提取命局特征（用于KB条目条件匹配）
    features = set()
    features.update(day_wx)  # 日主五行
    features.update(wx.keys())  # 所有五行
    
    # 透干十神
    for k, v in ss.items():
        if '天干' in k:
            features.add(v)
    
    # 全部十神
    for v in ss.values():
        features.add(v)
    
    # 喜忌
    yong = b.get('喜用神', '')
    ji = b.get('忌神', '')
    if yong: features.add('喜' + yong)
    if ji: features.add('忌' + ji)
    
    # 强弱
    features.add(b.get('日主强弱', ''))
    
    # 格局
    ca = chart.get('career_analysis', {})
    geju = ca.get('格局倾向', '')
    if geju:
        features.add(geju)
    
    # 紫微主星
    for k, v in z.items():
        if k.endswith('主星') and isinstance(v, list):
            for star in v:
                features.add(star)
    
    features_str = ' '.join(features)
    
    # KB 匹配：条目的触发关键词在 features 中出现 → 激活
    activated = []
    for e in FULL_KB:
        hit_count = 0
        # 检查触发条件
        trig = e.get('触发', {})
        if isinstance(trig, dict):
            for k, vals in trig.items():
                if isinstance(vals, list):
                    for v in vals:
                        if isinstance(v, str) and v in features_str:
                            hit_count += 1
                            break
                elif isinstance(vals, str) and vals in features_str:
                    hit_count += 1
        elif isinstance(trig, str):
            if trig in features_str:
                hit_count += 1
        
        # 也检查关键词是否在特征中
        kws = e.get('关键词', [])
        for kw in kws:
            if kw in features_str:
                hit_count += 1
        
        if hit_count > 0:
            activated.append((hit_count, e))
    
    # 按命中数排序，取前15
    activated.sort(key=lambda x: -x[0])
    top = activated[:15]
    
    # 用激活的断语给选项打分
    option_scores = {}
    for o in question.get('options', []):
        letter = o.get('letter', '?')
        txt = o.get('text', '')
        score = 0.0
        for hits, e in top:
            for kw in e.get('关键词', []):
                try:
                    if re.search(kw, txt):
                        score += 1.0 * hits
                except:
                    if kw in txt:
                        score += 1.0 * hits
            # 断语中的关键词也匹配
            assertion = e.get('断语', '')
            for kw in ['富','贵','贫','穷','病','伤','婚','离','子','官','讼','灾','寿','夭','智','愚','聪','暴','温和','固执','桃花','迁移','出国','留学']:
                if kw in assertion and kw in txt:
                    score += 0.5
        option_scores[letter] = score
    
    return option_scores


def main():
    with open(DATA_PATH, encoding='utf-8') as f:
        data = json.load(f)
    
    correct = total = 0
    detail = []
    cat_stats = {}
    
    for q in data['questions']:
        bi = q['birth_info']
        cat = q['category']
        try:
            r = HTK.analyze_question(
                year=bi['year'], month=bi['month'], day=bi['day'],
                hour=bi.get('hour', 12), gender=bi['gender'],
                category=cat, question=q['question'],
                options_json=json.dumps(q['options'], ensure_ascii=False))
            chart = json.loads(r)
        except:
            chart = {}
        
        scores = score_with_kb333(q, chart, cat)
        
        if scores and max(scores.values()) > 0:
            best = max(scores, key=lambda L: scores[L])
        else:
            best = chart.get('rules_suggestion', {}).get('suggested_answer', 'A')
        
        real = q['answer']
        ok = best == real
        total += 1
        correct += ok
        cat_stats.setdefault(cat, [0, 0])
        cat_stats[cat][0] += ok
        cat_stats[cat][1] += 1
        detail.append('%s %-4s %s->%s %s' % (q['id'], cat, best, real, 'OK' if ok else 'X'))
    
    lines = ['=== KB 333 ENTRIES ENGINE ===']
    lines.append('Score: %d/%d = %.1f%%' % (correct, total, correct/total*100))
    lines.append('Baselines: rules 33.75% | hybrid 40.0%')
    lines.append('')
    for cat, s in sorted(cat_stats.items()):
        lines.append('  %s: %d/%d (%.0f%%)' % (cat, s[0], s[1], s[0]/max(s[1],1)*100))
    lines += detail
    with open(r'E:\ming_li_skill\MingLiSkill\kb333_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('KB333: %d/%d = %.1f%%' % (correct, total, correct/total*100))


if __name__ == '__main__':
    main()
