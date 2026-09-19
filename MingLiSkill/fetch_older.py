# -*- coding: utf-8 -*-
"""fetch_older.py — 2010/2011/2012/2016/2017 届题目+答案页抓取"""
from urllib.parse import quote
import subprocess, re

def get_page(path):
    url = 'https://hkjfma.org/' + quote(path)
    r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', url], capture_output=True)
    return r.stdout.decode('utf-8', errors='replace')

def imgs_of(html):
    found = re.findall(r'(?:src|href)="(http[^"]+hkjfma\.org/wp-content/uploads/[^"]+\.(?:jpg|jpeg|png))"', html)
    seen = []
    for u in found:
        if u not in seen and 'logo' not in u and 'fb.jpg' not in u and '766x' not in u and '-940x' not in u:
            seen.append(u)
    return seen

targets = [
    ('2010', '過往活動/2010年度全球算命師比賽（第一屆）/題目、答案及得獎者'),
    ('2011', '過往活動/2011年度全球算命師比賽（第二屆）/題目及答案'),
    ('2012', '過往活動/2012年度全球算命師比賽（第三屆）/題目及答案'),
    ('2013', '過往活動/2013年度全球算命師比賽（第四屆）/2013年第四屆全球算命師大賽題目'),
    ('2016ans', '過往活動/2016年度全球算命師比賽（第七屆）/2016第七屆比賽答案及得獎成績'),
    ('2017', '過往活動/2017年度全球算命師比賽（第八屆）/2017年度全球算命師比賽（第八屆）題目'),
]
out = []
import os
base = r'E:\ming_li_skill\MingLiSkill\data2019' + chr(92)
for tag, path in targets:
    h = get_page(path)
    t = re.search(r'<title>([^<]+)</title>', h)
    ims = imgs_of(h)
    out.append('%s [%s]: %d imgs' % (tag, 'OK' if t else '404', len(ims)))
    for i, u in enumerate(ims):
        out.append('  ' + u)
        ext = u.split('.')[-1]
        subprocess.run(['curl', '-s', '-L', '-o', base + 'old%s_%d.%s' % (tag, i, ext), '--max-time', '90', u], capture_output=True)
open(r'E:\ming_li_skill\MingLiSkill\data2019\old_urls.txt', 'w', encoding='utf-8').write('\n'.join(out))
print(chr(10).join([l for l in out if not l.startswith('  ')]))
