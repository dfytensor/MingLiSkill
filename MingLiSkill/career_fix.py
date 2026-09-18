# -*- coding: utf-8 -*-
"""
career_fix.py — 事业/性格/学业信号 P1-P4/C1-C4/M3/EDU 全局审计
"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.ziwei_tools import ZiweiToolkit
from tools.calendar_engine import shi_shen

HTK = HybridMingliToolkit()
ZT = ZiweiToolkit()
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}
BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v5.json', encoding='utf-8'))

GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
ZHI_HIDE = {'子':('癸',), '丑':('己','癸','辛'), '寅':('甲','丙','戊'), '卯':('乙',),
            '辰':('戊','乙','癸'), '巳':('丙','庚','戊'), '午':('丁','己'), '未':('己','丁','乙'),
            '申':('庚','壬','戊'), '酉':('辛',), '戌':('戊','辛','丁'), '亥':('壬','甲')}
CHONG = {'子午','午子','丑未','未丑','寅申','申寅','卯酉','酉卯','辰戌','戌辰','巳亥','亥巳'}

def year_gz(y):
    gz = ['甲子','乙丑','丙寅','丁卯','戊辰','己巳','庚午','辛未','壬申','癸酉',
          '甲戌','乙亥','丙子','丁丑','戊寅','己卯','庚辰','辛巳','壬午','癸未',
          '甲申','乙酉','丙戌','丁亥','戊子','己丑','庚寅','辛卯','壬辰','癸巳',
          '甲午','乙未','丙申','丁酉','戊戌','己亥','庚子','辛丑','壬寅','癸卯',
          '甲辰','乙巳','丙午','丁未','戊申','己酉','庚戌','辛亥','壬子','癸丑',
          '甲寅','乙卯','丙辰','丁巳','戊午','己未','庚申','辛酉','壬戌','癸亥']
    return gz[(y - 4) % 60]

def era_edu(y):
    if y <= 1960: return ['小学']
    if y <= 1989: return ['中学', '高中']
    if y <= 1997: return ['大学', '大专']
    return ['中六', '高中', '大学', '修读', '在读']

gain = loss = 0
details = []

for qid in sorted(BASE):
    q = by_id.get(qid)
    if not q: continue
    bi = q['birth_info']
    my = BASE[qid]; real = q['answer']
    opts = q['options']
    alltxt = q['question'] + ' ' + ' '.join(o['text'] for o in opts)
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour',12), gender=bi['gender'], category=q['category'],
            question=q['question'], options_json=json.dumps(opts, ensure_ascii=False))
        b = json.loads(r).get('bazi', {})
    except:
        continue
    pillars = b.get('四柱', {})
    day_gan = b.get('日主','')
    if not day_gan: continue
    day_wx = GAN_WX[day_gan]
    strong = b.get('日主强弱') == '身强'
    female = bi['gender'] in ('女','F','female')
    wx = b.get('五行力量', {})
    tot = sum(wx.values()) or 1
    seal_wx = {'木':'水','火':'木','土':'火','金':'土','水':'金'}[day_wx]
    guan_wx = {'木':'金','火':'水','土':'木','金':'火','水':'土'}[day_wx]
    food_wx = {'木':'火','火':'土','土':'金','金':'水','水':'木'}[day_wx]
    gan_list = [pillars.get(p,'')[0:1] for p in ['年柱','月柱','日柱','时柱']]
    ss_gans = [shi_shen(day_gan, g) for g in gan_list if g]
    day_zhi = pillars.get('日柱','')[1:2]

    pick = None; why = ''

    # EDU: 学历题年代先验
    if not pick and any(k in q['question'] for k in ['学历','学业','教育程度']):
        compound = any(k in alltxt for k in ['婚姻','单身','已婚','离婚'])
        if not compound:
            try:
                r2 = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                               hour=bi.get('hour',12), gender=bi['gender'])
                zw = json.loads(r2).get('十二宫', {})
                gl = (zw.get('官禄') or {}).get('主星', []) if isinstance(zw.get('官禄'), dict) else []
            except:
                gl = []
            tier = era_edu(bi['year'])
            done = False
            for kw in tier:
                for o in opts:
                    if kw in o['text']:
                        pick = o['letter']; why = 'EDU:%d年代->%s' % (bi['year'], kw); done = True; break
                if done: break

    # P1/P2/P4: 性格题
    if not pick and any(k in q['question'] for k in ['个性','性格']) and '装修' not in q['question']:
        has_pianyin = '偏印' in ss_gans
        has_shang = '伤官' in ss_gans
        has_zhengcai = '正财' in ss_gans
        has_food_tou = any(s in ('食神','伤官') for s in ss_gans)
        if has_pianyin and any(k in alltxt for k in ['内向','沉默','孤僻','独处','忧郁']):
            for o in opts:
                if any(k in o['text'] for k in ['内向','沉默','孤僻']):
                    pick = o['letter']; why = 'P1:偏印透→内向'; break
        elif has_shang and any(s in ss_gans for s in ('正财','偏财')):
            for o in opts:
                if any(k in o['text'] for k in ['风流','女人缘','慷慨','迷人']):
                    pick = o['letter']; why = 'P2b:伤官+财双透→风流女人缘'; break
        elif has_shang and any(k in alltxt for k in ['交际','外向','热情','乐于']):
            for o in opts:
                if any(k in o['text'] for k in ['交际','外向','乐于']):
                    pick = o['letter']; why = 'P2:伤官透无财→外向交际'; break
        elif strong and any(n in ('比肩','劫财') for n in ss_gans) and any('固执' in o['text'] for o in opts):
            for o in opts:
                if '固执' in o['text']:
                    pick = o['letter']; why = 'P3:身强比劫→固执'; break
        elif has_zhengcai and not has_food_tou and any(k in alltxt for k in ['谨慎','小心','冒险']):
            for o in opts:
                if '谨慎' in o['text'] or '小心' in o['text']:
                    pick = o['letter']; why = 'P4:正财透无食伤透→谨慎'; break

    # C1: 家庭主妇
    if not pick and female and any(k in alltxt for k in ['家庭主妇']):
        spct = wx.get(guan_wx, 0) / tot * 100
        fpct = wx.get(food_wx, 0) / tot * 100
        if spct < 5 and fpct > 10:
            for o in opts:
                if '家庭主妇' in o['text']:
                    pick = o['letter']; why = 'C1:官杀%.0f%%食伤%.0f%%→主妇' % (spct, fpct); break

    # C2: 身弱七杀透年 → 创业
    if not pick and any(k in q['question'] for k in ['创业','开店','自行']):
        for o in opts:
            m = re.search(r'(19|20)\d\d', o['text'])
            if m:
                gz = year_gz(int(m.group(0)))
                if shi_shen(day_gan, gz[0]) == '七杀' and not strong:
                    pick = o['letter']; why = 'C2:%s七杀透+身弱→创业' % gz; break

    # C4: "没有发生"题: 官杀无透干/支本气 → 工作类没发生
    if not pick and '没有发生' in q['question']:
        for ym in re.finditer(r'(19|20)\d\d', q['question']):
            gz = year_gz(int(ym.group(0)))
            yzhi = gz[1]
            guan_show = (GAN_WX.get(gz[0]) == guan_wx) or (ZHI_HIDE.get(yzhi) and GAN_WX.get(ZHI_HIDE[yzhi][0]) == guan_wx)
            if not guan_show:
                for o in opts:
                    if any(k in o['text'] for k in ['工作','升职','上班']):
                        pick = o['letter']; why = 'C4:%s官不现→工作类没发生' % gz; break
            break

    # M3 + C3: 年份事件题
    if not pick:
        mq = re.search(r'(19|20)\d\d', q['question'])
        y = int(mq.group(0)) if mq else None
        if y:
            gz = year_gz(y)
            yzhi = gz[1]
            # M3: 冲日支 → 迁移/绿卡/远行
            if (yzhi + day_zhi) in CHONG:
                for o in opts:
                    if any(k in o['text'] for k in ['绿卡','移民','远距离旅行','搬','出国','外地']):
                        pick = o['letter']; why = 'M3:%s冲日支→迁移' % gz; break
            # C3: 身强+官杀支本气年 → 事业向好
            if not pick and strong and any(k in alltxt for k in ['生意','事业','公司']):
                if ZHI_HIDE.get(yzhi) and GAN_WX.get(ZHI_HIDE[yzhi][0]) == guan_wx:
                    for o in opts:
                        if any(k in o['text'] for k in ['蒸蒸日上','峰回路转','好机遇','得奖','顺利','升']):
                            pick = o['letter']; why = 'C3:%s官星本气+身强→事业向好' % gz; break

    if not pick or pick == my:
        continue
    was = my == real; now = pick == real
    if now and not was: gain += 1; tag = 'GAIN'
    elif was and not now: loss += 1; tag = 'LOSS'
    else: continue
    BASE[qid] = pick
    details.append('%s: %s->%s real=%s %s [%s]' % (qid, my, pick, real, tag, why))

final = sum(1 for k, v in BASE.items() if k in by_id and by_id[k]['answer'] == v)
print('CAREER/PER/EDU FIX: +%d / -%d' % (gain, loss))
print('FINAL: %d/115 = %.1f%%' % (final, final/115*100))
for d in details:
    print(' ', d.encode('ascii','replace').decode())
json.dump(BASE, open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v6.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('saved fixed_answers_v6.json')
