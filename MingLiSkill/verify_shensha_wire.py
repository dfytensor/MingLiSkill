# -*- coding: utf-8 -*-
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
htk = HybridMingliToolkit()
r = htk.analyze_question(year=1980, month=7, day=11, hour=9, gender='男',
                         category='婚姻', question='命主第一次结婚在那一年？',
                         options_json=json.dumps([{"letter": "A", "text": "2000年"},
                                                  {"letter": "B", "text": "2001年"},
                                                  {"letter": "C", "text": "2005年"},
                                                  {"letter": "D", "text": "2006年"}]))
d = json.loads(r)
for yi in d['liunian']['年份流年对比']:
    ss = [t for t in yi['标签'] if '神煞' in t]
    print(yi['年份'], yi['干支'], 'shensha:', ss if ss else '-')
