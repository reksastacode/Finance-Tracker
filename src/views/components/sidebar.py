"""
Sidebar Navigation Component.
Implements the green sidebar with rounded corners, dark green header box,
and reactive item selection matching the design UI.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QColor
from src.core.constants import AppColors

class SidebarButton(QPushButton):
    """Custom sidebar button with clean styling and active state."""
    def __init__(self, icon_str: str, text: str, page_idx: int, parent=None):
        super().__init__(parent)
        self.page_idx = page_idx
        self.setText(f"  {icon_str}   {text}" if icon_str else f"  {text}")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48)
        self._update_style(False)

    def _update_style(self, is_active: bool):
        if is_active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #587352;
                    border: none;
                    border-radius: 12px;
                    text-align: left;
                    padding-left: 16px;
                    font-size: 13px;
                    font-weight: 700;
                }
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 12px;
                    text-align: left;
                    padding-left: 16px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.18);
                    color: #FFFFFF;
                }}
            """)

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._update_style(checked)


class SidebarWidget(QWidget):
    page_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(220)
        self.buttons = []
        self._setup_ui()

    def _setup_ui(self):
        # Sidebar container styling with rounded right corners
        self.setStyleSheet(f"""
            SidebarWidget {{
                background-color: {AppColors.SIDEBAR_BG};
                border-top-right-radius: 24px;
                border-bottom-right-radius: 24px;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 20)
        layout.setSpacing(10)

        # 1. Top Branding Box (Dark Green Rounded Rectangle without emoji)
        brand_box = QFrame()
        brand_box.setStyleSheet("""
            QFrame {
                background-color: #728D6E;
                border-radius: 14px;
                border: none;
            }
        """)
        brand_layout = QVBoxLayout(brand_box)
        brand_layout.setContentsMargins(12, 14, 12, 14)
        brand_layout.setSpacing(2)
        brand_layout.setAlignment(Qt.AlignCenter)

        title_app = QLabel("KEUANGAN")
        title_app.setAlignment(Qt.AlignCenter)
        title_app.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 800; letter-spacing: 1.5px;")

        sub_app = QLabel("MANDIRI")
        sub_app.setAlignment(Qt.AlignCenter)
        sub_app.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 800; letter-spacing: 1.5px;")

        brand_layout.addWidget(title_app)
        brand_layout.addWidget(sub_app)
        layout.addWidget(brand_box)

        layout.addSpacing(10)

        # 2. Nav Items
        nav_items = [
            ("", "Dashboard", 0),
            ("", "Input Transaksi", 1),
            ("", "Kategori", 2),
            ("", "Riwayat", 3),
            ("", "Target Keuangan", 4),
        ]

        for icon_str, text, idx in nav_items:
            btn = SidebarButton(icon_str, text, idx, self)
            btn.clicked.connect(lambda checked, i=idx: self.select_page(i))
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Initial selection
        self.select_page(0)

    @Slot(int)
    def select_page(self, page_index: int):
        """Activates the button for page_index and emits navigation signal."""
        for btn in self.buttons:
            btn.setChecked(btn.page_idx == page_index)
        self.page_changed.emit(page_index)
