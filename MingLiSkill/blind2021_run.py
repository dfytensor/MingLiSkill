# -*- coding: utf-8 -*-
"""
blind2021_run.py — 2021年40道新题盲测（信号从未在这些题上挖掘过）
统一引擎: v12修复 + 婚姻v2/v3 + 财运W + 健康家庭HF + 事业性格学业C/P/EDU
无信号命中的题回退A(随机基线25%)。
"""
import io, sys, json, re
if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.ziwei_tools import ZiweiToolkit
from tools.calendar_engine import shi_shen
from marriage_fix_v2 import analyze as m2_analyze
from marriage_fix_v3 import analyze as m3_analyze

HTK = HybridMingliToolkit()
ZT = ZiweiToolkit()

GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
ZHI_HIDE = {'子':('癸',), '丑':('己','癸','辛'), '寅':('甲','丙','戊'), '卯':('乙',),
            '辰':('戊','乙','癸'), '巳':('丙','庚','戊'), '午':('丁','己'), '未':('己','丁','乙'),
            '申':('庚','壬','戊'), '酉':('辛',), '戌':('戊','辛','丁'), '亥':('壬','甲')}
WUXUE_KU = {'木':'未','火':'戌','金':'丑','水':'辰'}
CHONG = {'子午','午子','丑未','未丑','寅申','申寅','卯酉','酉卯','辰戌','戌辰','巳亥','亥巳'}
HEALTH_KW_Q = ['健康','病','癌','手术','抑郁','状况如何','受伤']
POSITIVE_KW = ['得奖','获奖','结婚','好机遇','喜事','升职','加薪','得财','顺利']

def year_gz(y):
    gz = ['甲子','乙丑','丙寅','丁卯','戊辰','己巳','庚午','辛未','壬申','癸酉',
          '甲戌','乙亥','丙子','丁丑','戊寅','己卯','庚辰','辛巳','壬午','癸未',
          '甲申','乙酉','丙戌','丁亥','戊子','己丑','庚寅','辛卯','壬辰','癸巳',
          '甲午','乙未','丙申','丁酉','戊戌','己亥','庚子','辛丑','壬寅','癸卯',
          '甲辰','乙巳','丙午','丁未','戊申','己酉','庚戌','辛亥','壬子','癸丑',
          '甲寅','乙卯','丙辰','丁巳','戊午','己未','庚申','辛酉','壬戌','癸亥']
    return gz[(y - 4) % 60]

def pick_year_option(opts, y):
    for o in opts:
        m = re.search(r'(19|20)\d\d', o['text'])
        if m and int(m.group(0)) == y:
            return o['letter']
    for o in opts:
        m = re.search(r'(19|20)\d\d', o['text'])
        if m:
            return o['letter']
    return None

def era_edu(y):
    if y <= 1960: return ['小学']
    if y <= 1989: return ['中学', '高中']
    if y <= 1997: return ['大学', '大专']
    return ['中六', '高中', '大学', '修读', '在读']

def adapt(q21):
    """2021格式 → ftb-like格式"""
    bi = {'year': q21['birth']['year'], 'month': q21['birth']['month'],
          'day': q21['birth']['day'], 'hour': q21['birth'].get('hour', 12),
          'gender': '男' if q21['gender'] == 'male' else '女'}
    opts = []
    for txt in q21['options']:
        letter = txt[0]
        body = txt[2:] if len(txt) > 2 and txt[1] in (' ', '.', '、') else txt[1:]
        opts.append({'letter': letter, 'text': body.strip()})
    fq = {'id': q21['question_id'], 'category': '', 'question': q21['question'],
          'options': opts, 'answer': q21['answer']}
    return bi, fq

