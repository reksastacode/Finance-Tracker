"""
Header Component.
Displays page titles, subtitles, and real-time formatted date badge based on user system clock.
"""
from datetime import date
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QSizePolicy
from PySide6.QtCore import Qt
from src.core.constants import AppColors
from src.core.utils import format_indonesian_date
from src.core.assets import AppIcons, create_svg_label

class HeaderWidget(QWidget):
    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._setup_ui(title, subtitle)

    def _setup_ui(self, title: str, subtitle: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Left: Title and Subtitle
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(2)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: 800; color: #587352; letter-spacing: 0.5px; background: transparent; border: none;")

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet(f"font-size: 13px; color: {AppColors.TEXT_SECONDARY}; background: transparent; border: none;")

        left_layout.addWidget(self.title_label)
        left_layout.addWidget(self.subtitle_label)
        layout.addLayout(left_layout)

        layout.addStretch()

        # Right: Fixed-size Date Badge with Calendar Icon showing real computer date
        date_badge = QFrame()
        date_badge.setFixedHeight(42)
        date_badge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        date_badge.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        date_layout = QHBoxLayout(date_badge)
        date_layout.setContentsMargins(14, 6, 14, 6)
        date_layout.setSpacing(10)

        cal_icon = create_svg_label(AppIcons.DASHBOARD_KALENDER, 18, 18)

        # Use current system date
        self.date_text = QLabel(format_indonesian_date(date.today()))
        self.date_text.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {AppColors.TEXT_PRIMARY}; background: transparent; border: none;")

        date_layout.addWidget(cal_icon)
        date_layout.addWidget(self.date_text)

        layout.addWidget(date_badge, 0, Qt.AlignVCenter)

    def set_title(self, title: str, subtitle: str):
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)

    def refresh_date(self):
        """Update date badge with current computer date."""
        self.date_text.setText(format_indonesian_date(date.today()))
