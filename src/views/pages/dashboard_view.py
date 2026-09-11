"""
Dashboard View.
Implements the main dashboard page, connecting UI components to DashboardViewModel
via PySide6 Signals & Slots.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt, Slot
from src.core.constants import AppColors
from src.core.event_bus import event_bus
from src.viewmodels.dashboard_viewmodel import DashboardViewModel
from src.views.components.header import HeaderWidget
from src.views.components.summary_card import SummaryCardWidget
from src.views.components.chart_widget import ChartWidget
from src.views.components.calendar_widget import CalendarWidget

class DashboardView(QWidget):
    def __init__(self, viewmodel: DashboardViewModel, parent=None):
        super().__init__(parent)
        self.vm = viewmodel
        self._setup_ui()
        self._bind_viewmodel()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Scroll Area for responsive scrolling on smaller screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(16)

        # 1. Header
        self.header = HeaderWidget("DASHBOARD", "Selamat datang kembali")
        layout.addWidget(self.header)

        # 2. Top Summary KPI Cards Row
        summary_row = QHBoxLayout()
        summary_row.setSpacing(14)

        self.card_saldo = SummaryCardWidget("Saldo Saat Ini", "Rp 12.000.000", "$", AppColors.PEMASUKAN)
        self.card_pemasukan = SummaryCardWidget("Total Pemasukan", "Rp 1.000.000", "⬆", AppColors.PEMASUKAN)
        self.card_pengeluaran = SummaryCardWidget("Total Pengeluaran", "Rp 800.000", "⬇", AppColors.PENGELUARAN)
        self.card_target = SummaryCardWidget("Total Target", "Rp 5.000.000", "🎯", AppColors.TARGET)

        summary_row.addWidget(self.card_saldo)
        summary_row.addWidget(self.card_pemasukan)
        summary_row.addWidget(self.card_pengeluaran)
        summary_row.addWidget(self.card_target)
        layout.addLayout(summary_row)

        # 3. Middle Row: Chart (Left) + Calendar (Right)
        mid_row = QHBoxLayout()
        mid_row.setSpacing(14)

        self.chart_widget = ChartWidget()
        self.calendar_widget = CalendarWidget()

        mid_row.addWidget(self.chart_widget, 3)
        mid_row.addWidget(self.calendar_widget, 2)
        layout.addLayout(mid_row)

        # 4. Bottom Row: Target Keuangan (Left) + Transaksi Terbaru (Right)
        btm_row = QHBoxLayout()
        btm_row.setSpacing(14)

        # Bottom Left: Target Keuangan Card
        self.target_box = QFrame()
        self.target_box.setProperty("class", "card")
        self.target_box.setStyleSheet(f"""
            QFrame {{
                background-color: {AppColors.CARD_BG};
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 12px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        tb_layout = QVBoxLayout(self.target_box)
        tb_layout.setContentsMargins(16, 14, 16, 14)
        tb_layout.setSpacing(10)

        tb_hdr = QHBoxLayout()
        tb_icon = QLabel("🎯")
        tb_title = QLabel("Target Keuangan")
        tb_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {AppColors.TEXT_PRIMARY}; background: transparent; border: none;")
        tb_hdr.addWidget(tb_icon)
        tb_hdr.addWidget(tb_title)
        tb_hdr.addStretch()

        see_all_target_btn = QPushButton("Lihat Semua")
        see_all_target_btn.setCursor(Qt.PointingHandCursor)
        see_all_target_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppColors.PRIMARY_BUTTON};
                color: #FFFFFF;
                font-size: 11px;
                font-weight: 700;
                border-radius: 6px;
                padding: 4px 12px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {AppColors.PRIMARY_BUTTON_HOVER};
            }}
        """)
        see_all_target_btn.clicked.connect(lambda: event_bus.navigation_requested.emit(4))
        tb_hdr.addWidget(see_all_target_btn)
        tb_layout.addLayout(tb_hdr)

        self.target_items_layout = QVBoxLayout()
        self.target_items_layout.setSpacing(10)
        tb_layout.addLayout(self.target_items_layout)
        btm_row.addWidget(self.target_box, 1)

        # Bottom Right: Transaksi Terbaru Card
        self.recent_box = QFrame()
        self.recent_box.setProperty("class", "card")
        self.recent_box.setStyleSheet(f"""
            QFrame {{
                background-color: {AppColors.CARD_BG};
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 12px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        rb_layout = QVBoxLayout(self.recent_box)
        rb_layout.setContentsMargins(16, 14, 16, 14)
        rb_layout.setSpacing(10)

        rb_hdr = QHBoxLayout()
        rb_icon = QLabel("📋")
        rb_title = QLabel("Transaksi Terbaru")
        rb_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {AppColors.TEXT_PRIMARY};")
        rb_hdr.addWidget(rb_icon)
        rb_hdr.addWidget(rb_title)
        rb_hdr.addStretch()

        see_all_hist_btn = QPushButton("Lihat Semua Riwayat")
        see_all_hist_btn.setCursor(Qt.PointingHandCursor)
        see_all_hist_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppColors.PRIMARY_BUTTON};
                color: #FFFFFF;
                font-size: 11px;
                font-weight: 700;
                border-radius: 6px;
                padding: 4px 12px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {AppColors.PRIMARY_BUTTON_HOVER};
            }}
        """)
        see_all_hist_btn.clicked.connect(lambda: event_bus.navigation_requested.emit(3))
        rb_hdr.addWidget(see_all_hist_btn)
        rb_layout.addLayout(rb_hdr)

        self.recent_items_layout = QVBoxLayout()
        self.recent_items_layout.setSpacing(8)
        rb_layout.addLayout(self.recent_items_layout)
        btm_row.addWidget(self.recent_box, 1)

        layout.addLayout(btm_row)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _bind_viewmodel(self):
        """Connects ViewModel signals to UI update slots."""
        self.vm.summary_updated.connect(self._on_summary_updated)
        self.vm.chart_data_updated.connect(self.chart_widget.update_chart_data)
        self.vm.calendar_data_updated.connect(self.calendar_widget.update_calendar_data)
        self.vm.recent_transactions_updated.connect(self._on_recent_tx_updated)
        self.vm.targets_preview_updated.connect(self._on_targets_preview_updated)

        # View events -> ViewModel slots
        self.chart_widget.period_changed.connect(self.vm.set_chart_period)
        self.calendar_widget.month_changed.connect(self.vm.set_calendar_month)

    def showEvent(self, event):
        """Component lifecycle hook: refresh data whenever this view is shown."""
        super().showEvent(event)
        self.vm.refresh()

    @Slot(dict)
    def _on_summary_updated(self, data: dict):
        self.card_saldo.update_value(data.get("saldo_saat_ini", "Rp 0"))
        self.card_pemasukan.update_value(data.get("total_pemasukan", "Rp 0"))
        self.card_pengeluaran.update_value(data.get("total_pengeluaran", "Rp 0"))
        self.card_target.update_value(data.get("total_target", "Rp 0"))

    @Slot(list)
    def _on_targets_preview_updated(self, targets: list):
        # Clear items
        while self.target_items_layout.count():
            child = self.target_items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for t in targets:
            item = QFrame()
            item.setStyleSheet("background: #FAF8F5; border-radius: 8px; border: 1px solid #F0EDE6;")
            il = QHBoxLayout(item)
            il.setContentsMargins(10, 8, 10, 8)
            il.setSpacing(10)

            # Left Col
            left_c = QVBoxLayout()
            left_c.setSpacing(2)
            name_l = QLabel(t["name"])
            name_l.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {AppColors.TEXT_PRIMARY};")
            amt_l = QLabel(f"{t['collected_formatted']} / {t['target_formatted']}")
            amt_l.setStyleSheet(f"font-size: 11px; color: {AppColors.TEXT_SECONDARY};")
            left_c.addWidget(name_l)
            left_c.addWidget(amt_l)

            # Middle Col: Progress
            mid_c = QVBoxLayout()
            mid_c.setSpacing(2)
            pbar = QProgressBar()
            pbar.setRange(0, 100)
            pbar.setValue(t["progress_percent"])
            pbar.setTextVisible(False)
            pbar.setFixedHeight(5)
            pct_l = QLabel(f"{t['progress_percent']}%")
            pct_l.setAlignment(Qt.AlignCenter)
            pct_l.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_SECONDARY}; font-weight: 600;")
            mid_c.addWidget(pbar)
            mid_c.addWidget(pct_l)

            # Right: Isi Target Button
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
            t_id = t["id"]
            isi_btn.clicked.connect(lambda checked, tid=t_id: event_bus.open_isi_target_requested.emit(tid))

            il.addLayout(left_c, 2)
            il.addLayout(mid_c, 2)
            il.addWidget(isi_btn)
            self.target_items_layout.addWidget(item)

    @Slot(list)
    def _on_recent_tx_updated(self, transactions: list):
        while self.recent_items_layout.count():
            child = self.recent_items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for tx in transactions:
            row = QFrame()
            row.setStyleSheet("background: transparent; border-bottom: 1px solid #F0EDE6;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(4, 6, 4, 6)
            rl.setSpacing(10)

            # Icon
            icon_str = "⬆" if tx["type"] == "Pemasukan" else ("⬇" if tx["type"] == "Pengeluaran" else "🎯")
            icon_lbl = QLabel(icon_str)
            icon_lbl.setStyleSheet(f"color: {tx['color']}; font-size: 13px; font-weight: bold;")

            # Title & Subtitle
            t_col = QVBoxLayout()
            t_col.setSpacing(1)
            title = QLabel(tx["title"])
            title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {AppColors.TEXT_PRIMARY};")
            cat_type = QLabel(f"{tx['category']} • {tx['type']}")
            cat_type.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_SECONDARY};")
            t_col.addWidget(title)
            t_col.addWidget(cat_type)

            # Amount & Date
            r_col = QVBoxLayout()
            r_col.setSpacing(1)
            amt = QLabel(tx["amount_formatted"])
            amt.setAlignment(Qt.AlignRight)
            amt.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {tx['color']};")
            dt = QLabel(tx["date"])
            dt.setAlignment(Qt.AlignRight)
            dt.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_SECONDARY};")
            r_col.addWidget(amt)
            r_col.addWidget(dt)

            rl.addWidget(icon_lbl)
            rl.addLayout(t_col)
            rl.addStretch()
            rl.addLayout(r_col)

            self.recent_items_layout.addWidget(row)
