# -*- coding: utf-8 -*-
from urllib.parse import quote
import subprocess, re

paths = [
    ('2010', '過往活動/2010年度全球算命師比賽（第一屆）/題目、答案及得獎者'),
    ('2016', '過往活動/2016年度全球算命師比賽（第七屆）/2016第七屆比賽答案及得獎成績'),
    ('2017', '過往活動/2017年度全球算命師比賽（第八屆）/2017年度全球算命師比賽（第八屆）題目'),
]
for tag, p in paths:
    url = 'https://hkjfma.org/' + quote(p)
    r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', url], capture_output=True)
    h = r.stdout.decode('utf-8', errors='replace')
    pdfs = re.findall(r'href="([^"]+\.pdf)"', h)
    survey = re.findall(r'href="(https?://(?:www\.)?allcounted[^"]*)"', h)
    fb = re.findall(r'href="(https://www\.facebook\.com/[^"]*)"', h)
    print(tag, '| pdf:', len(pdfs), '| survey:', len(survey), '| fb:', len(fb))
    for u in (pdfs + survey)[:4]:
        print('   ', u[:110])
