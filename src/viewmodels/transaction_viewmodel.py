"""
Transaction Input ViewModel.
Manages input events, dynamic category population, live currency formatting,
character counter updates, validation, and submission signals.
"""
from PySide6.QtCore import Signal, Slot
from src.viewmodels.base_viewmodel import BaseViewModel
from src.core.mock_data import mock_store, TransactionType
from src.core.utils import parse_rupiah, format_rupiah, format_short_date

class TransactionViewModel(BaseViewModel):
    # Signals for View Binding
    categories_loaded = Signal(list)
    formatted_amount_changed = Signal(str)
    character_count_changed = Signal(int, int)  # (current_count, max_count)
    validation_status_changed = Signal(bool, str)
    transaction_saved = Signal(bool, str)
    transaction_cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_type = TransactionType.PEMASUKAN
        self._current_amount = 0
        self._max_notes_len = 100

    def refresh(self):
        """Reload categories when view is shown or refreshed."""
        self.load_categories_for_type(self._current_type)

    @Slot(str)
    def load_categories_for_type(self, tx_type: str):
        """Loads categories matching selected transaction type."""
        self._current_type = tx_type
        filtered_cats = [
            cat.name for cat in mock_store.categories
            if cat.type == tx_type
        ]
        self.categories_loaded.emit(filtered_cats)

    @Slot(str)
    def on_amount_text_changed(self, raw_text: str):
        """Processes live amount input and formats it to currency."""
        amount = parse_rupiah(raw_text)
        self._current_amount = amount
        if amount > 0:
            formatted = format_rupiah(amount, with_prefix=True)
        else:
            formatted = "Rp 0"
        self.formatted_amount_changed.emit(formatted)
        self._validate_form()

    @Slot(str)
    def on_notes_text_changed(self, text: str):
        """Tracks character count in notes field."""
        curr_len = len(text)
        self.character_count_changed.emit(curr_len, self._max_notes_len)

    def _validate_form(self) -> bool:
        if self._current_amount <= 0:
            self.validation_status_changed.emit(False, "Nominal harus lebih dari 0")
            return False
        self.validation_status_changed.emit(True, "")
        return True

    @Slot(str, str, str, str, str)
    def save_transaction(self, tx_type: str, raw_amount: str, category: str, tx_date: str, notes: str):
        """Handles submission event of a new transaction."""
        amount = parse_rupiah(raw_amount)
        if amount <= 0:
            self.transaction_saved.emit(False, "Nominal transaksi tidak valid!")
            self.notify_toast("Nominal transaksi tidak valid!", "error")
            return

        if not category:
            self.transaction_saved.emit(False, "Silakan pilih kategori!")
            self.notify_toast("Silakan pilih kategori!", "warning")
            return

        # Add to mock store
        mock_store.add_transaction(
            tx_type=tx_type,
            category=category,
            amount=amount,
            tx_date=tx_date or format_short_date(),
            notes=notes.strip()
        )

        # Notify global bus
        self.notify_data_changed()
        self.notify_toast("Transaksi berhasil disimpan!", "success")
        self.transaction_saved.emit(True, "Transaksi berhasil disimpan!")

    @Slot()
    def cancel_transaction(self):
        """Handles cancel event."""
        self.notify_toast("Transaksi dibatalkan", "error")
        self.transaction_cancelled.emit()
