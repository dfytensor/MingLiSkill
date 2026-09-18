# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'E:\ming_li_skill\MingLiSkill\marriage_fix_v2.py'
c = open(p, encoding='utf-8').read()

# Fix A: correct accounting (wrong->wrong = 0)
old_d = """    if new and new != my:
        ok = new == real
        d = 1 if ok else -1
        if ok: fix_ok += 1
        else: fix_bad += 1"""
new_d = """    if new and new != my:
        was_right = (my == real)
        now_right = (new == real)
        if now_right and not was_right:
            fix_ok += 1
        elif was_right and not now_right:
            fix_bad += 1
        else:
            continue"""
assert old_d in c
c = c.replace(old_d, new_d)

# Fix B: S6 uses only pure-year options
old_y = """    year_opts = []
    for o in opts:
        m = re.search(r'(19|20)\\d\\d', o['text'])
        if m:
            year_opts.append((o['letter'], int(m.group(0))))"""
new_y = """    year_opts = []
    pure_year_opts = []
    for o in opts:
        m = re.search(r'(19|20)\\d\\d', o['text'])
        if m:
            year_opts.append((o['letter'], int(m.group(0))))
            if re.fullmatch(r'\\s*(19|20)\\d\\d\\s*年?\\s*', o['text']):
                pure_year_opts.append((o['letter'], int(m.group(0))))"""
assert old_y in c
c = c.replace(old_y, new_y)

# Fix C: S6 picks latest PURE year option
old_s6 = """                if any(any(r.startswith('S6') for r in rs) for rs in cands.values()):
                    latest = max(year_opts, key=lambda t: t[1])
                    return latest[0], 'S6武破晚婚→选最晚%d' % latest[1]"""
new_s6 = """                if any(any(r.startswith('S6') for r in rs) for rs in cands.values()) and pure_year_opts:
                    latest = max(pure_year_opts, key=lambda t: t[1])
                    return latest[0], 'S6武破晚婚→选最晚%d' % latest[1]"""
assert old_s6 in c
c = c.replace(old_s6, new_s6)

# Fix D: S7b official-star transparent on year GAN, higher priority than S7a
old_s7 = """            # S7: 配偶星到位(支本气=配偶星)
            if ZHI_HIDE.get(gz) and GAN_WX.get(ZHI_HIDE[gz][0]) == sw_wx:
                reasons.append('S7配偶星到位(%s)' % gz)"""
new_s7 = """            # S7b: 配偶星透于流年天干
            if GAN_WX.get(gg) == sw_wx:
                reasons.append('S7b配偶星透干(%s)' % gg)
            # S7a: 配偶星到位(支本气=配偶星)
            if ZHI_HIDE.get(gz) and GAN_WX.get(ZHI_HIDE[gz][0]) == sw_wx:
                reasons.append('S7配偶星到位(%s)' % gz)"""
assert old_s7 in c
c = c.replace(old_s7, new_s7)

# Fix E: wedding priority S1 > S7b > S7a
old_pri = """                for sig in ['S1', 'S7']:
                    for L, rs in sorted(cands.items()):
                        if any(r.startswith(sig) for r in rs):
                            return L, '; '.join(rs)"""
new_pri = """                for sig in ['S1', 'S7b', 'S7']:
                    for L, rs in sorted(cands.items()):
                        if any(r.startswith(sig) for r in rs):
                            return L, '; '.join(rs)"""
assert old_pri in c
c = c.replace(old_pri, new_pri)

# Fix F: ASCII output
old_out = """print('婚姻题修复: +%d / -%d' % (fix_ok, fix_bad))
print('全库: %d/115=%.1f%% → %d/115=%.1f%%' % (base_c, base_c/115*100, base_c+fix_ok-fix_bad, (base_c+fix_ok-fix_bad)/115*100))
for d in details:
    print(' ', d)"""
new_out = """print('MARRIAGE FIX: +%d / -%d / net %+d' % (fix_ok, fix_bad, fix_ok - fix_bad))
print('TOTAL: %d/115=%.1f%% -> %d/115=%.1f%%' % (base_c, base_c/115*100, base_c+fix_ok-fix_bad, (base_c+fix_ok-fix_bad)/115*100))
for d in details:
    print(' ', d.encode('ascii', 'replace').decode())"""
assert old_out in c
c = c.replace(old_out, new_out)

open(p, 'w', encoding='utf-8').write(c)
print('patched v2 OK')
