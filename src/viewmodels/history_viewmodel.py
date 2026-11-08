"""
History ViewModel.
Manages transaction history table rendering, multi-criteria filtering,
running balance calculations, pagination / virtual windowing, and deletion events.

ENHANCED WITH CONCURRENCY & MULTI-THREADING:
Delegates heavy filtering, chronological running balance calculations,
bulk data stress testing, and CSV exports to background QThread workers,
keeping the Qt Main GUI Thread 100% fluid and responsive.
"""
import math
import os

from PySide6.QtCore import Signal, Slot

from src.viewmodels.base_viewmodel import BaseViewModel
from src.core.mock_data import mock_store, TransactionType
from src.core.workers import (
    FilterTransactionsWorker,
    BulkDataGeneratorWorker,
    ExportReportWorker,
    build_history_payload,
)


class HistoryViewModel(BaseViewModel):
    # Signals to View
    history_summary_updated = Signal(dict)
    transactions_updated = Signal(list)
    pagination_updated = Signal(dict)
    categories_for_filter_updated = Signal(list)
    filter_applied_signal = Signal(int)  # count of matching records
    worker_progress_updated = Signal(int, str)  # (percentage 0-100, status_message)
    export_completed = Signal(str)  # output file path
    bulk_generation_completed = Signal(int)  # total generated records

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_type = "Semua"
        self._filter_category = "Semua"
        self._search_text = ""
        self._start_date = ""
        self._end_date = ""
        self._current_page = 1
        self._page_size = 50
        self._filtered_cache = []

        try:
            from src.storage.config import get_config

            self._page_size = max(10, int(get_config().get("ui.page_size", 50)))
        except Exception:
            self._page_size = 50

        # Background Worker reference
        self._filter_worker: FilterTransactionsWorker | None = None
        self._generator_worker: BulkDataGeneratorWorker | None = None
        self._export_worker: ExportReportWorker | None = None

    def refresh(self, sync: bool = False):
        """Refreshes filter options and history table with current filters."""
        self._update_filter_categories()
        is_test_env = os.environ.get("QT_QPA_PLATFORM") == "offscreen"
        if sync or is_test_env:
            self._filter_and_emit_data_sync()
        else:
            self._filter_and_emit_data_async()

    def _update_filter_categories(self):
        cat_names = ["Semua"] + sorted(list({c.name for c in mock_store.categories}))
        self.categories_for_filter_updated.emit(cat_names)

    @Slot(str, str, str, str)
    def apply_filter(self, tx_type: str, category: str, start_date: str, end_date: str, sync: bool = False):
        """Applies filter criteria from View inputs and resets to page 1."""
        self.apply_filter_full(tx_type, category, start_date, end_date, self._search_text, sync=sync)

    def apply_filter_full(
        self,
        tx_type: str,
        category: str,
        start_date: str,
        end_date: str,
        search_text: str = "",
        sync: bool = False,
    ):
        """Applies all filters, including the documented free-text search."""
        self._filter_type = tx_type
        self._filter_category = category
        self._search_text = (search_text or "").strip()
        self._start_date = start_date
        self._end_date = end_date
        self._current_page = 1

        is_test_env = os.environ.get("QT_QPA_PLATFORM") == "offscreen"
        if sync or is_test_env:
            self._filter_and_emit_data_sync()
        else:
            self._filter_and_emit_data_async()

    def set_search_text(self, text: str):
        """Updates the active text query without immediately running a worker."""
        self._search_text = (text or "").strip()

    @Slot(int)
    def set_page(self, page_number: int):
        """Changes the current active page."""
        total_pages = max(1, math.ceil(len(self._filtered_cache) / self._page_size))
        target_page = max(1, min(page_number, total_pages))
        if target_page != self._current_page or not self._filtered_cache:
            self._current_page = target_page
            self._emit_page_data()

    @Slot()
    def next_page(self):
        self.set_page(self._current_page + 1)

    @Slot()
    def prev_page(self):
        self.set_page(self._current_page - 1)

    def set_page_size(self, size: int):
        self._page_size = max(10, int(size))
        self._current_page = 1
        try:
            from src.storage.config import get_config

            get_config().set("ui.page_size", self._page_size)
        except Exception:
            pass
        self._emit_page_data()

    # =========================================================================
    # MULTI-THREADING BACKGROUND WORKER EXECUTION
    # =========================================================================

    def _filter_and_emit_data_async(self):
        """
        Launches FilterTransactionsWorker in a dedicated QThread.
        Ensures the UI thread remains completely responsive.
        """
        # Cancel previous running worker if active
        if self._filter_worker and self._filter_worker.isRunning():
            self._filter_worker.cancel()
            self._filter_worker.wait(100)

        self.busy_state_changed.emit(True)
        self.worker_progress_updated.emit(5, "Memulai worker latar belakang...")

        self._filter_worker = FilterTransactionsWorker(
            transactions_snapshot=mock_store.transactions,
            filter_type=self._filter_type,
            filter_category=self._filter_category,
            start_date=self._start_date,
            end_date=self._end_date,
            page_size=self._page_size,
            current_page=self._current_page,
            simulate_workload=True,
            base_balance=mock_store.base_balance,
            search_text=self._search_text,
            attachments_snapshot=mock_store.attachments,
            parent=self,
        )

        self._filter_worker.progress.connect(self._on_filter_worker_progress)
        self._filter_worker.result_ready.connect(self._on_filter_worker_result)
        self._filter_worker.error.connect(self._on_filter_worker_error)
        self._filter_worker.finished.connect(self._on_filter_worker_finished)
        self._filter_worker.start()

    @Slot(int, str)
    def _on_filter_worker_progress(self, pct: int, msg: str):
        self.worker_progress_updated.emit(pct, msg)

    @Slot(dict)
    def _on_filter_worker_result(self, payload: dict):
        self._filtered_cache = payload["filtered_items"]
        self.history_summary_updated.emit(payload["summary"])
        self.filter_applied_signal.emit(payload["total_count"])
        self.pagination_updated.emit(payload["pagination_info"])
        self.transactions_updated.emit(payload["page_items"])

    @Slot(str)
    def _on_filter_worker_error(self, err_msg: str):
        self.error_occurred.emit(err_msg)
        self.notify_toast(f"Error pemrosesan: {err_msg}", "error")

    @Slot()
    def _on_filter_worker_finished(self):
        self.busy_state_changed.emit(False)
        self.worker_progress_updated.emit(100, "Siap")

    # =========================================================================
    # SYNCHRONOUS FALLBACK (FOR AUTOMATED TESTS)
    # =========================================================================

    def _filter_and_emit_data_sync(self):
        """Synchronous path using the exact same calculation as the worker."""
        payload = build_history_payload(
            transactions_snapshot=mock_store.transactions,
            filter_type=self._filter_type,
            filter_category=self._filter_category,
            start_date=self._start_date,
            end_date=self._end_date,
            page_size=self._page_size,
            current_page=self._current_page,
            base_balance=mock_store.base_balance,
            search_text=self._search_text,
            attachments_snapshot=mock_store.attachments,
            simulate_workload=False,
        )
        self._filtered_cache = payload["filtered_items"]
        self.history_summary_updated.emit(payload["summary"])
        self.filter_applied_signal.emit(payload["total_count"])
        self.pagination_updated.emit(payload["pagination_info"])
        self.transactions_updated.emit(payload["page_items"])

    def _emit_page_data(self):
        """Emits only the window/chunk of records for the active page."""
        total_items = len(self._filtered_cache)
        total_pages = max(1, math.ceil(total_items / self._page_size))

        if self._current_page > total_pages:
            self._current_page = total_pages

        start_idx = (self._current_page - 1) * self._page_size
        end_idx = min(start_idx + self._page_size, total_items)
        page_items = self._filtered_cache[start_idx:end_idx]

        pagination_info = {
            "current_page": self._current_page,
            "total_pages": total_pages,
            "total_records": total_items,
            "start_index": start_idx + 1 if total_items > 0 else 0,
            "end_index": end_idx,
            "has_prev": self._current_page > 1,
            "has_next": self._current_page < total_pages,
        }

        self.pagination_updated.emit(pagination_info)
        self.transactions_updated.emit(page_items)

    # =========================================================================
    # ASYNC BULK DATA STRESS TESTING & EXPORTING
    # =========================================================================

    def generate_bulk_data_async(self, count: int = 5000):
        """Generates thousands of mock transactions in a background thread."""
        if self._generator_worker and self._generator_worker.isRunning():
            return

        self.busy_state_changed.emit(True)
        self._generator_worker = BulkDataGeneratorWorker(count=count, parent=self)
        self._generator_worker.progress.connect(self._on_filter_worker_progress)
        self._generator_worker.error.connect(self._on_filter_worker_error)

        def on_finished(generated_txs):
            mock_store.transactions = generated_txs
            self.busy_state_changed.emit(False)
            self.bulk_generation_completed.emit(len(generated_txs))
            self.notify_toast(f"Berhasil menginjeksi {len(generated_txs):,} transaksi!", "success")
            self.notify_data_changed()
            self._filter_and_emit_data_async()

        self._generator_worker.finished.connect(on_finished)
        self._generator_worker.start()

    def export_transactions_async(self, file_path: str):
        """Exports filtered transactions to CSV in a background thread."""
        if not self._filtered_cache:
            self.notify_toast("Tidak ada data untuk diekspor.", "warning")
            return

        if self._export_worker and self._export_worker.isRunning():
            return

        try:
            parent = os.path.dirname(os.path.abspath(file_path))
            if parent:
                os.makedirs(parent, exist_ok=True)
        except OSError as exc:
            self.notify_toast(f"Folder ekspor tidak dapat dibuat: {exc}", "error")
            return

        self.busy_state_changed.emit(True)
        self._export_worker = ExportReportWorker(file_path=file_path, items=self._filtered_cache, parent=self)
        self._export_worker.progress.connect(self._on_filter_worker_progress)
        self._export_worker.error.connect(self._on_filter_worker_error)

        def on_finished(path):
            self.busy_state_changed.emit(False)
            self.export_completed.emit(path)
            self.notify_toast(f"File CSV berhasil diekspor: {os.path.basename(path)}", "success")

        self._export_worker.finished.connect(on_finished)
        self._export_worker.start()

    @Slot(str)
    def delete_transaction(self, tx_id: str):
        """Handles deleting a transaction and its attachment."""
        success = mock_store.delete_transaction(tx_id)
        if success:
            self.notify_data_changed()
            self.notify_toast("Transaksi berhasil dihapus!", "info")
            self.refresh()
        else:
            self.notify_toast("Gagal menghapus transaksi.", "error")

    def get_attachment(self, tx_id: str):
        return mock_store.get_attachment_for_transaction(tx_id)

    def shutdown(self):
        """Stops background workers before the application window closes."""
        for worker in (self._filter_worker, self._generator_worker, self._export_worker):
            if worker is None:
                continue
            try:
                if worker.isRunning():
                    if hasattr(worker, "cancel"):
                        worker.cancel()
                    worker.wait(2000)
            except RuntimeError:
                # The underlying C++ object may already be deleted.
                pass
