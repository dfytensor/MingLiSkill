# -*- coding: utf-8 -*-
"""Download raw competition papers + scoring code + fortune api results."""
import io, sys, os, json, urllib.request, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
HDR = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/vnd.github.v3+json'}
REPO = 'DestinyLinker/MingLi-Bench'
DEST = r'E:\ming_li_skill\MingLiSkill\bench_source'
os.makedirs(DEST, exist_ok=True)

FILES = [
    'data/raw/2022.txt', 'data/raw/2023.txt', 'data/raw/2024.txt', 'data/raw/2025.txt',
    'mingli_bench/benchmark.py', 'mingli_bench/data/loader.py',
    'README_zh.md',
]
for path in FILES:
    url = 'https://api.github.com/repos/%s/contents/%s' % (REPO, path)
    req = urllib.request.Request(url, headers=HDR)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            d = json.loads(resp.read().decode('utf-8'))
        content = base64.b64decode(d['content'])
        fn = path.replace('/', '__')
        with open(os.path.join(DEST, fn), 'wb') as f:
            f.write(content)
        print('OK  %7d  %s' % (len(content), path))
    except Exception as e:
        print('FAIL %s: %s' % (path, e))

# fortune_api_results is large, use raw URL
try:
    url = 'https://raw.githubusercontent.com/%s/HEAD/data/fortune_api_results.json' % REPO
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read()
    with open(os.path.join(DEST, 'fortune_api_results.json'), 'wb') as f:
        f.write(body)
    print('OK  %7d  fortune_api_results.json' % len(body))
except Exception as e:
    print('FAIL fortune_api: %s' % e)
