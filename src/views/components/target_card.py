"""
Target Card Component.
Renders target progress, priority badge, amounts, and handles button events.
"""
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QCursor
from src.core.constants import AppColors

class TargetCardWidget(QFrame):
    isi_target_clicked = Signal(str)      # target_id
    edit_target_clicked = Signal(str)     # target_id
    delete_target_clicked = Signal(str)   # target_id

    def __init__(self, target_data: dict, parent=None):
        super().__init__(parent)
        self.target_data = target_data
        self._setup_ui()

    def _setup_ui(self):
        self.setProperty("class", "card")
        self.setMinimumWidth(210)
        self.setFixedHeight(180)
        self.setStyleSheet(f"""
            TargetCardWidget {{
                background-color: {AppColors.CARD_BG};
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Top: Title and Priority Badge
        top_layout = QHBoxLayout()
        title_lbl = QLabel(self.target_data.get("name", "Target"))
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {AppColors.TEXT_PRIMARY};")
        top_layout.addWidget(title_lbl)
        top_layout.addStretch()

        priority = self.target_data.get("priority", "Sedang")
        badge_bg = self.target_data.get("badge_bg", "#FFF8E1")
        badge_fg = self.target_data.get("badge_fg", "#FFB74D")

        badge = QLabel(priority)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {badge_bg};
                color: {badge_fg};
                font-size: 10px;
                font-weight: 700;
                padding: 2px 8px;
                border-radius: 6px;
            }}
        """)
        top_layout.addWidget(badge)
        layout.addLayout(top_layout)

        # Target & Deadline info
        target_amt = self.target_data.get("target_amount_formatted", "Rp 0")
        deadline = self.target_data.get("deadline_date", "-")

        info_lbl = QLabel(f"Target: {target_amt}\nBatas: {deadline}")
        info_lbl.setStyleSheet(f"font-size: 11px; color: {AppColors.TEXT_SECONDARY}; line-height: 14px;")
        layout.addWidget(info_lbl)

        # Collected Amount
        collected_amt = self.target_data.get("collected_amount_formatted", "Rp 0")
        amt_lbl = QLabel(collected_amt)
        amt_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {AppColors.TEXT_PRIMARY};")
        layout.addWidget(amt_lbl)

        # Progress bar and percent
        pct = self.target_data.get("progress_pct", 0)
        p_layout = QHBoxLayout()
        p_layout.setSpacing(8)

        pbar = QProgressBar()
        pbar.setRange(0, 100)
        pbar.setValue(pct)
        pbar.setTextVisible(False)
        pbar.setFixedHeight(6)
        pbar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #EDF2F7;
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {AppColors.TARGET};
                border-radius: 3px;
            }}
        """)

        pct_lbl = QLabel(f"{pct}%")
        pct_lbl.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_SECONDARY}; font-weight: 600;")

        p_layout.addWidget(pbar)
        p_layout.addWidget(pct_lbl)
        layout.addLayout(p_layout)

        # Sisa & Actions Row
        sisa_amt = self.target_data.get("sisa_formatted", "Rp 0")
        btm_layout = QHBoxLayout()
        btm_layout.setSpacing(6)

        sisa_lbl = QLabel(f"Sisa: {sisa_amt}")
        sisa_lbl.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_SECONDARY}; font-weight: 600;")
        btm_layout.addWidget(sisa_lbl)
        btm_layout.addStretch()

        # Isi Target button
        isi_btn = QPushButton("Isi Target")
        isi_btn.setCursor(Qt.PointingHandCursor)
        isi_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppColors.TARGET};
                color: #FFFFFF;
                font-size: 11px;
                font-weight: 700;
                border-radius: 6px;
                padding: 4px 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #9787AD;
            }}
        """)
        target_id = self.target_data.get("id", "")
        isi_btn.clicked.connect(lambda: self.isi_target_clicked.emit(target_id))
        btm_layout.addWidget(isi_btn)

        # Options button "..."
        more_btn = QPushButton(". . .")
        more_btn.setCursor(Qt.PointingHandCursor)
        more_btn.setFixedSize(28, 24)
        more_btn.setStyleSheet("""
            QPushButton {
                background-color: #F0EDE6;
                color: #718096;
                font-size: 10px;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """)
        more_btn.clicked.connect(lambda: self._show_options_menu(more_btn))
        btm_layout.addWidget(more_btn)

        layout.addLayout(btm_layout)

    def _show_options_menu(self, btn: QPushButton):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 16px;
                font-size: 12px;
                color: #2D3748;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #F7F5F0;
            }
        """)
        edit_action = QAction("Edit target", self)
        edit_action.triggered.connect(lambda: self.edit_target_clicked.emit(self.target_data.get("id", "")))

        delete_action = QAction("Hapus target", self)
        delete_action.triggered.connect(lambda: self.delete_target_clicked.emit(self.target_data.get("id", "")))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
