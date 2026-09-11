"""
Base ViewModel class for Keuangan Mandiri.
Inherits QObject to support PySide6 Signal & Slot event-driven programming.
"""
from PySide6.QtCore import QObject, Signal, Slot
from src.core.event_bus import event_bus

class BaseViewModel(QObject):
    """
    Abstract/Base ViewModel providing shared event dispatching,
    error notification, and lifecycle signals.
    """
    error_occurred = Signal(str)
    busy_state_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Connect to global event bus data changes
        event_bus.data_changed.connect(self._on_global_data_changed)

    @Slot()
    def _on_global_data_changed(self):
        """Hook called when global data mutates. Override in subclasses if needed."""
        self.refresh()

    def refresh(self):
        """Override to perform data refresh when triggered by events."""
        pass

    def notify_toast(self, message: str, toast_type: str = "info"):
        """Emit global toast request signal."""
        event_bus.toast_requested.emit(message, toast_type)

    def notify_data_changed(self):
        """Broadcast global data changed signal."""
        event_bus.data_changed.emit()
