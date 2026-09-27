from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from src.core.constants import AppColors
from src.core.assets import AppIcons, get_svg_icon, create_svg_label

class SidebarButton(QPushButton):
    """Custom sidebar button with clean styling and active state."""
    def __init__(self, svg_icon_path: str, text: str, page_idx: int, parent=None):
        super().__init__(parent)
        self.page_idx = page_idx
        self.setText(f"   {text}")
        if svg_icon_path:
            self.setIcon(get_svg_icon(svg_icon_path, 22, 22))
            self.setIconSize(QSize(22, 22))
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(52)
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
                    padding-left: 18px;
                    font-size: 14px;
                    font-weight: 800;
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
                    padding-left: 18px;
                    font-size: 14px;
                    font-weight: 700;
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
        self.setFixedWidth(240)
        self.buttons = []
        self._setup_ui()

    def _setup_ui(self):
        # Sidebar container styling with rounded right corners
        self.setStyleSheet(f"""
            SidebarWidget {{
                background-color: {AppColors.SIDEBAR_BG};
                border-top-right-radius: 28px;
                border-bottom-right-radius: 28px;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 20)
        layout.setSpacing(10)

        # 1. Top Branding Box (Dark Green Rounded Rectangle with Logo)
        brand_box = QFrame()
        brand_box.setStyleSheet("""
            QFrame {
                background-color: #728D6E;
                border-radius: 14px;
                border: none;
            }
        """)
        brand_layout = QHBoxLayout(brand_box)
        brand_layout.setContentsMargins(12, 12, 12, 12)
        brand_layout.setSpacing(10)
        brand_layout.setAlignment(Qt.AlignCenter)

        coin_logo = create_svg_label(AppIcons.DASHBOARD_SALDO, 34, 34)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        text_col.setAlignment(Qt.AlignVCenter)

        title_app = QLabel("KEUANGAN")
        title_app.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 800; letter-spacing: 1.2px; background: transparent; border: none;")

        sub_app = QLabel("MANDIRI")
        sub_app.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 800; letter-spacing: 1.2px; background: transparent; border: none;")

        text_col.addWidget(title_app)
        text_col.addWidget(sub_app)

        brand_layout.addWidget(coin_logo)
        brand_layout.addLayout(text_col)
        layout.addWidget(brand_box)

        layout.addSpacing(10)

        # 2. Nav Items
        nav_items = [
            (AppIcons.DASHBOARD_MENU, "Dashboard", 0),
            (AppIcons.INPUT_TRANSAKSI_MENU, "Input Transaksi", 1),
            (AppIcons.KATEGORI_MENU, "Kategori", 2),
            (AppIcons.RIWAYAT_MENU, "Riwayat", 3),
            (AppIcons.TARGET_MENU, "Target Keuangan", 4),
        ]

        for svg_path, text, idx in nav_items:
            btn = SidebarButton(svg_path, text, idx, self)
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
