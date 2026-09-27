import os
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from src.core.constants import AppColors
from src.core.assets import get_svg_pixmap

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
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        # Icon
        if self._svg_icon and os.path.exists(self._svg_icon):
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(52, 52)
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet("background: transparent; border: none;")
            icon_lbl.setPixmap(get_svg_pixmap(self._svg_icon, 52, 52))
            icon_lbl.setScaledContents(True)
            layout.addWidget(icon_lbl)
        else:
            icon_frame = QFrame()
            icon_frame.setFixedSize(50, 50)
            icon_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._icon_bg};
                    border-radius: 25px;
                    border: none;
                }}
            """)
            icon_layout = QHBoxLayout(icon_frame)
            icon_layout.setContentsMargins(0, 0, 0, 0)
            icon_lbl = QLabel(self._icon_symbol)
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet(f"font-size: 20px; color: {self._icon_fg}; font-weight: bold; background: transparent; border: none;")
            icon_layout.addWidget(icon_lbl)
            layout.addWidget(icon_frame)

        # Texts
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        text_layout.setAlignment(Qt.AlignVCenter)

        self.title_label = QLabel(self._title.upper())
        self.title_label.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {self._title_color}; letter-spacing: 0.6px; background: transparent; border: none;")

        self.value_label = QLabel(self._value)
        self.value_label.setStyleSheet(f"font-size: 21px; font-weight: 800; color: {AppColors.TEXT_PRIMARY}; background: transparent; border: none;")

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.value_label)

        layout.addLayout(text_layout)
        layout.addStretch()

    def update_value(self, new_value: str):
        self.value_label.setText(new_value)
