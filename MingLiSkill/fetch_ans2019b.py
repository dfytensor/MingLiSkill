# -*- coding: utf-8 -*-
from urllib.parse import quote
import subprocess, re

p = '過往活動/2019第十屆全球算命師比賽/2019年度第十屆全球算命師比賽答案,得獎名單及統計資料'
url = 'https://hkjfma.org/' + quote(p, safe='/,')
r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', url], capture_output=True)
html = r.stdout.decode('utf-8', errors='replace')
m = re.search(r'<title>([^<]+)</title>', html)
print('title:', (m.group(1)[:50] if m else 'none'))
imgs = re.findall(r'(?:src|href)="(http[^"]+hkjfma\.org/wp-content/uploads/[^"]+\.(?:jpg|jpeg|png))"', html)
seen = []
for u in imgs:
    if u not in seen and 'logo' not in u and 'fb.jpg' not in u:
        seen.append(u)
print('imgs:', len(seen))

import os
base = r'E:\ming_li_skill\MingLiSkill\data2019' + chr(92)
for i, u in enumerate(seen):
    subprocess.run(['curl', '-s', '-L', '-o', base + 'ans2019_%d.jpg' % i, '--max-time', '90', u], capture_output=True)
    print('got ans2019_%d' % i)
