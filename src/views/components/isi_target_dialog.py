"""
Isi Target Modal Dialog.
Allows user to allocate funds from available balance into a savings target.
Demonstrates dialog events, input validation, and event submission.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from src.core.constants import AppColors
from src.core.mock_data import mock_store
from src.core.utils import format_rupiah, parse_rupiah

class IsiTargetDialog(QDialog):
    deposit_confirmed = Signal(str, str, str)  # (target_id, amount_str, notes)

    def __init__(self, target_data: dict, parent=None):
        super().__init__(parent)
        self.target_data = target_data
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(480, 420)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Dialog Box Container
        box = QFrame()
        box.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 16px;
            }}
        """)
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(24, 20, 24, 20)
        box_layout.setSpacing(14)

        # 1. Header with Close Button
        hdr_layout = QHBoxLayout()
        hdr_icon = QLabel("🎯")
        hdr_icon.setStyleSheet("font-size: 16px;")
        hdr_title = QLabel("Isi Target")
        hdr_title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {AppColors.TEXT_PRIMARY};")
        hdr_layout.addWidget(hdr_icon)
        hdr_layout.addWidget(hdr_title)
        hdr_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #A0AEC0;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                color: #2D3748;
            }
        """)
        close_btn.clicked.connect(self.reject)
        hdr_layout.addWidget(close_btn)
        box_layout.addLayout(hdr_layout)

        # 2. Target Name and Priority Badge
        t_row = QHBoxLayout()
        t_name = QLabel(self.target_data.get("name", ""))
        t_name.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {AppColors.TEXT_PRIMARY};")
        t_row.addWidget(t_name)
        t_row.addStretch()

        badge_bg = self.target_data.get("badge_bg", "#FFF8E1")
        badge_fg = self.target_data.get("badge_fg", "#FFB74D")
        t_badge = QLabel(self.target_data.get("priority", "Sedang"))
        t_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {badge_bg};
                color: {badge_fg};
                font-size: 10px;
                font-weight: 700;
                padding: 2px 8px;
                border-radius: 6px;
            }}
        """)
        t_row.addWidget(t_badge)
        box_layout.addLayout(t_row)

        # 3. Target Stats Box (Target, Terkumpul, Sisa)
        stats_box = QFrame()
        stats_box.setStyleSheet("""
            QFrame {
                background-color: #FBF9F5;
                border: 1px solid #F0EDE6;
                border-radius: 8px;
            }
        """)
        stats_layout = QHBoxLayout(stats_box)
        stats_layout.setContentsMargins(12, 10, 12, 10)

        def make_col(title, val):
            col = QVBoxLayout()
            col.setSpacing(2)
            lbl = QLabel(title)
            lbl.setStyleSheet(f"font-size: 11px; color: {AppColors.TEXT_SECONDARY}; font-weight: 600;")
            val_lbl = QLabel(val)
            val_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {AppColors.TEXT_PRIMARY};")
            col.addWidget(lbl)
            col.addWidget(val_lbl)
            return col

        stats_layout.addLayout(make_col("Target", self.target_data.get("target_amount_formatted", "Rp 0")))
        stats_layout.addLayout(make_col("Terkumpul", self.target_data.get("collected_amount_formatted", "Rp 0")))
        stats_layout.addLayout(make_col("Sisa", self.target_data.get("sisa_formatted", "Rp 0")))
        box_layout.addWidget(stats_box)

        # 4. Input Nominal
        box_layout.addWidget(QLabel("Nominal Tabungan", styleSheet=f"font-size: 12px; font-weight: 600; color: {AppColors.TEXT_PRIMARY};"))
        
        self.amt_input = QLineEdit()
        self.amt_input.setPlaceholderText("Masukkan nominal")
        self.amt_input.textChanged.connect(self._on_text_changed)
        box_layout.addWidget(self.amt_input)

        # Info text
        info_lbl = QLabel(f"ⓘ Nominal yang kamu masukkan akan ditambahkan ke target {self.target_data.get('name', '')}.")
        info_lbl.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_SECONDARY};")
        box_layout.addWidget(info_lbl)

        # 5. Saldo Tersedia Box
        saldo_box = QFrame()
        saldo_box.setStyleSheet("""
            QFrame {
                background-color: #E8F5E9;
                border-radius: 8px;
            }
        """)
        s_layout = QHBoxLayout(saldo_box)
        s_layout.setContentsMargins(12, 8, 12, 8)
        s_layout.setSpacing(10)

        wallet_icon = QLabel("👛")
        wallet_icon.setStyleSheet("font-size: 14px;")
        
        saldo_txt_layout = QVBoxLayout()
        saldo_txt_layout.setSpacing(1)
        s_title = QLabel("Saldo Tersedia")
        s_title.setStyleSheet("font-size: 10px; color: #2E7D32; font-weight: 600;")
        curr_balance_str = format_rupiah(mock_store.get_current_balance())
        s_val = QLabel(curr_balance_str)
        s_val.setStyleSheet("font-size: 13px; color: #1B5E20; font-weight: 800;")
        saldo_txt_layout.addWidget(s_title)
        saldo_txt_layout.addWidget(s_val)

        s_layout.addWidget(wallet_icon)
        s_layout.addLayout(saldo_txt_layout)
        s_layout.addStretch()
        box_layout.addWidget(saldo_box)

        # 6. Action Buttons (Batal & Tambahkan)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        batal_btn = QPushButton("Batal")
        batal_btn.setCursor(Qt.PointingHandCursor)
        batal_btn.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0;
                color: #4A5568;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 700;
                border: none;
            }
            QPushButton:hover {
                background-color: #CBD5E0;
            }
        """)
        batal_btn.clicked.connect(self.reject)

        add_btn = QPushButton("Tambahkan")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppColors.PRIMARY_BUTTON};
                color: #FFFFFF;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 700;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {AppColors.PRIMARY_BUTTON_HOVER};
            }}
        """)
        add_btn.clicked.connect(self._on_submit)

        btn_layout.addWidget(batal_btn)
        btn_layout.addWidget(add_btn)
        box_layout.addLayout(btn_layout)

        main_layout.addWidget(box)

    def _on_text_changed(self, text: str):
        # Auto format number
        val = parse_rupiah(text)
        if val > 0:
            formatted = format_rupiah(val, with_prefix=True)
            if self.amt_input.text() != formatted:
                self.amt_input.blockSignals(True)
                self.amt_input.setText(formatted)
                self.amt_input.blockSignals(False)

    def _on_submit(self):
        raw_text = self.amt_input.text()
        target_id = self.target_data.get("id", "")
        self.deposit_confirmed.emit(target_id, raw_text, f"Tabungan ke {self.target_data.get('name', '')}")
        self.accept()
