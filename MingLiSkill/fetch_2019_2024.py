# -*- coding: utf-8 -*-
from urllib.parse import quote
import subprocess, re

def get_page(path):
    url = 'https://hkjfma.org/' + quote(path)
    r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', url], capture_output=True)
    return r.stdout.decode('utf-8', errors='replace')

base = r'E:\ming_li_skill\MingLiSkill\data2019' + chr(92)
import os
os.makedirs(base, exist_ok=True)

# 2019 question PNGs
urls2019 = [
    '61636324_1447452102070117_8444786292490764288_n.png',
    '61438379_1447452122070115_8917340262506692608_n.png',
    '61678940_1447452162070111_6070995315811418112_n.png',
    '61481736_1447452205403440_3603024523898650624_n.png',
    '61865447_1447452238736770_7199744607037423616_n.png',
    '61763221_1447452265403434_8791022203429715968_n.png',
    '61425962_1447452298736764_4098239291124088832_n.png',
    '61383369_1447452378736756_4532968815604006912_n.png',
    '62212461_1447452442070083_2795143602177572864_n.png',
    '61439935_1447452055403455_8102613695491735552_n.png',
]
for i, fn in enumerate(urls2019):
    u = 'http://hkjfma.org/wp-content/uploads/2019/06/' + quote(fn)
    subprocess.run(['curl', '-s', '-L', '-o', base + 'q2019_%d.png' % i, '--max-time', '90', u], capture_output=True)
    print('got q2019_%d' % i)

# 2024 answer key + whatsapp imgs
urls2024 = [
    ('http://hkjfma.org/wp-content/uploads/2024/08/' + quote('2024年第15屆全球算命師大賽正確答案.jpeg'), 'ans2024.jpg'),
    ('http://hkjfma.org/wp-content/uploads/2024/08/WhatsApp-Image-2024-08-09-at-23.58.12.jpeg', 'ans2024_b.jpg'),
]
for u, fn in urls2024:
    subprocess.run(['curl', '-s', '-L', '-o', base + fn, '--max-time', '90', u], capture_output=True)
    print('got', fn)

# 2023 June post (truncated URL from nav)
h = get_page('2023/06/由香港青年術數家協會主辦-2023年第十四屆全球算命師大賽')
imgs = re.findall(r'(?:src|href)="(http[^"]+hkjfma\.org/wp-content/uploads/2023/[^"]+\.(?:jpg|jpeg|png))"', h)
seen = []
for u in imgs:
    if u not in seen and '-766x' not in u and 'logo' not in u:
        seen.append(u)
print('2023 june post imgs:', len(seen))
for i, u in enumerate(seen[:12]):
    subprocess.run(['curl', '-s', '-L', '-o', base + 'q2023_%d.jpg' % i, '--max-time', '90', u], capture_output=True)
    print('got q2023_%d' % i)
open(base + 'urls.txt', 'w', encoding='utf-8').write('\n'.join(seen))
