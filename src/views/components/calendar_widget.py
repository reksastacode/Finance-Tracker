"""
Calendar Transaction Component.
Displays monthly calendar grid with transaction tag chips per day.
Implements event listeners for month changes based on system date.
"""
from datetime import date
import calendar
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QWidget
)
from PySide6.QtCore import Qt, Signal
from src.core.constants import AppColors
from src.core.utils import BULAN
from src.core.assets import AppIcons, create_svg_label

class CalendarWidget(QFrame):
    month_changed = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        today = date.today()
        self.year = today.year
        self.month = today.month
        self.events = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setProperty("class", "card")
        self.setFixedHeight(340)
        self.setStyleSheet(f"""
            CalendarWidget {{
                background-color: {AppColors.CARD_BG};
                border: 1px solid {AppColors.BORDER_CARD};
                border-radius: 12px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Header Row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title_icon = create_svg_label(AppIcons.DASHBOARD_KALENDER, 20, 20)
        title = QLabel("Kalender Transaksi")
        title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {AppColors.TEXT_PRIMARY}; background: transparent; border: none;")

        header_layout.addWidget(title_icon)
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Month Selector (Populated dynamically with current year's months)
        self.month_combo = QComboBox()
        month_items = [f"{m} {self.year}" for m in BULAN]
        self.month_combo.addItems(month_items)
        self.month_combo.setCurrentIndex(max(0, self.month - 1))
        self.month_combo.setFixedWidth(195)
        self.month_combo.setFixedHeight(34)
        self.month_combo.currentIndexChanged.connect(self._on_month_combo_changed)
        header_layout.addWidget(self.month_combo)

        layout.addLayout(header_layout)

        # Legend Row
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(12)

        def make_legend(color, text):
            frame = QFrame()
            frame.setStyleSheet("background: transparent; border: none;")
            fl = QHBoxLayout(frame)
            fl.setContentsMargins(0, 0, 0, 0)
            fl.setSpacing(4)
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent; border: none;")
            lbl = QLabel(text)
            lbl.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_SECONDARY}; font-weight: 600; background: transparent; border: none;")
            fl.addWidget(dot)
            fl.addWidget(lbl)
            return frame

        legend_layout.addWidget(make_legend(AppColors.TARGET, "Target"))
        legend_layout.addWidget(make_legend(AppColors.PEMASUKAN, "Pemasukan"))
        legend_layout.addWidget(make_legend(AppColors.PENGELUARAN, "Pengeluaran"))
        legend_layout.addStretch()
        layout.addLayout(legend_layout)

        # Calendar Grid Container
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent; border: none;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 2, 0, 0)
        self.grid_layout.setSpacing(3)

        layout.addWidget(self.grid_widget)
        layout.addStretch()
        self._rebuild_grid()

    def _on_month_combo_changed(self, idx: int):
        self.month = idx + 1
        self.month_changed.emit(self.year, self.month)
        self._rebuild_grid()

    def update_calendar_data(self, data: dict):
        self.year = data.get("year", date.today().year)
        self.month = data.get("month", date.today().month)
        self.events = data.get("events", {})
        self._rebuild_grid()

    def _rebuild_grid(self):
        # Clear existing grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Day Headers (Minggu to Sabtu)
        days = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
        for col, day_name in enumerate(days):
            hdr = QLabel(day_name)
            hdr.setAlignment(Qt.AlignCenter)
            hdr.setFixedHeight(24)
            hdr.setStyleSheet(f"""
                QLabel {{
                    background-color: #D6E3D3;
                    color: {AppColors.SIDEBAR_TEXT};
                    font-size: 11px;
                    font-weight: 700;
                    border-radius: 4px;
                    border: none;
                }}
            """)
            self.grid_layout.addWidget(hdr, 0, col)

        # Month matrix (Sunday first: Sunday=6 in standard weekday, mapped to 0)
        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(self.year, self.month)

        for row_idx, week in enumerate(month_days):
            for col_idx, day_num in enumerate(week):
                cell = QFrame()
                cell.setFixedHeight(34)
                cell.setStyleSheet(f"""
                    QFrame {{
                        background-color: {'#FFFFFF' if day_num > 0 else 'transparent'};
                        border: 1px solid {'#F0EDE6' if day_num > 0 else 'transparent'};
                        border-radius: 4px;
                    }}
                """)
                cell_layout = QVBoxLayout(cell)
                cell_layout.setContentsMargins(3, 2, 3, 2)
                cell_layout.setSpacing(0)

                if day_num > 0:
                    day_lbl = QLabel(str(day_num))
                    day_lbl.setStyleSheet(f"font-size: 10px; color: {AppColors.TEXT_PRIMARY}; font-weight: 600; background: transparent; border: none;")
                    cell_layout.addWidget(day_lbl, 0, Qt.AlignLeft | Qt.AlignTop)

                    # Check for event tag
                    if day_num in self.events:
                        ev_list = self.events[day_num]
                        for ev in ev_list:
                            tag_lbl = QLabel(ev["label"])
                            tag_lbl.setStyleSheet(f"""
                                QLabel {{
                                    font-size: 9px;
                                    color: {ev['color']};
                                    font-weight: bold;
                                    background: transparent;
                                    border: none;
                                }}
                            """)
                            cell_layout.addWidget(tag_lbl, 0, Qt.AlignRight | Qt.AlignBottom)

                self.grid_layout.addWidget(cell, row_idx + 1, col_idx)
