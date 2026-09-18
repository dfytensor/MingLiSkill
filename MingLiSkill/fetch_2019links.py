# -*- coding: utf-8 -*-
from urllib.parse import quote, unquote
import subprocess, re

# 2019 main post (200 OK confirmed)
p = '過往活動/2019第十屆全球算命師比賽'
url = 'https://hkjfma.org/' + quote(p)
r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', url], capture_output=True)
html = r.stdout.decode('utf-8', errors='replace')

# find all internal links under this post
links = re.findall(r'href="(https://hkjfma\.org/[^"]*2019[^"]*)"', html)
seen = []
for u in links:
    if u not in seen:
        seen.append(u)
out = ['2019 post links:']
for u in seen:
    out.append(unquote(u))
print('\n'.join(out[:20]))
open(r'E:\ming_li_skill\MingLiSkill\data2019\post_links.txt', 'w', encoding='utf-8').write('\n'.join(out))
