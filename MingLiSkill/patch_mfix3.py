# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'E:\ming_li_skill\MingLiSkill\marriage_fix_v2.py'
c = open(p, encoding='utf-8').read()
old = """        if now_right and not was_right:
            fix_ok += 1
        elif was_right and not now_right:
            fix_bad += 1
        else:
            continue
        details.append('%s: %s?%s real=%s %s [%s]' % (qid, my, new, real, '\u2713' if ok else '\u2717', why))"""
new = """        if now_right and not was_right:
            fix_ok += 1
            tag = 'GAIN'
        elif was_right and not now_right:
            fix_bad += 1
            tag = 'LOSS'
        else:
            continue
        details.append('%s: %s->%s real=%s %s [%s]' % (qid, my, new, real, tag, why))"""
assert old in c, 'pattern missing'
c = c.replace(old, new)
open(p, 'w', encoding='utf-8').write(c)
print('fixed detail block')
