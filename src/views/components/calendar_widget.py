"""
Calendar Transaction Component.
Displays monthly calendar grid with transaction tag chips per day.
Implements event listeners for month changes and fixed layout constraints.
"""
import calendar
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QWidget
)
from PySide6.QtCore import Qt, Signal
from src.core.constants import AppColors

class CalendarWidget(QFrame):
    month_changed = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.year = 2026
        self.month = 9  # September
        self.events = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setProperty("class", "card")
        self.setFixedHeight(310)
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

        title_icon = QLabel("📅")
        title_icon.setStyleSheet("font-size: 14px; background: transparent; border: none;")
        title = QLabel("Kalender Transaksi")
        title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {AppColors.TEXT_PRIMARY}; background: transparent; border: none;")

        header_layout.addWidget(title_icon)
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Month Selector (Width enlarged so text is never truncated)
        self.month_combo = QComboBox()
        self.month_combo.addItems([
            "Januari 2026", "Februari 2026", "Maret 2026", "April 2026",
            "Mei 2026", "Juni 2026", "Juli 2026", "Agustus 2026",
            "September 2026", "Oktober 2026", "November 2026", "Desember 2026"
        ])
        self.month_combo.setCurrentText("September 2026")
        self.month_combo.setFixedWidth(165)
        self.month_combo.setFixedHeight(32)
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
        self.grid_layout.setSpacing(2)

        layout.addWidget(self.grid_widget)
        layout.addStretch()
        self._rebuild_grid()

    def _on_month_combo_changed(self, idx: int):
        self.month = idx + 1
        self.month_changed.emit(self.year, self.month)
        self._rebuild_grid()

    def update_calendar_data(self, data: dict):
        self.year = data.get("year", 2026)
        self.month = data.get("month", 9)
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
            hdr.setFixedHeight(22)
            hdr.setStyleSheet(f"""
                QLabel {{
                    background-color: #D6E3D3;
                    color: {AppColors.SIDEBAR_TEXT};
                    font-size: 10px;
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
                cell.setFixedHeight(30)
                cell.setStyleSheet(f"""
                    QFrame {{
                        background-color: {'#FFFFFF' if day_num > 0 else 'transparent'};
                        border: 1px solid {'#F0EDE6' if day_num > 0 else 'transparent'};
                        border-radius: 4px;
                    }}
                """)
                cell_layout = QVBoxLayout(cell)
                cell_layout.setContentsMargins(2, 2, 2, 2)
                cell_layout.setSpacing(0)

                if day_num > 0:
                    day_lbl = QLabel(str(day_num))
                    day_lbl.setStyleSheet(f"font-size: 9px; color: {AppColors.TEXT_PRIMARY}; font-weight: 600; background: transparent; border: none;")
                    cell_layout.addWidget(day_lbl, 0, Qt.AlignLeft | Qt.AlignTop)

                    # Check for event tag
                    if day_num in self.events:
                        ev_list = self.events[day_num]
                        for ev in ev_list:
                            tag_lbl = QLabel(ev["label"])
                            tag_lbl.setStyleSheet(f"""
                                QLabel {{
                                    font-size: 8px;
                                    color: {ev['color']};
                                    font-weight: bold;
                                    background: transparent;
                                    border: none;
                                }}
                            """)
                            cell_layout.addWidget(tag_lbl, 0, Qt.AlignRight | Qt.AlignBottom)

                self.grid_layout.addWidget(cell, row_idx + 1, col_idx)
