"""
Constants and Enums for Keuangan Mandiri
Based on the color palette and design specifications.
"""
from enum import Enum

class AppColors:
    # Palette based on design PDF
    SIDEBAR_BG = "#A8BFA3"        # 🌿 Sage green
    BACKGROUND = "#F7F5F0"        # 🤍 Soft warm white/off-white
    CARD_BG = "#FFFFFF"           # ⬜ Pure white
    PRIMARY_BUTTON = "#7F9B7A"    # 🌱 Forest sage green
    PRIMARY_BUTTON_HOVER = "#6E8B69"
    PRIMARY_BUTTON_PRESSED = "#5D7A58"
    
    PEMASUKAN = "#7FAE8A"         # 🟢 Green income
    PEMASUKAN_LIGHT = "#E8F5E9"
    
    PENGELUARAN = "#C98787"       # 🔴 Coral red expense
    PENGELUARAN_LIGHT = "#FFEBEE"
    
    TARGET = "#A99ABF"            # 🟣 Lavender target
    TARGET_LIGHT = "#F3E5F5"
    
    TEXT_PRIMARY = "#2D3748"
    TEXT_SECONDARY = "#718096"
    TEXT_MUTED = "#A0AEC0"
    
    BORDER_LIGHT = "#E2E8F0"
    BORDER_CARD = "#EAE6DF"
    
    PRIORITY_TINGGI = "#E57373"
    PRIORITY_SEDANG = "#FFB74D"
    PRIORITY_RENDAH = "#81C784"
    
    SIDEBAR_TEXT = "#2E382D"
    SIDEBAR_ITEM_HOVER = "#9BB496"
    SIDEBAR_ITEM_ACTIVE = "#8EA789"


class TransactionType(str, Enum):
    PEMASUKAN = "Pemasukan"
    PENGELUARAN = "Pengeluaran"
    TARGET = "Target"


class TargetPriority(str, Enum):
    TINGGI = "Tinggi"
    SEDANG = "Sedang"
    RENDAH = "Rendah"


class ToastType(str, Enum):
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
