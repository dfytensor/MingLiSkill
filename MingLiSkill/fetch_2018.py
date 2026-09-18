# -*- coding: utf-8 -*-
from urllib.parse import quote
import subprocess

downloads = [
    ('http://hkjfma.org/wp-content/uploads/2018/10/2018第九屆全球算命師比賽答案.jpg', 'ans2018.jpg'),
    ('http://hkjfma.org/wp-content/uploads/2018/06/鄭智恆.jpg', 't2018_0.jpg'),
    ('http://hkjfma.org/wp-content/uploads/2018/06/樂只君師傅.jpg', 't2018_1.jpg'),
    ('http://hkjfma.org/wp-content/uploads/2018/06/陳開通師傅.jpg', 't2018_2.jpg'),
    ('http://hkjfma.org/wp-content/uploads/2018/06/丘智偉.jpg', 't2018_3.jpg'),
    ('http://hkjfma.org/wp-content/uploads/2018/06/方榮師傅.jpg', 't2018_4.jpg'),
    ('http://hkjfma.org/wp-content/uploads/2018/06/12308643_1050485481649304_5771317340732187806_n.jpg', 't2018_5.jpg'),
]
for u, fn in downloads:
    out = r'E:\ming_li_skill\MingLiSkill\data2020' + chr(92) + fn
    subprocess.run(['curl', '-s', '-L', '-o', out, '--max-time', '90', u], capture_output=True)
    print('got', fn)
