"""A QLabel that keeps its natural width but can shrink with an ellipsis."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QLabel, QSizePolicy


class ElidedLabel(QLabel):
    """
    Labels normally force layouts to be as wide as their longest text.

    This subclass reports the full text as its size hint (so it looks right when
    there is room) but a zero-width minimum size hint (so the window can shrink).
    When the available width is smaller, the displayed text is elided and the
    full text remains available as a tooltip.
    """

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._full_text = ""
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setText(text or "")

    # ------------------------------------------------------------------
    # Size hints
    # ------------------------------------------------------------------
    def minimumSizeHint(self) -> QSize:
        height = super().minimumSizeHint().height()
        return QSize(0, height)

    def sizeHint(self) -> QSize:
        base = super().sizeHint()
        text_width = self.fontMetrics().horizontalAdvance(self._full_text)
        return QSize(max(base.width(), text_width), base.height())

    # ------------------------------------------------------------------
    # Text handling
    # ------------------------------------------------------------------
    def setText(self, text: str):
        self._full_text = text or ""
        self.setToolTip(self._full_text)
        self._update_elided_text()

    def full_text(self) -> str:
        return self._full_text

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided_text()

    def _update_elided_text(self):
        width = self.width()
        if width <= 0:
            super().setText(self._full_text)
            return
        super().setText(
            self.fontMetrics().elidedText(self._full_text, Qt.ElideRight, width)
        )
