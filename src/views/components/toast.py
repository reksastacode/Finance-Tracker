"""
Animated Floating Toast Notification.
Listens to global toast events and renders auto-dismissing banner.
Demonstrates QPropertyAnimation and QTimer event handling in PySide6.
"""
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Slot
from src.core.constants import AppColors

class ToastWidget(QFrame):
    def __init__(self, message: str, toast_type: str = "success", parent=None):
        super().__init__(parent)
        self.message = message
        self.toast_type = toast_type
        self._setup_ui()
        self._setup_animation()

    def _setup_ui(self):
        self.setFixedWidth(280)
        self.setFixedHeight(48)
        
        # Determine styling based on type
        if self.toast_type == "success":
            icon_char = "✓"
            icon_bg = "#4CAF50"
            border_col = "#C8E6C9"
            bg_col = "#E8F5E9"
            text_col = "#1B5E20"
        elif self.toast_type == "error":
            icon_char = "✕"
            icon_bg = "#E57373"
            border_col = "#FFCDD2"
            bg_col = "#FFEBEE"
            text_col = "#B71C1C"
        elif self.toast_type == "warning":
            icon_char = "!"
            icon_bg = "#FFB74D"
            border_col = "#FFE0B2"
            bg_col = "#FFF3E0"
            text_col = "#E65100"
        else: # info
            icon_char = "ℹ"
            icon_bg = "#64B5F6"
            border_col = "#BBDEFB"
            bg_col = "#E3F2FD"
            text_col = "#0D47A1"

        self.setStyleSheet(f"""
            ToastWidget {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 10px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # Icon Circle
        icon_frame = QFrame()
        icon_frame.setFixedSize(24, 24)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {icon_bg};
                border-radius: 12px;
            }}
        """)
        icon_layout = QHBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        lbl_icon = QLabel(icon_char)
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_icon.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: bold;")
        icon_layout.addWidget(lbl_icon)

        # Message Text
        msg_lbl = QLabel(self.message)
        msg_lbl.setStyleSheet(f"color: {text_col}; font-size: 11px; font-weight: 700;")
        msg_lbl.setWordWrap(True)

        # Close button "x"
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #A0AEC0;
                font-size: 11px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                color: #4A5568;
            }
        """)
        close_btn.clicked.connect(self.hide_toast)

        layout.addWidget(icon_frame)
        layout.addWidget(msg_lbl)
        layout.addStretch()
        layout.addWidget(close_btn)

    def _setup_animation(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        # Auto-dismiss timer
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_toast)

    def show_toast(self):
        self.show()
        self.raise_()
        self.anim.setDirection(QPropertyAnimation.Forward)
        self.anim.start()
        self.timer.start(3500) # 3.5 seconds

    @Slot()
    def hide_toast(self):
        self.timer.stop()
        self.anim.setDirection(QPropertyAnimation.Backward)
        self.anim.finished.connect(self.deleteLater)
        self.anim.start()
