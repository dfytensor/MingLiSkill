# -*- coding: utf-8 -*-
import subprocess, re, json

r = subprocess.run(['curl', '-s', '-L', '--max-time', '60', 'https://asklingxi.com/mingli-dasai/2019'], capture_output=True)
h = r.stdout.decode('utf-8', errors='replace')

# 找 Q1 题干位置，查看周边数据结构
i = h.find('命主的身体跟长相为何')
print('Q1 at:', i)
if i > 0:
    seg = h[max(0, i - 200): i + 3000]
    # 找该片段中的key结构
    keys = re.findall(r'"(\w+)":', seg)
    print('keys near Q1:', keys[:40])
    # 保存片段
    open(r'E:\ming_li_skill\MingLiSkill\data_archive\q1_ctx.txt', 'w', encoding='utf-8').write(seg)

# 找数据脚本(可能题目+答案都在一个JSON blob)
m = re.findall(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
print('NEXT_DATA blobs:', len(m))
if m:
    try:
        data = json.loads(m[0])
        # 递归找含'官方'或answer的key
        def walk(o, path=''):
            if isinstance(o, dict):
                for k, v in o.items():
                    if any(w in str(k).lower() for w in ('answer', 'correct', 'da')):
                        print('KEY:', path + '/' + str(k), '->', str(v)[:100])
                    walk(v, path + '/' + str(k))
            elif isinstance(o, list):
                for idx, v in enumerate(o[:3]):
                    walk(v, path + '[%d]' % idx)
        walk(data)
        json.dump(data, open(r'E:\ming_li_skill\MingLiSkill\data_archive\next_data_2019.json', 'w', encoding='utf-8'), ensure_ascii=False)
        print('saved next_data_2019.json')
    except Exception as e:
        print('json parse fail:', e)
