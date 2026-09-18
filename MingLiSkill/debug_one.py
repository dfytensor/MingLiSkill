# -*- coding: utf-8 -*-
import io, sys, json, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
q = data['questions'][0]
bi = q['birth_info']
try:
    from tools import HybridMingliToolkit
    htk = HybridMingliToolkit()
    r = htk.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
                             hour=bi.get('hour', 12), gender=bi['gender'],
                             category=q['category'], question=q['question'],
                             options_json=json.dumps(q['options'], ensure_ascii=False))
    print('OK', len(r))
except Exception:
    traceback.print_exc()
