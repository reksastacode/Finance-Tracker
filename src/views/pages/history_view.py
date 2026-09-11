"""
History View.
Renders transaction history with statistical summary cards, dynamic filters,
and interactive data table with running balances and deletion actions.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QDateEdit, QScrollArea
)
from PySide6.QtCore import Qt, QDate, Slot
from src.core.constants import AppColors, TransactionType
from src.viewmodels.history_viewmodel import HistoryViewModel
from src.views.components.header import HeaderWidget
from src.views.components.summary_card import SummaryCardWidget

class HistoryView(QWidget):
    def __init__(self, viewmodel: HistoryViewModel, parent=None):
        super().__init__(parent)
        self.vm = viewmodel
        self._setup_ui()
        self._bind_viewmodel()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 1. Header
        self.header = HeaderWidget("RIWAYAT", "Lihat semua catatan pemasukan dan pengeluaranmu di sini!")
        main_layout.addWidget(self.header)

        # 2. Summary Cards Row
        summary_row = QHBoxLayout()
        summary_row.setSpacing(14)

        self.card_pemasukan = SummaryCardWidget("Total Pemasukan", "Rp. 10.000.000", "⬆", AppColors.PEMASUKAN)
        self.card_pengeluaran = SummaryCardWidget("Total Pengeluaran", "Rp. 3.200.000", "⬇", AppColors.PENGELUARAN)
        self.card_saldo_bersih = SummaryCardWidget("Saldo Bersih", "Rp. 6.800.000", "⚖️", "#E6AF2E")
        self.card_total_tx = SummaryCardWidget("Jumlah Transaksi", "12 Transaksi", "📄", "#5C6BC0")

        summary_row.addWidget(self.card_pemasukan)
        summary_row.addWidget(self.card_pengeluaran)
        summary_row.addWidget(self.card_saldo_bersih)
        summary_row.addWidget(self.card_total_tx)
        main_layout.addLayout(summary_row)

        # 3. Filter Bar
        filter_card = QFrame()
        filter_card.setStyleSheet(f"""
            QFrame {{
                background-color: {AppColors.CARD_BG};
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 12px;
            }}
        """)
        f_layout = QHBoxLayout(filter_card)
        f_layout.setContentsMargins(16, 12, 16, 12)
        f_layout.setSpacing(12)

        # Filter 1: Jenis Transaksi
        c1 = QVBoxLayout()
        c1.setSpacing(2)
        c1.addWidget(QLabel("Jenis Transaksi", styleSheet="font-size: 11px; font-weight: 600; color: #4A5568;"))
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Semua", "Pemasukan", "Pengeluaran", "Target"])
        self.combo_type.setFixedHeight(34)
        c1.addWidget(self.combo_type)
        f_layout.addLayout(c1, 1)

        # Filter 2: Kategori
        c2 = QVBoxLayout()
        c2.setSpacing(2)
        c2.addWidget(QLabel("Kategori", styleSheet="font-size: 11px; font-weight: 600; color: #4A5568;"))
        self.combo_cat = QComboBox()
        self.combo_cat.addItems(["Semua"])
        self.combo_cat.setFixedHeight(34)
        c2.addWidget(self.combo_cat)
        f_layout.addLayout(c2, 1)

        # Filter 3: Tanggal Mulai
        c3 = QVBoxLayout()
        c3.setSpacing(2)
        c3.addWidget(QLabel("Tanggal Mulai", styleSheet="font-size: 11px; font-weight: 600; color: #4A5568;"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate(2026, 8, 1))
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.start_date_edit.setFixedHeight(34)
        c3.addWidget(self.start_date_edit)
        f_layout.addLayout(c3, 1)

        # Filter 4: Tanggal Akhir
        c4 = QVBoxLayout()
        c4.setSpacing(2)
        c4.addWidget(QLabel("Tanggal Akhir", styleSheet="font-size: 11px; font-weight: 600; color: #4A5568;"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate(2026, 9, 2))
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.end_date_edit.setFixedHeight(34)
        c4.addWidget(self.end_date_edit)
        f_layout.addLayout(c4, 1)

        # Filter Button
        self.filter_btn = QPushButton("🔍 FILTER")
        self.filter_btn.setCursor(Qt.PointingHandCursor)
        self.filter_btn.setFixedHeight(34)
        self.filter_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppColors.PRIMARY_BUTTON};
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 700;
                border-radius: 8px;
                padding: 0 18px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {AppColors.PRIMARY_BUTTON_HOVER};
            }}
        """)
        self.filter_btn.clicked.connect(self._on_filter_clicked)

        # Add stretch above filter btn for alignment
        btn_box = QVBoxLayout()
        btn_box.setSpacing(2)
        btn_box.addWidget(QLabel(" "))
        btn_box.addWidget(self.filter_btn)
        f_layout.addLayout(btn_box)

        main_layout.addWidget(filter_card)

        # 4. Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Tanggal", "Jenis", "Kategori", "Keterangan", "Nominal", "Saldo Setelah", "Aksi"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        main_layout.addWidget(self.table)

    def _bind_viewmodel(self):
        self.vm.history_summary_updated.connect(self._on_summary_updated)
        self.vm.transactions_updated.connect(self._on_transactions_updated)
        self.vm.categories_for_filter_updated.connect(self._on_categories_filter_updated)

    def showEvent(self, event):
        super().showEvent(event)
        self.vm.refresh()

    def _on_filter_clicked(self):
        tx_type = self.combo_type.currentText()
        cat = self.combo_cat.currentText()
        s_date = self.start_date_edit.date().toString("dd/MM/yyyy")
        e_date = self.end_date_edit.date().toString("dd/MM/yyyy")
        self.vm.apply_filter(tx_type, cat, s_date, e_date)

    @Slot(list)
    def _on_categories_filter_updated(self, cat_names: list):
        current = self.combo_cat.currentText()
        self.combo_cat.clear()
        self.combo_cat.addItems(cat_names)
        if current in cat_names:
            self.combo_cat.setCurrentText(current)

    @Slot(dict)
    def _on_summary_updated(self, summary: dict):
        self.card_pemasukan.update_value(summary.get("total_pemasukan", "Rp 0"))
        self.card_pengeluaran.update_value(summary.get("total_pengeluaran", "Rp 0"))
        self.card_saldo_bersih.update_value(summary.get("saldo_bersih", "Rp 0"))
        self.card_total_tx.update_value(f"{summary.get('jumlah_transaksi', '0')} Transaksi")

    @Slot(list)
    def _on_transactions_updated(self, transactions: list):
        self.table.setRowCount(len(transactions))
        for row, tx in enumerate(transactions):
            # Tanggal
            t_item = QTableWidgetItem(tx["date"])
            t_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, t_item)

            # Jenis
            j_item = QTableWidgetItem(tx["type"])
            j_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, j_item)

            # Kategori
            k_item = QTableWidgetItem(tx["category"])
            k_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, k_item)

            # Keterangan
            d_item = QTableWidgetItem(tx["notes"])
            self.table.setItem(row, 3, d_item)

            # Nominal
            n_item = QTableWidgetItem(tx["nominal_formatted"])
            n_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, n_item)

            # Saldo Setelah
            s_item = QTableWidgetItem(tx["saldo_setelah"])
            s_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 5, s_item)

            # Aksi: Delete Button
            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(26, 24)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFCDD2;
                    border-radius: 4px;
                    border: none;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #EF9A9A;
                }
            """)
            tx_id = tx["id"]
            del_btn.clicked.connect(lambda checked, tid=tx_id: self.vm.delete_transaction(tid))

            cell_widget = QWidget()
            cw_l = QHBoxLayout(cell_widget)
            cw_l.setContentsMargins(0, 0, 0, 0)
            cw_l.setAlignment(Qt.AlignCenter)
            cw_l.addWidget(del_btn)
            self.table.setCellWidget(row, 6, cell_widget)
