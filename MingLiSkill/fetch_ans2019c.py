# -*- coding: utf-8 -*-
from urllib.parse import quote, unquote
import subprocess, re

p = '過往活動/2019第十屆全球算命師比賽'
url = 'https://hkjfma.org/' + quote(p)
r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', url], capture_output=True)
html = r.stdout.decode('utf-8', errors='replace')

links = re.findall(r'href="(https://hkjfma\.org/%e9%81%8e%e5%be%80[^"]*2019[^"]*)"', html)
seen = []
for u in links:
    if u not in seen:
        seen.append(unquote(u))

# 找答案页 (含"答案")
ans_url = None
for u in seen:
    if '答案' in u:
        ans_url = u
        print('ANSWER PAGE:', u)

if ans_url:
    full = 'https://hkjfma.org/' + quote(ans_url.replace('https://hkjfma.org/', ''), safe='/,')
    r2 = subprocess.run(['curl', '-s', '-L', '--max-time', '60', full], capture_output=True)
    h2 = r2.stdout.decode('utf-8', errors='replace')
    imgs = re.findall(r'(?:src|href)="(http[^"]+hkjfma\.org/wp-content/uploads/[^"]+\.(?:jpg|jpeg|png))"', h2)
    uniq = []
    for u in imgs:
        if u not in uniq and 'logo' not in u and 'fb.jpg' not in u:
            uniq.append(u)
    print('answer page imgs:', len(uniq))
    import os
    base = r'E:\ming_li_skill\MingLiSkill\data2019' + chr(92)
    for i, iu in enumerate(uniq):
        subprocess.run(['curl', '-s', '-L', '-o', base + 'ans2019_%d.jpg' % i, '--max-time', '90', iu], capture_output=True)
        print('got ans2019_%d' % i)
else:
    print('all child pages:')
    for u in seen:
        print(' ', u)
