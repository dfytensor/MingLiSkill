# -*- coding: utf-8 -*-
"""Discover corpus sources: github repos + gushiwen chapter list."""
import io, sys, json, re, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
HDR = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

out = []

# 1) GitHub repo search
for q in ['渊海子平', '三命通会', '子平真诠', '八字 命理 书', '滴天髓']:
    try:
        url = 'https://api.github.com/search/repositories?q=%s&per_page=8' % urllib.parse.quote(q)
        req = urllib.request.Request(url, headers=HDR)
        with urllib.request.urlopen(req, timeout=20) as resp:
            d = json.loads(resp.read().decode('utf-8'))
        out.append('== github: %s ==' % q)
        for it in d.get('items', []):
            out.append('  %s | %s | %s' % (it['full_name'], it.get('size', 0), (it.get('description') or '')[:60]))
    except Exception as e:
        out.append('github %s FAIL %s' % (q, e))

# 2) gushiwen 三命通会 index
try:
    req = urllib.request.Request('https://www.gushiwen.cn/gushi/tonghui.aspx', headers=HDR)
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    links = re.findall(r'href="(/shiwenv_[\w]+\.aspx)"[^>]*>([^<]{2,40})<', html)
    out.append('== gushiwen 三命通会 chapters: %d ==' % len(links))
    for u, t in links[:40]:
        out.append('  %s %s' % (u, t))
    with open(r'E:\ming_li_skill\MingLiSkill\gushiwen_index.json', 'w', encoding='utf-8') as f:
        json.dump(links, f, ensure_ascii=False, indent=1)
except Exception as e:
    out.append('gushiwen FAIL %s' % e)

with open(r'E:\ming_li_skill\MingLiSkill\corpus_scan.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
