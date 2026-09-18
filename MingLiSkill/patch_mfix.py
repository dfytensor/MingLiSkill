# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'E:\ming_li_skill\MingLiSkill\marriage_fix_v2.py'
c = open(p, encoding='utf-8').read()

# Fix 1: year zhi/gan formula
old_zhi = "def year_zhi(y):\n    return ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'][y % 12]"
new_zhi = "def year_zhi(y):\n    return ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'][(y - 4) % 12]"
assert old_zhi in c, 'zhi pattern not found'
c = c.replace(old_zhi, new_zhi)

old_gan = "def year_gan(y):\n    return ['庚','辛','壬','癸','甲','乙','丙','丁','戊','己'][(y - 1980) % 10] if y >= 1980 else ['庚','辛','壬','癸','甲','乙','丙','丁','戊','己'][(y - 1970) % 10]"
new_gan = "def year_gan(y):\n    return ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'][(y - 4) % 10]"
assert old_gan in c, 'gan pattern not found'
c = c.replace(old_gan, new_gan)

# Fix 2: drop unreliable married branch in S3
old_s3 = """        elif has_spouse_monthday:
            for o in opts:
                if any(k in o['text'] for k in ['已婚','嫁','娶']):
                    return o['letter'], 'S3:配偶星在月日→已婚'"""
new_s3 = "        # (已婚判定不可靠, 已移除, 只保留独身判定)"
assert old_s3 in c, 'S3 pattern not found'
c = c.replace(old_s3, new_s3)

# Fix 3: S6 must pick latest year
old_s6a = """            if is_wedding_q and any(s in fuqi for s in ['武曲','破军']):
                reasons.append('S6武破晚婚')"""
new_s6a = """            if is_wedding_q and any(s in fuqi for s in ['武曲','破军']):
                reasons.append('S6武破晚婚@%d' % y)"""
assert old_s6a in c, 'S6a pattern not found'
c = c.replace(old_s6a, new_s6a)

old_s6b = """                for sig in ['S1', 'S7', 'S6']:
                    for L, rs in sorted(cands.items()):
                        if any(r.startswith(sig) for r in rs):
                            return L, '; '.join(rs)"""
new_s6b = """                if any(any(r.startswith('S6') for r in rs) for rs in cands.values()):
                    latest = max(year_opts, key=lambda t: t[1])
                    return latest[0], 'S6武破晚婚→选最晚%d' % latest[1]
                for sig in ['S1', 'S7']:
                    for L, rs in sorted(cands.items()):
                        if any(r.startswith(sig) for r in rs):
                            return L, '; '.join(rs)"""
assert old_s6b in c, 'S6b pattern not found'
c = c.replace(old_s6b, new_s6b)

open(p, 'w', encoding='utf-8').write(c)
print('patched OK')
