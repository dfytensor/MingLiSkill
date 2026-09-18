# -*- coding: utf-8 -*-
"""Download mingli corpus files from GitHub raw."""
import io, sys, os, json, urllib.request, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
HDR = {'User-Agent': 'Mozilla/5.0'}
DEST = r'E:\ming_li_skill\MingLiSkill\corpus'
os.makedirs(DEST, exist_ok=True)

# resolve HEAD sha per repo to build raw urls
def tree(repo):
    url = 'https://api.github.com/repos/%s/git/trees/HEAD?recursive=1' % repo
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

def want(path, size):
    if size < 3000:
        return False
    low = path.lower()
    if low.endswith(('.txt', '.md')):
        return True
    return False

JOBS = []
t = tree('workhardooday/Bazi_RAG_Agent')
for x in t['tree']:
    if x['type'] == 'blob' and want(x['path'], x.get('size', 0)):
        JOBS.append(('workhardooday/Bazi_RAG_Agent', x['path'], x['size']))
t = tree('x3747991-ship-it/ditiansui-skillpack')
for x in t['tree']:
    if x['type'] == 'blob' and want(x['path'], x.get('size', 0)):
        JOBS.append(('x3747991-ship-it/ditiansui-skillpack', x['path'], x['size']))
t = tree('henrryjoke/diguan-bazi')
for x in t['tree']:
    if x['type'] == 'blob' and x['path'].startswith('references/') and want(x['path'], x.get('size', 0)):
        JOBS.append(('henrryjoke/diguan-bazi', x['path'], x['size']))

log = []
ok_n = fail_n = 0
total_bytes = 0
for repo, path, size in JOBS:
    raw = 'https://raw.githubusercontent.com/%s/HEAD/%s' % (repo, urllib.parse.quote(path))
    safe = path.replace('/', '__')
    dest = os.path.join(DEST, repo.split('/')[-1] + '__' + safe)
    try:
        req = urllib.request.Request(raw, headers=HDR)
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
        with open(dest, 'wb') as f:
            f.write(body)
        total_bytes += len(body)
        ok_n += 1
        log.append('OK  %7d  %s :: %s' % (len(body), repo, path))
    except Exception as e:
        fail_n += 1
        log.append('FAIL %s :: %s (%s)' % (repo, path, e))

log.append('TOTAL files=%d ok=%d fail=%d bytes=%d' % (len(JOBS), ok_n, fail_n, total_bytes))
with open(r'E:\ming_li_skill\MingLiSkill\corpus_dl_log.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(log))
print('ok=%d fail=%d bytes=%d' % (ok_n, fail_n, total_bytes))
