# -*- coding: utf-8 -*-
"""preregister.py — 2019/2020 两届80题预注册预测（无官方答案=无法作弊）"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from blind2021_run import unified, adapt
from tools.ziwei_tools import ZiweiToolkit
from tools import HybridMingliToolkit
from datetime import datetime

ZT = ZiweiToolkit()
HTK = HybridMingliToolkit()

def parse_birth(s):
    """'1962-04-04 巳時 香港' / '1979-03-01 23:50 廣州' / '1963-06-26 午時 + 1976-08-12 巳時'"""
    s = s.strip()
    hour_map = {'子':23,'丑':1,'寅':3,'卯':5,'辰':7,'巳':9,'午':11,'未':13,'申':15,'酉':17,'戌':19,'亥':21}
    hour = 12
    for z, h in hour_map.items():
        if z + '時' in s or z + '时' in s:
            hour = h; break
    m = re.search(r'(\d{2,3}):(\d\d)', s)
    if m:
        hh = int(m.group(1))
        hour = 23 if hh >= 23 else hh
    dm = re.search(r'(\d{4})-(\d{2})-(\d{2})', s)
    loc = ''
    for L in ['香港','廣州','广州','马来西亚','馬來西亞','廣西','广西','台灣','台湾','天津','英国','英國','中山','大陆','大陸']:
        if L in s: loc = L; break
    return int(dm.group(1)), int(dm.group(2)), int(dm.group(3)), hour, loc

results = {}
dump = []
for src in ['comp2020_questions.json', 'comp2019_questions.json']:
    comp = json.load(open(r'E:\ming_li_skill\MingLiSkill\data_archive' + chr(92) + src, encoding='utf-8'))
    yr = src[4:8]
    for indiv in comp['individuals']:
        block = indiv['block']
        binfo = indiv['birth']
        gender = indiv['gender']
        # skip 双命例 (Q36-40 of 2019) — 不可单盘作答, 记为SKIP
        if '+' in binfo or '雙' in binfo or '双' in binfo:
            for qd in indiv['questions']:
                qid = '%s-%s' % (yr, qd['q'].split(' ')[0])
                results[qid] = {'answer': 'SKIP', 'why': '双命例题无法单盘预测', 'signal': '-'}
            continue
        y, mo, d, h, loc = parse_birth(binfo)
        for qd in indiv['questions']:
            qnum = qd['q'].split(' ')[0].replace('Q','').replace(':','').replace('：','')
            qid = '%s-Q%s' % (yr, qnum)
            opts = qd['options']
            letters = ['A','B','C','D','E'][:len(opts)]
            q21 = {
                'question_id': qid, 'person_id': block,
                'birth': {'year': y, 'month': mo, 'day': d, 'hour': h, 'minute': 0, 'place': loc, 'raw': binfo},
                'gender': 'male' if gender == '男' else 'female',
                'question': qd['q'], 'options': ['%s %s' % (L, t) for L, t in zip(letters, opts)],
                'answer': None,
            }
            bi2, fq = adapt(q21)
            pick, why = unified(fq, bi2)
            results[qid] = {
                'answer': pick or 'NO-SIGNAL',
                'why': why,
                'signal': pick or '-',
                'options': opts,
            }
            dump.append('%s | %s | %s | signal=%s' % (qid, gender, qd['q'][:50], pick or '-'))
            dump.append('   命例: %s %s' % (gender, binfo))

meta = {
    'type': 'PRE-REGISTERED PREDICTIONS',
    'date': datetime.now().isoformat(),
    'note': '2019/2020两届比赛无公开官方答案。本预测在答案公开前锁定, 不可事后修改。官方答案公开后逐题判分, 这是skill泛化能力的终极无偏测试。',
    'predictions': results,
}
json.dump(meta, open(r'E:\ming_li_skill\MingLiSkill\preregistered_predictions.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
open(r'E:\ming_li_skill\MingLiSkill\prereg_dump.txt', 'w', encoding='utf-8').write('\n'.join(dump))
sig = sum(1 for v in results.values() if v['answer'] not in ('NO-SIGNAL','SKIP'))
print('total questions: %d, signal-fired: %d, no-signal: %d, skip: %d' % (
    len(results), sig, sum(1 for v in results.values() if v['answer']=='NO-SIGNAL'),
    sum(1 for v in results.values() if v['answer']=='SKIP')))
