import os
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt
from src.core.constants import AppColors
from src.core.assets import get_svg_pixmap
from src.views.components.elided_label import ElidedLabel

class SummaryCardWidget(QFrame):
    def __init__(self, title: str, value: str, icon_symbol: str = "", icon_bg: str = AppColors.PEMASUKAN, icon_fg: str = "#FFFFFF", svg_icon: str = None, title_color: str = None, parent=None):
        super().__init__(parent)
        self._title = title
        self._value = value
        self._icon_symbol = icon_symbol
        self._icon_bg = icon_bg
        self._icon_fg = icon_fg
        self._title_color = title_color or self._get_default_title_color(title)
        self._svg_icon = svg_icon or (icon_symbol if icon_symbol and icon_symbol.endswith(".svg") else None)
        self._setup_ui()

    def _get_default_title_color(self, title: str) -> str:
        t_upper = title.upper()
        if "PEMASUKAN" in t_upper or "SALDO" in t_upper:
            return "#7FAE82"
        elif "PENGELUARAN" in t_upper:
            return "#E57373"
        elif "TARGET" in t_upper:
            return "#9575CD"
        elif "BERSIH" in t_upper:
            return "#F59E0B"
        return AppColors.TEXT_SECONDARY

    def _setup_ui(self):
        self.setProperty("class", "card")
        self.setFixedHeight(102)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            SummaryCardWidget {{
                background-color: {AppColors.CARD_BG};
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 14px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Icon
        if self._svg_icon and os.path.exists(self._svg_icon):
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(44, 44)
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet("background: transparent; border: none;")
            icon_lbl.setPixmap(get_svg_pixmap(self._svg_icon, 44, 44))
            icon_lbl.setScaledContents(True)
            layout.addWidget(icon_lbl)
        else:
            icon_frame = QFrame()
            icon_frame.setFixedSize(44, 44)
            icon_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._icon_bg};
                    border-radius: 22px;
                    border: none;
                }}
            """)
            icon_layout = QHBoxLayout(icon_frame)
            icon_layout.setContentsMargins(0, 0, 0, 0)
            icon_lbl = QLabel(self._icon_symbol)
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet(f"font-size: 18px; color: {self._icon_fg}; font-weight: bold; background: transparent; border: none;")
            icon_layout.addWidget(icon_lbl)
            layout.addWidget(icon_frame)

        # Texts
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        text_layout.setAlignment(Qt.AlignVCenter)

        self.title_label = ElidedLabel(self._title.upper())
        self.title_label.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {self._title_color}; letter-spacing: 0.4px; background: transparent; border: none;")

        self.value_label = ElidedLabel(self._value)
        self.value_label.setStyleSheet(f"font-size: 19px; font-weight: 800; color: {AppColors.TEXT_PRIMARY}; background: transparent; border: none;")

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.value_label)

        layout.addLayout(text_layout, 1)

    def update_value(self, new_value: str):
        self.value_label.setText(new_value)
