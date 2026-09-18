# -*- coding: utf-8 -*-
from urllib.parse import quote
import subprocess, re

def get_page(path):
    url = 'https://hkjfma.org/' + quote(path)
    r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', url], capture_output=True)
    return r.stdout.decode('utf-8', errors='replace')

# 2023 紀念刊物
h = get_page('2023/11/2023年第十四屆全球算命師大賽頒獎禮暨第二屆國際玄學術數研討會紀念刊物')
imgs = re.findall(r'(?:src|href)="(http[^"]+hkjfma\.org/wp-content/uploads/[^"]+\.(?:jpg|jpeg|png|pdf))"', h)
seen = []
for u in imgs:
    if u not in seen and 'logo' not in u and 'fb.jpg' not in u and '766x' not in u and '-940x' not in u:
        seen.append(u)
print('2023紀念刊物 imgs:', len(seen))
import os
base = r'E:\ming_li_skill\MingLiSkill\data2019' + chr(92)
os.makedirs(base, exist_ok=True)
for i, u in enumerate(seen[:20]):
    ext = '.pdf' if '.pdf' in u else '.jpg'
    subprocess.run(['curl', '-s', '-L', '-o', base + 'jc2023_%d%s' % (i, ext), '--max-time', '90', u], capture_output=True)
    print('got jc2023_%d' % i)
open(base + 'jc_urls.txt', 'w', encoding='utf-8').write('\n'.join(seen))
