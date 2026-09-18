from .bazi_tools import BaziToolkit
from .ziwei_tools import ZiweiToolkit
from .hybrid_tools import HybridMingliToolkit
from .divination_tools import LiuYaoToolkit, MeiHuaToolkit, QiMenToolkit, LiuRenToolkit
from .physiognomy_tools import PhysiognomyToolkit
from .fengshui_tools import FengShuiToolkit
from .calendar_engine import (
    TIANGAN, DIZHI, TIANGAN_IDX, DIZHI_IDX,
    WUXING_GAN, WUXING_ZHI, WUXING_SHENG, WUXING_KE,
    build_four_pillars, build_dayun, build_liunian,
    year_ganzhi, day_ganzhi_from_date, hour_ganzhi, month_ganzhi,
    shi_shen, five_element_strength, nayin,
)

ALL_TOOLKITS = {
    "八字": BaziToolkit,
    "紫微斗数": ZiweiToolkit,
    "混合路由": HybridMingliToolkit,
    "六爻": LiuYaoToolkit,
    "梅花易数": MeiHuaToolkit,
    "奇门遁甲": QiMenToolkit,
    "大六壬": LiuRenToolkit,
    "面相手相": PhysiognomyToolkit,
    "风水": FengShuiToolkit,
}

__all__ = [
    "BaziToolkit",
    "ZiweiToolkit",
    "HybridMingliToolkit",
    "LiuYaoToolkit",
    "MeiHuaToolkit",
    "QiMenToolkit",
    "LiuRenToolkit",
    "PhysiognomyToolkit",
    "FengShuiToolkit",
    "ALL_TOOLKITS",
]
