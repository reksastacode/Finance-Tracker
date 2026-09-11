"""
Transaction Input View.
Provides the form for adding income or expense records.
Demonstrates input listeners, live character counter, dynamic dropdown population,
and form lifecycle events.
"""
from datetime import date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QTextEdit,
    QPushButton, QFrame, QDateEdit, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QDate, Slot
from src.core.constants import AppColors, TransactionType
from src.core.utils import format_short_date, parse_rupiah, format_rupiah
from src.viewmodels.transaction_viewmodel import TransactionViewModel
from src.views.components.header import HeaderWidget

class TransactionInputView(QWidget):
    def __init__(self, viewmodel: TransactionViewModel, parent=None):
        super().__init__(parent)
        self.vm = viewmodel
        self._setup_ui()
        self._bind_viewmodel()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 1. Header
        self.header = HeaderWidget("INPUT TRANSAKSI", "Catat pemasukan dan pengeluaran di sini")
        main_layout.addWidget(self.header)

        # 2. Form Card Container (Centered)
        center_container = QWidget()
        center_layout = QHBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addStretch()

        form_card = QFrame()
        form_card.setProperty("class", "card")
        form_card.setFixedWidth(520)
        form_card.setStyleSheet(f"""
            QFrame {{
                background-color: {AppColors.CARD_BG};
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 16px;
            }}
        """)
        card_layout = QVBoxLayout(form_card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(16)

        # Form Title
        form_title = QLabel("FORM TRANSAKSI")
        form_title.setAlignment(Qt.AlignCenter)
        form_title.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {AppColors.TEXT_PRIMARY}; letter-spacing: 1px;")
        card_layout.addWidget(form_title)
        card_layout.addSpacing(4)

        # Field 1: Jenis Transaksi
        card_layout.addWidget(QLabel("Jenis transaksi", styleSheet="font-size: 12px; font-weight: 600; color: #4A5568;"))
        self.jenis_combo = QComboBox()
        self.jenis_combo.addItem("⬆  Pemasukan", TransactionType.PEMASUKAN)
        self.jenis_combo.addItem("⬇  Pengeluaran", TransactionType.PENGELUARAN)
        self.jenis_combo.setFixedHeight(38)
        card_layout.addWidget(self.jenis_combo)

        # Field 2: Nominal
        card_layout.addWidget(QLabel("Nominal", styleSheet="font-size: 12px; font-weight: 600; color: #4A5568;"))
        self.nominal_input = QLineEdit()
        self.nominal_input.setPlaceholderText("Rp 0")
        self.nominal_input.setFixedHeight(38)
        card_layout.addWidget(self.nominal_input)

        # Field 3: Pilih Kategori
        card_layout.addWidget(QLabel("Pilih Kategori", styleSheet="font-size: 12px; font-weight: 600; color: #4A5568;"))
        self.kategori_combo = QComboBox()
        self.kategori_combo.setFixedHeight(38)
        card_layout.addWidget(self.kategori_combo)

        # Field 4: Tanggal
        card_layout.addWidget(QLabel("Tanggal", styleSheet="font-size: 12px; font-weight: 600; color: #4A5568;"))
        self.tanggal_edit = QDateEdit()
        self.tanggal_edit.setCalendarPopup(True)
        self.tanggal_edit.setDate(QDate(2026, 7, 25)) # Mock date per design
        self.tanggal_edit.setDisplayFormat("dd/MM/yyyy")
        self.tanggal_edit.setFixedHeight(38)
        card_layout.addWidget(self.tanggal_edit)

        # Field 5: Keterangan (Opsional) + Counter Label
        keterangan_hdr = QHBoxLayout()
        keterangan_hdr.addWidget(QLabel("Keterangan (opsional)", styleSheet="font-size: 12px; font-weight: 600; color: #4A5568;"))
        keterangan_hdr.addStretch()
        card_layout.addLayout(keterangan_hdr)

        self.keterangan_input = QLineEdit()
        self.keterangan_input.setPlaceholderText("Tulis keterangan transaksi (opsional)")
        self.keterangan_input.setFixedHeight(38)
        self.keterangan_input.setMaxLength(100)
        card_layout.addWidget(self.keterangan_input)

        counter_layout = QHBoxLayout()
        counter_layout.addStretch()
        self.char_count_lbl = QLabel("0/100")
        self.char_count_lbl.setStyleSheet(f"font-size: 11px; color: {AppColors.TEXT_MUTED};")
        counter_layout.addWidget(self.char_count_lbl)
        card_layout.addLayout(counter_layout)

        card_layout.addSpacing(10)

        # Buttons (Batal & Simpan Transaksi)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(14)

        self.batal_btn = QPushButton("batal")
        self.batal_btn.setCursor(Qt.PointingHandCursor)
        self.batal_btn.setFixedHeight(40)
        self.batal_btn.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0;
                color: #4A5568;
                border-radius: 8px;
                font-weight: 700;
                border: none;
            }
            QPushButton:hover {
                background-color: #CBD5E0;
            }
        """)
        self.batal_btn.clicked.connect(self.vm.cancel_transaction)

        self.simpan_btn = QPushButton("simpan transaksi")
        self.simpan_btn.setCursor(Qt.PointingHandCursor)
        self.simpan_btn.setFixedHeight(40)
        self.simpan_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppColors.PRIMARY_BUTTON};
                color: #FFFFFF;
                border-radius: 8px;
                font-weight: 700;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {AppColors.PRIMARY_BUTTON_HOVER};
            }}
        """)
        self.simpan_btn.clicked.connect(self._on_simpan_clicked)

        btn_layout.addWidget(self.batal_btn, 1)
        btn_layout.addWidget(self.simpan_btn, 2)
        card_layout.addLayout(btn_layout)

        center_layout.addWidget(form_card)
        center_layout.addStretch()

        main_layout.addWidget(center_container)
        main_layout.addStretch()

    def _bind_viewmodel(self):
        # ViewModel Signals -> View Slots
        self.vm.categories_loaded.connect(self._on_categories_loaded)
        self.vm.character_count_changed.connect(self._on_char_count_changed)
        self.vm.formatted_amount_changed.connect(self._on_formatted_amount_changed)
        self.vm.transaction_saved.connect(self._on_transaction_saved)
        self.vm.transaction_cancelled.connect(self._reset_form)

        # UI Events -> ViewModel Slots
        self.jenis_combo.currentIndexChanged.connect(self._on_jenis_changed)
        self.nominal_input.textChanged.connect(self.vm.on_amount_text_changed)
        self.keterangan_input.textChanged.connect(self.vm.on_notes_text_changed)

    def showEvent(self, event):
        super().showEvent(event)
        self._on_jenis_changed()

    def _on_jenis_changed(self):
        curr_data = self.jenis_combo.currentData() or TransactionType.PEMASUKAN
        self.vm.load_categories_for_type(curr_data)

    @Slot(list)
    def _on_categories_loaded(self, categories: list):
        self.kategori_combo.clear()
        for cat in categories:
            self.kategori_combo.addItem(cat)

    @Slot(int, int)
    def _on_char_count_changed(self, current_len: int, max_len: int):
        self.char_count_lbl.setText(f"{current_len}/{max_len}")

    @Slot(str)
    def _on_formatted_amount_changed(self, formatted: str):
        if self.nominal_input.text() != formatted:
            self.nominal_input.blockSignals(True)
            self.nominal_input.setText(formatted)
            self.nominal_input.blockSignals(False)

    def _on_simpan_clicked(self):
        tx_type = self.jenis_combo.currentData() or TransactionType.PEMASUKAN
        raw_amt = self.nominal_input.text()
        category = self.kategori_combo.currentText()
        dt_str = self.tanggal_edit.date().toString("dd/MM/yyyy")
        notes = self.keterangan_input.text()

        self.vm.save_transaction(tx_type, raw_amt, category, dt_str, notes)

    @Slot(bool, str)
    def _on_transaction_saved(self, success: bool, message: str):
        if success:
            self._reset_form()

    def _reset_form(self):
        self.nominal_input.blockSignals(True)
        self.nominal_input.setText("")
        self.nominal_input.blockSignals(False)
        self.keterangan_input.setText("")
        self.char_count_lbl.setText("0/100")