def unified(q, bi):
    """返回 (letter, why) 或 (None, reason)"""
    opts = q['options']
    alltxt = q['question'] + ' ' + ' '.join(o['text'] for o in opts)
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour',12), gender=bi['gender'], category=q.get('category',''),
            question=q['question'], options_json=json.dumps(opts, ensure_ascii=False))
        b = json.loads(r).get('bazi', {})
    except:
        return None, 'chart fail'
    pillars = b.get('四柱', {})
    day_gan = b.get('日主','')
    if not day_gan: return None, 'no daymaster'
    day_wx = GAN_WX[day_gan]
    strong = b.get('日主强弱') == '身强'
    female = bi['gender'] in ('女','F','female')
    wx = b.get('五行力量', {})
    tot = sum(wx.values()) or 1
    seal_wx = {'木':'水','火':'木','土':'火','金':'土','水':'金'}[day_wx]
    guan_wx = {'木':'金','火':'水','土':'木','金':'火','水':'土'}[day_wx]
    food_wx = {'木':'火','火':'土','土':'金','金':'水','水':'木'}[day_wx]
    sw_wx = guan_wx if female else {'木':'土','火':'金','土':'水','金':'木','水':'火'}[day_wx]
    wealth_wx = {'木':'土','火':'金','土':'水','金':'木','水':'火'}[day_wx]
    gan_list = [pillars.get(p,'')[0:1] for p in ['年柱','月柱','日柱','时柱']]
    ss_gans = [shi_shen(day_gan, g) for g in gan_list if g]
    day_pillar = pillars.get('日柱','')
    day_zhi = day_pillar[1:2]

    # ===== v12 修复A: 机梁福德 → 玄学职业 =====
    try:
        r2 = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                       hour=bi.get('hour',12), gender=bi['gender'])
        zw = json.loads(r2).get('十二宫', {})
        smap = {k: (v.get('主星',[]) if isinstance(v,dict) else v) for k,v in zw.items()}
    except:
        smap = {}
    fude = smap.get('福德', [])
    fd_text = json.dumps(fude, ensure_ascii=False)
    if ('机梁' in str(analyze_fude_cache(bi, smap)) if False else False):
        pass
    # 机梁同福德
    if '天机' in fude and '天梁' in fude:
        for o in opts:
            if any(k in o['text'] for k in ['命理','风水','玄学','算命','占卜','宗教','法师','八字']):
                return o['letter'], 'FIXA:机梁福德→玄学'

    # ===== 婚姻 v3 (含v2大多数信号) =====
    cat = '婚姻' if any(k in q['question'] for k in ['婚','結婚','夫妻','离婚','離婚','拍拖','恋爱','嫁','娶','配偶']) else ''
    q2 = dict(q); q2['category'] = cat
    new, why = m3_analyze(q2, bi)
    if new: return new, 'M3:' + why
    new, why = m2_analyze(q2, bi)
    if new: return new, 'M2:' + why

    # ===== 财运 W =====
    if any(k in alltxt for k in ['出身','家境','贫或富','出生家境']):
        year_zhi = pillars.get('年柱','')[1:2]
        benqi = ZHI_HIDE.get(year_zhi, (None,))[0]
        if GAN_WX.get(benqi) == wealth_wx:
            for o in opts:
                if any(k in o['text'] for k in ['富','有钱']) and '贫穷' not in o['text']:
                    return o['letter'], 'W1r:年支本气财→富'
    if any(k in alltxt for k in ['年薪','收入','财运','理财','身家']):
        cb = smap.get('财帛', [])
        nums = []
        for o in opts:
            m = re.search(r'(\d+)\s*(万|千万|千)', o['text'])
            if m:
                v = int(m.group(1))
                if '千万' in m.group(2): v *= 1000
                elif m.group(2) == '千': v /= 10
                nums.append((v, o['letter']))
        nums.sort()
        if any(s in cb for s in ['天府','武曲']) and len(nums) >= 3:
            return nums[len(nums)-2][1], 'W6:财帛天府武曲→第2高'
        elif any(s in cb for s in ['廉贞','贪狼']):
            for o in opts:
                if any(k in o['text'] for k in ['乱花','投机','没理财']):
                    return o['letter'], 'W6:财帛廉贪→乱花钱'
        elif not cb and len(nums) >= 3:
            return nums[len(nums)//2][1], 'W6:财帛无星→中档'
    if female and any(k in alltxt for k in ['花女人钱','倾家荡产','被骗','老千','对象类型','感情对象']):
        wpct = wx.get(wealth_wx, 0) / tot * 100
        if wpct < 8:
            for o in opts:
                if '花女人钱' in o['text']:
                    return o['letter'], 'W8b:财%.0f%%→花女人钱' % wpct
    if female and '家用' in alltxt:
        benqi_root = any(ZHI_HIDE.get(pillars.get(p,'')[1:2], (None,))[0] and GAN_WX.get(ZHI_HIDE[pillars.get(p,'')[1:2]][0]) == wealth_wx for p in ['年柱','月柱','日柱','时柱'])
        if benqi_root:
            for o in opts:
                if '家用充足' in o['text']:
                    return o['letter'], 'S9:财有本气根→家用充足'

    # ===== 事业/性格/学业 =====
    if any(k in q['question'] for k in ['学历','学业','教育程度']):
        compound = any(k in alltxt for k in ['婚姻','单身','已婚','离婚'])
        if not compound:
            tier = era_edu(bi['year'])
            for kw in tier:
                for o in opts:
                    if kw in o['text']:
                        return o['letter'], 'EDU:%d→%s' % (bi['year'], kw)
    if any(k in q['question'] for k in ['个性','性格']) and '装修' not in q['question']:
        has_pianyin = '偏印' in ss_gans
        has_shang = '伤官' in ss_gans
        has_caitou = any(s in ss_gans for s in ('正财','偏财'))
        has_food_tou = any(s in ('食神','伤官') for s in ss_gans)
        if has_pianyin and any(k in alltxt for k in ['内向','沉默','孤僻','独处','忧郁']):
            for o in opts:
                if any(k in o['text'] for k in ['内向','沉默','孤僻']):
                    return o['letter'], 'P1:偏印透→内向'
        if has_shang and has_caitou:
            for o in opts:
                if any(k in o['text'] for k in ['风流','女人缘','慷慨','迷人']):
                    return o['letter'], 'P2b:伤官+财→风流'
        if has_shang and any(k in alltxt for k in ['交际','外向','热情','乐于']):
            for o in opts:
                if any(k in o['text'] for k in ['交际','外向','乐于']):
                    return o['letter'], 'P2:伤官→外向'
        if strong and any(n in ('比肩','劫财') for n in ss_gans) and any('固执' in o['text'] for o in opts):
            for o in opts:
                if '固执' in o['text']:
                    return o['letter'], 'P3:身强比劫→固执'
        if '正财' in ss_gans and not has_food_tou and any(k in alltxt for k in ['谨慎','小心','冒险']):
            for o in opts:
                if '谨慎' in o['text'] or '小心' in o['text']:
                    return o['letter'], 'P4:正财→谨慎'
    if female and any(k in alltxt for k in ['家庭主妇']):
        spct = wx.get(guan_wx, 0) / tot * 100
        fpct = wx.get(food_wx, 0) / tot * 100
        if spct < 5 and fpct > 10:
            for o in opts:
                if '家庭主妇' in o['text']:
                    return o['letter'], 'C1:官弱食伤旺→主妇'
    if any(k in q['question'] for k in ['创业','开店','自行']):
        for o in opts:
            m = re.search(r'(19|20)\d\d', o['text'])
            if m:
                gz = year_gz(int(m.group(0)))
                if shi_shen(day_gan, gz[0]) == '七杀' and not strong:
                    return o['letter'], 'C2:七杀透+身弱→创业'
    if '没有发生' in q['question']:
        for ym in re.finditer(r'(19|20)\d\d', q['question']):
            gz = year_gz(int(ym.group(0)))
            yzhi = gz[1]
            guan_show = (GAN_WX.get(gz[0]) == guan_wx) or (ZHI_HIDE.get(yzhi) and GAN_WX.get(ZHI_HIDE[yzhi][0]) == guan_wx)
            if not guan_show:
                for o in opts:
                    if any(k in o['text'] for k in ['工作','升职','上班']):
                        return o['letter'], 'C4:官不现→工作没发生'
            break
    mq = re.search(r'(19|20)\d\d', q['question'])
    if mq:
        y = int(mq.group(0))
        gz = year_gz(y)
        ygan, yzhi = gz[0], gz[1]
        ss_g = shi_shen(day_gan, ygan)
        is_health_q = any(k in q['question'] for k in HEALTH_KW_Q)
        is_generic_q = ('发生' in q['question'] or '出现的时间' in q['question'] or '何时' in q['question']) and not is_health_q
        # H1
        if ss_g == '正印' and any(k in alltxt for k in ['抑郁','忧郁']):
            p = pick_year_option(opts, y) or next((o['letter'] for o in opts if '抑郁' in o['text']), None)
            if p: return p, 'H1:%s正印→抑郁' % gz
        # H5a
        if ss_g == '伤官':
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['意外','伤','病','癌','食药','骨折','车祸','撞'])), None)
            if cand: return cand, 'H5a:%s伤官→伤损' % gz
        # H5b
        if ss_g == '食神' and is_health_q:
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['病','癌','骨折','撞'])), None)
            if cand: return cand, 'H5b:%s食神+健康→病' % gz
        # H6
        if ss_g == '食神' and is_generic_q:
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in POSITIVE_KW)), None)
            if cand: return cand, 'H6:%s食神→喜事' % gz
        # D1
        if ss_g == '偏印' and any(k in alltxt for k in ['凶劫','灾','患癌','抑郁']):
            own = next((o['letter'] for o in opts if ('患癌' in o['text'] or '凶劫' in o['text']) and ('自己' in o['text'] or '命主' in o['text'])), None)
            if not own: own = pick_year_option(opts, y)
            if own: return own, 'D1:%s偏印→灾病' % gz
        # H3
        if female and any(k in alltxt for k in ['流产','堕胎']):
            zhi_ss_all = [shi_shen(day_gan, h) for h in ZHI_HIDE.get(yzhi, ())]
            if ss_g in ('食神','伤官') or any(s in ('食神','伤官') for s in zhi_ss_all):
                cand = next((o['letter'] for o in opts if '流产' in o['text'] or '堕胎' in o['text']), None)
                if cand: return cand, 'H3:%s食伤→流产' % gz
        # F3
        if any(k in alltxt for k in ['父亲','母亲']) and ZHI_HIDE.get(yzhi) and len(ZHI_HIDE[yzhi]) > 1:
            mid = ZHI_HIDE[yzhi][1]
            mid_ss = shi_shen(day_gan, mid)
            opt_years = {}
            for o in opts:
                for m2 in re.finditer(r'(19|20)\d\d', o['text']):
                    opt_years.setdefault(int(m2.group(0)), o['letter'])
            opt = opt_years.get(y)
            if opt:
                otext = next(o['text'] for o in opts if o['letter'] == opt)
                if mid_ss == '正印' and re.search(r'母亲[^。]{0,20}(去世|离世|亡|病逝)', otext) and not re.search(r'父亲[^。]{0,20}(去世|离世|亡)', otext):
                    return opt, 'F3:%s母星→母亡' % gz
                if mid_ss == '偏财' and re.search(r'父亲[^。]{0,20}(去世|离世|亡)', otext) and not re.search(r'母亲[^。]{0,20}(去世|离世|亡|病逝)', otext):
                    return opt, 'F3:%s父星→父亡' % gz
        # F1
        if any(k in alltxt for k in ['父亲']):
            ku = WUXUE_KU.get(wealth_wx)
            if ku and yzhi == ku:
                cand = next((o['letter'] for o in opts if re.search(r'父亲[^。]{0,20}(去世|离世|亡)', o['text'])), None)
                if cand: return cand, 'F1:%s父星入库→父亡' % gz
        # H2
        if any(k in alltxt for k in ['健康','确诊','手术','中风','去世','辞世','长辞']):
            if gz == pillars.get('年柱',''):
                p = pick_year_option(opts, y)
                if p: return p, 'H2:%s伏吟年柱' % gz
        # M3
        if (yzhi + day_zhi) in CHONG:
            for o in opts:
                if any(k in o['text'] for k in ['绿卡','移民','远距离旅行','搬','出国','外地']):
                    return o['letter'], 'M3:%s冲日支→迁移' % gz
        # C3
        if strong and any(k in alltxt for k in ['生意','事业','公司']):
            if ZHI_HIDE.get(yzhi) and GAN_WX.get(ZHI_HIDE[yzhi][0]) == guan_wx:
                for o in opts:
                    if any(k in o['text'] for k in ['蒸蒸日上','峰回路转','好机遇','得奖','顺利','升']):
                        return o['letter'], 'C3:%s官本气+身强→事业好' % gz
        # X1: 七杀透干年 + 伤病 → 手术/住院 (古典: 杀主病伤)
        if ss_g == '七杀':
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['开刀','住院','手术','伤'])), None)
            if cand: return cand, 'X1:%s七杀透→伤病' % gz
        # X2: 正官透干年 + 官非 → 官非 (古典: 官星动=见官)
        if ss_g == '正官':
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['官非','牢狱','警察','扣留','犯法'])), None)
            if cand: return cand, 'X2:%s官透→官非' % gz
        # X3: 偏印年 + 投资/生意 → 失利/不顺 (枭神夺食)
        if ss_g == '偏印':
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['失利','损失','不顺','赚不到钱','负债','停滞','失败'])), None)
            if cand: return cand, 'X3:%s偏印→停滞失利' % gz
        # X4: 劫财透干年 + 耗财 (古典: 劫财主破耗)
        if ss_g == '劫财':
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['耗财','损失','失利','负债','赚不到钱'])), None)
            if cand: return cand, 'X4:%s劫财→破耗' % gz
        # X5: 伤官年 + 小财 (伤官生财)
        if ss_g == '伤官':
            cand = next((o['letter'] for o in opts if any(k in o['text'] for k in ['赚得小财','小财','平中见顺'])), None)
            if cand: return cand, 'X5:%s伤官→技能小财' % gz
    return None, 'no signal'

def analyze_fude_cache(bi, smap):
    return []

def main():
    qs = json.load(open(r'E:\ming_li_skill\MingLiSkill\new_bench\bench2021_questions.json', encoding='utf-8'))
    correct = total = fired = fired_correct = 0
    details = []
    for q21 in qs:
        bi, q = adapt(q21)
        real = q['answer']
        pick, why = unified(q, bi)
        if pick is None:
            pick = 'A'  # 回退
            was_fired = False
        else:
            was_fired = True
        ok = pick == real
        total += 1
        correct += ok
        if was_fired:
            fired += 1
            fired_correct += ok
        details.append('%s %s->%s real=%s %s [%s]' % (q['id'], 'F' if was_fired else '.', pick, real, 'OK' if ok else 'X', why.encode('ascii','replace').decode()))
    print('BLIND 2021: %d/%d = %.1f%% (random=25%%)' % (correct, total, correct/total*100))
    print('signal-fired: %d/%d = %.1f%%' % (fired_correct, fired, fired_correct/max(fired,1)*100))
    print('fallback(A): %d questions' % (total - fired))
    for d in details:
        print(' ', d)

if __name__ == '__main__':
    main()
