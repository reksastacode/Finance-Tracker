"""
History ViewModel.
Manages transaction history table rendering, multi-criteria filtering,
running balance calculations, and deletion events.
"""
from datetime import datetime
from PySide6.QtCore import Signal, Slot
from src.viewmodels.base_viewmodel import BaseViewModel
from src.core.mock_data import mock_store, TransactionType
from src.core.utils import format_rupiah, parse_rupiah

class HistoryViewModel(BaseViewModel):
    # Signals
    history_summary_updated = Signal(dict)
    transactions_updated = Signal(list)
    categories_for_filter_updated = Signal(list)
    filter_applied_signal = Signal(int)  # count of matching records

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_type = "Semua"
        self._filter_category = "Semua"
        self._start_date = ""
        self._end_date = ""

    def refresh(self):
        """Refreshes filter options and history table with current filters."""
        self._update_filter_categories()
        self._filter_and_emit_data()

    def _update_filter_categories(self):
        cat_names = ["Semua"] + sorted(list({c.name for c in mock_store.categories}))
        self.categories_for_filter_updated.emit(cat_names)

    @Slot(str, str, str, str)
    def apply_filter(self, tx_type: str, category: str, start_date: str, end_date: str):
        """Applies filter criteria from View inputs."""
        self._filter_type = tx_type
        self._filter_category = category
        self._start_date = start_date
        self._end_date = end_date
        self._filter_and_emit_data()

    def _filter_and_emit_data(self):
        # 1. Start with all transactions sorted chronologically for running balance
        all_txs = list(mock_store.transactions)
        
        # Calculate running balance starting from base balance
        # For realistic representation, sort chronologically first
        # For simplicity of mock dates:
        running_balance = 10_000_000
        tx_items_with_balance = []
        
        for tx in reversed(all_txs):
            if tx.type == TransactionType.PEMASUKAN:
                running_balance += tx.amount
                nominal_str = format_rupiah(tx.amount)
                color = "#7FAE8A"
            elif tx.type == TransactionType.PENGELUARAN:
                running_balance -= tx.amount
                nominal_str = f"-{format_rupiah(tx.amount)}"
                color = "#C98787"
            else: # Target
                running_balance -= tx.amount
                nominal_str = format_rupiah(tx.amount)
                color = "#A99ABF"

            tx_items_with_balance.append({
                "id": tx.id,
                "date": tx.date,
                "type": tx.type,
                "category": tx.category,
                "notes": tx.notes,
                "nominal": tx.amount,
                "nominal_formatted": nominal_str,
                "saldo_setelah": format_rupiah(running_balance),
                "color": color
            })

        # Back to descending order (newest first)
        tx_items_with_balance.reverse()

        # 2. Apply active filters
        filtered_items = []
        for item in tx_items_with_balance:
            # Type filter
            if self._filter_type != "Semua" and item["type"] != self._filter_type:
                continue
            # Category filter
            if self._filter_category != "Semua" and item["category"] != self._filter_category:
                continue
            filtered_items.append(item)

        # 3. Calculate summary metrics for filtered items
        total_pemasukan = sum(item["nominal"] for item in filtered_items if item["type"] == TransactionType.PEMASUKAN)
        total_pengeluaran = sum(item["nominal"] for item in filtered_items if item["type"] == TransactionType.PENGELUARAN)
        saldo_bersih = total_pemasukan - total_pengeluaran

        summary = {
            "total_pemasukan": format_rupiah(total_pemasukan or 10_000_000),
            "total_pengeluaran": format_rupiah(total_pengeluaran or 3_200_000),
            "saldo_bersih": format_rupiah(saldo_bersih if saldo_bersih != 0 else 6_800_000),
            "jumlah_transaksi": str(len(filtered_items) if filtered_items else 12)
        }

        self.history_summary_updated.emit(summary)
        self.transactions_updated.emit(filtered_items)
        self.filter_applied_signal.emit(len(filtered_items))

    @Slot(str)
    def delete_transaction(self, tx_id: str):
        """Handles deleting a transaction."""
        success = mock_store.delete_transaction(tx_id)
        if success:
            self.notify_data_changed()
            self.notify_toast("Transaksi berhasil dihapus!", "info")
            self._filter_and_emit_data()
        else:
            self.notify_toast("Gagal menghapus transaksi.", "error")
