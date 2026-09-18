# -*- coding: utf-8 -*-
"""
fix_tools.py — 修复三类系统性错误的工具
1. 福德宫分析器（玄学/精神/爱好信号）
2. 十神有无检查器（官杀=0→无事业心）
3. 天相正解（管理者≠秘书）
"""

def analyze_fude_palace(ziwei_palaces):
    """福德宫分析器：福德宫=精神世界/潜意识/爱好/玄学缘。
    天机+天梁=命理玄学缘！"""
    fude_stars = ziwei_palaces.get('福德', ziwei_palaces.get('福德宫', []))
    
    signals = []
    if '天机' in fude_stars:
        signals.append('天机在福德=喜欢研究思考，玄学缘')
    if '天梁' in fude_stars:
        signals.append('天梁在福德=荫星，关注精神层面/医药/宗教')
    if '天机' in fude_stars and '天梁' in fude_stars:
        signals.append('机梁同福德=强玄学命理宗教缘！可能从事命理风水')
    
    # 其他玄学信号
    all_stars = []
    for stars in ziwei_palaces.values():
        all_stars.extend(stars)
    if '天机' in all_stars and '天梁' in all_stars:
        if not any('机梁' in s for s in signals):
            signals.append('天机天梁成对=玄学研究天赋')
    
    return signals


def check_guan_sha_absence(ten_gods, wx):
    """官杀有无检查器：女命官杀=事业心+丈夫管束。
    官杀=0或极弱 → 无事业心/在家/无管束"""
    day_gan = list(ten_gods.get('日主', '甲'))[0] if ten_gods.get('日主') else '甲'
    
    # 官杀五行
    day_wx = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土',
              '己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}.get(day_gan, '木')
    # 克我者=官杀
    guan_wx = {'木':'金','火':'水','土':'木','金':'火','水':'土'}.get(day_wx, '')
    
    guan_count = wx.get(guan_wx, 0)
    total = sum(wx.values()) or 1
    guan_pct = guan_count / total * 100
    
    signals = []
    if guan_count == 0:
        signals.append('官杀五行(%s)=0！女命→无事业心/无夫管束/在家' % guan_wx)
    elif guan_pct < 5:
        signals.append('官杀五行(%s)极弱(%.1f%%)→事业心弱/不受管束' % (guan_wx, guan_pct))
    
    return signals, guan_count, guan_pct


# ============ 十神职业映射修正表 ============
# 修复刻板印象：每个十神有多种职业可能
SS_CAREER_FIX = {
    '天相': {
        '错误理解': '辅助→秘书',
        '正确理解': '天相=印星=掌印者=管理者/官员/老板/参谋长',
        '关键词': ['管理', '老板', '掌印', '官员', '主任', '经理'],
    },
    '太阳': {
        '错误理解': '热情→外交',
        '正确理解': '太阳=照顾/付出/男性→家庭主妇也可以(在家掌权照顾全家)',
        '关键词': ['照顾', '家庭', '付出', '管理'],
    },
    '食伤旺': {
        '错误理解': '食伤旺=厨师/艺术(五行刻板)',
        '正确理解': '食伤=想法多/表达/创造/分析→看日主和整体格局定方向',
        '关键词': ['想法', '分析', '创意', '表达', '白日梦'],
    },
    '七杀': {
        '错误理解': '七杀=偏门/暴力',
        '正确理解': '七杀=权威/开创/执行→也可是宗教修行(杀印相生)',
        '关键词': ['权威', '开创', '宗教', '执行'],
    },
}


def fix_career_interpretation(stars, ten_gods, wx, gender):
    """修正职业判断：综合所有信号，不用刻板印象。"""
    signals = []
    
    # 1. 官杀检查
    guan_signals, guan_count, guan_pct = check_guan_sha_absence(ten_gods, wx)
    signals += guan_signals
    
    # 2. 福德宫
    # (需要紫微数据，在外部传入)
    
    # 3. 天相修正
    if '天相' in str(ten_gods.values()) or '天相' in str(stars):
        signals.append('天相=掌印管理者(非秘书)')
    
    return signals
