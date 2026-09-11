"""
Summary Card Component.
Displays KPI metric with an icon badge, title label, and big currency/count value.
"""
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from src.core.constants import AppColors

class SummaryCardWidget(QFrame):
    def __init__(self, title: str, value: str, icon_symbol: str, icon_bg: str, icon_fg: str = "#FFFFFF", parent=None):
        super().__init__(parent)
        self._title = title
        self._value = value
        self._icon_symbol = icon_symbol
        self._icon_bg = icon_bg
        self._icon_fg = icon_fg
        self._setup_ui()

    def _setup_ui(self):
        self.setProperty("class", "card")
        self.setFixedHeight(88)
        self.setStyleSheet(f"""
            SummaryCardWidget {{
                background-color: {AppColors.CARD_BG};
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 12px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Icon Circle
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

        # Texts
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignVCenter)

        self.title_label = QLabel(self._title.upper())
        self.title_label.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {AppColors.TEXT_SECONDARY}; letter-spacing: 0.5px; background: transparent; border: none;")

        self.value_label = QLabel(self._value)
        self.value_label.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {AppColors.TEXT_PRIMARY}; background: transparent; border: none;")

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.value_label)

        layout.addWidget(icon_frame)
        layout.addLayout(text_layout)
        layout.addStretch()

    def update_value(self, new_value: str):
        self.value_label.setText(new_value)
