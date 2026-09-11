"""
Global Event Bus for Event-Driven Architecture in PySide6.
Provides decoupled inter-component and cross-ViewModel communication using Qt Signals.
"""
from PySide6.QtCore import QObject, Signal

class EventBus(QObject):
    """
    Central event broadcaster using PySide6 Signal & Slot mechanism.
    Allows ViewModels and Views to communicate without tight coupling.
    """
    data_changed = Signal()                          # Fired when any financial state changes
    toast_requested = Signal(str, str)               # (message: str, type: str -> "success"|"info"|"warning"|"error")
    navigation_requested = Signal(int)               # (page_index: int)
    open_isi_target_requested = Signal(str)          # (target_id: str)


# Global singleton instance
event_bus = EventBus()
