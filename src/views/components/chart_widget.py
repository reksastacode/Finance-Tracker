"""
Custom Financial Line Chart Component.
Uses QPainter and paintEvent to render multi-series charts (Pemasukan, Pengeluaran, Target).
Demonstrates visual lifecycle (paintEvent, resizeEvent) and event-driven data binding.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame
from PySide6.QtCore import Qt, QPointF, Signal, Slot
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from src.core.constants import AppColors

class ChartCanvas(QWidget):
    """Inner canvas rendering lines and points via paintEvent."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.labels = ["1 Sep 2026", "5 Sep 2026", "10 Sep 2026", "15 Sep 2026", "20 Sep 2026", "25 Sep 2026"]
        self.pemasukan = [1.0, 1.2, 2.0, 1.5, 2.2, 1.8]
        self.pengeluaran = [0.8, 0.9, 1.8, 1.9, 1.4, 2.7]
        self.target = [0.5, 1.5, 2.7, 3.8, 4.8, 5.2]
        self.max_val = 6.0

    def set_data(self, labels, pemasukan, pengeluaran, target, max_val=6.0):
        self.labels = labels
        self.pemasukan = pemasukan
        self.pengeluaran = pengeluaran
        self.target = target
        self.max_val = max(max_val, max(pemasukan + pengeluaran + target + [1.0]))
        self.update()  # Triggers paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        
        left_pad = 42
        right_pad = 24
        top_pad = 14
        bottom_pad = 28

        plot_w = w - left_pad - right_pad
        plot_h = h - top_pad - bottom_pad

        if plot_w <= 0 or plot_h <= 0:
            return

        # Y-Grid and labels
        y_steps = 6
        painter.setFont(QFont("Segoe UI", 9))
        
        for i in range(y_steps + 1):
            val = (self.max_val / y_steps) * i
            y_pos = top_pad + plot_h - (i * (plot_h / y_steps))

            painter.setPen(QPen(QColor("#F0EDE6"), 1, Qt.SolidLine))
            painter.drawLine(int(left_pad), int(y_pos), int(w - right_pad), int(y_pos))

            painter.setPen(QPen(QColor(AppColors.TEXT_SECONDARY)))
            label_str = f"{int(val)} jt" if val.is_integer() else f"{val:.1f} jt"
            painter.drawText(0, int(y_pos - 6), int(left_pad - 6), 14, Qt.AlignRight | Qt.AlignVCenter, label_str)

        # Draw series
        def draw_series(data, hex_color):
            if not data or len(data) < 2:
                return
            step_x = plot_w / (len(data) - 1)
            points = []
            for idx, val in enumerate(data):
                px = left_pad + idx * step_x
                py = top_pad + plot_h - (val / self.max_val * plot_h)
                points.append(QPointF(px, py))

            path = QPainterPath()
            path.moveTo(points[0])
            for i in range(len(points) - 1):
                p0 = points[i]
                p1 = points[i + 1]
                ctrl1 = QPointF(p0.x() + step_x / 2, p0.y())
                ctrl2 = QPointF(p1.x() - step_x / 2, p1.y())
                path.cubicTo(ctrl1, ctrl2, p1)

            pen = QPen(QColor(hex_color), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

            dot_brush = QBrush(QColor(hex_color))
            white_pen = QPen(QColor("#FFFFFF"), 2)
            painter.setPen(white_pen)
            painter.setBrush(dot_brush)
            for pt in points:
                painter.drawEllipse(pt, 4, 4)

        draw_series(self.target, AppColors.TARGET)
        draw_series(self.pengeluaran, AppColors.PENGELUARAN)
        draw_series(self.pemasukan, AppColors.PEMASUKAN)

        # X Labels
        if self.labels:
            step_x = plot_w / (len(self.labels) - 1) if len(self.labels) > 1 else plot_w
            painter.setPen(QPen(QColor(AppColors.TEXT_SECONDARY)))
            for idx, lbl in enumerate(self.labels):
                px = left_pad + idx * step_x
                painter.drawText(int(px - 40), int(h - bottom_pad + 6), 80, 20, Qt.AlignCenter, lbl)


class ChartWidget(QFrame):
    period_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setProperty("class", "card")
        self.setFixedHeight(310)
        self.setStyleSheet(f"""
            ChartWidget {{
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
        header_layout.setSpacing(12)

        title = QLabel("Grafik keuangan")
        title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {AppColors.TEXT_PRIMARY}; background: transparent; border: none;")
        header_layout.addWidget(title)

        header_layout.addStretch()

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

        header_layout.addWidget(make_legend(AppColors.PEMASUKAN, "Pemasukan"))
        header_layout.addWidget(make_legend(AppColors.PENGELUARAN, "Pengeluaran"))
        header_layout.addWidget(make_legend(AppColors.TARGET, "Target"))

        # Period Dropdown
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Minggu ini", "Bulan ini", "Tahun ini"])
        self.period_combo.setFixedWidth(125)
        self.period_combo.setFixedHeight(32)
        self.period_combo.currentTextChanged.connect(self.period_changed.emit)
        header_layout.addWidget(self.period_combo)

        layout.addLayout(header_layout)

        # Chart Canvas
        self.canvas = ChartCanvas(self)
        layout.addWidget(self.canvas)

    def update_chart_data(self, data: dict):
        labels = data.get("labels", [])
        pemasukan = data.get("pemasukan", [])
        pengeluaran = data.get("pengeluaran", [])
        target = data.get("target", [])
        max_val = data.get("max_val", 6.0)
        self.canvas.set_data(labels, pemasukan, pengeluaran, target, max_val)
