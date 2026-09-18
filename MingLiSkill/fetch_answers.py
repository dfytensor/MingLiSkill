# -*- coding: utf-8 -*-
from urllib.parse import quote
import subprocess, re, sys

# 2020 答案页 (标题带错字: 第大一屆)
page_url = 'https://hkjfma.org/' + quote('過往活動/2020第十一屆全球算命師比賽/2020第大一屆全球算命師比賽答案及得獎名單')
r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', page_url], capture_output=True)
html = r.stdout.decode('utf-8', errors='replace')
imgs = re.findall(r'href="(http://hkjfma\.org/wp-content/uploads/2020/[^"]+\.jpg)"', html)
print('answer images found:', len(imgs))

out_lines = ['count=%d' % len(imgs)] + imgs
open(r'E:\ming_li_skill\MingLiSkill\data2020\answer_urls.txt', 'w', encoding='utf-8').write('\n'.join(out_lines))

# download
for i, u in enumerate(imgs):
    out = r'E:\ming_li_skill\MingLiSkill\data2020\ans%d.jpg' % i
    subprocess.run(['curl', '-s', '-L', '-o', out, '--max-time', '60', u], capture_output=True)
    print('downloaded ans%d' % i)
