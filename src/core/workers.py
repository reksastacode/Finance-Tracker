"""
Concurrency & Multi-Threading Engine for Keuangan Mandiri.
Implements the Background Worker Pattern using PySide6 QThread & QRunnable
to offload heavy data processing, bulk generation, and file exporting
away from the Main GUI Thread, completely eliminating UI freeze / 'Not Responding'.
"""
import os
import csv
import math
import time
from datetime import datetime
from PySide6.QtCore import QThread, QObject, Signal, Slot, QRunnable, QThreadPool

from src.core.constants import TransactionType
from src.core.utils import format_rupiah


class WorkerSignals(QObject):
    """Signals for generic runnable workers."""
    started = Signal()
    progress = Signal(int, str)  # (percentage 0-100, status_message)
    finished = Signal(object)    # result payload
    error = Signal(str)          # error message


def build_history_payload(
    transactions_snapshot: list,
    filter_type: str,
    filter_category: str,
    start_date: str,
    end_date: str,
    page_size: int = 50,
    current_page: int = 1,
    base_balance: int = 0,
    search_text: str = "",
    attachments_snapshot: dict | None = None,
    progress_callback=None,
    cancelled=None,
    simulate_workload: bool = False,
) -> dict:
    """
    Single source of truth for history filtering, running balances, summaries,
    and pagination.  Both the QThread worker and the synchronous test path call
    this function so their numbers can never diverge.
    """
    transactions = list(transactions_snapshot)
    attachments = attachments_snapshot or {}
    total_raw = len(transactions)
    page_size = max(10, int(page_size))
    current_page = max(1, int(current_page))
    search_lower = (search_text or "").strip().lower()

    if progress_callback:
        progress_callback(10, f"Memuat {total_raw:,} data transaksi di background thread...")
    if simulate_workload and total_raw < 500:
        time.sleep(0.06)
    if cancelled and cancelled():
        return {}

    # 1. Running balance chronologically (oldest to newest)
    running_balance = int(base_balance or 0)
    tx_items_with_balance = []
    step_interval = max(1, total_raw // 5)
    for idx, tx in enumerate(reversed(transactions)):
        if cancelled and cancelled():
            return {}
        if tx.type == TransactionType.PEMASUKAN:
            running_balance += tx.amount
            nominal_str = format_rupiah(tx.amount)
            color = "#7FAE8A"
        elif tx.type == TransactionType.PENGELUARAN:
            running_balance -= tx.amount
            nominal_str = f"-{format_rupiah(tx.amount)}"
            color = "#C98787"
        else:
            running_balance -= tx.amount
            nominal_str = format_rupiah(tx.amount)
            color = "#A99ABF"

        attachment = attachments.get(tx.id)
        attachment_payload = None
        if attachment is not None:
            attachment_payload = {
                "id": attachment.id,
                "stored_name": attachment.stored_name,
                "original_name": attachment.original_name,
                "mime_type": attachment.mime_type,
                "size_bytes": attachment.size_bytes,
            }

        tx_items_with_balance.append({
            "id": tx.id,
            "date": tx.date,
            "type": tx.type,
            "category": tx.category,
            "notes": tx.notes,
            "nominal": tx.amount,
            "nominal_formatted": nominal_str,
            "saldo_setelah": format_rupiah(running_balance),
            "color": color,
            "attachment": attachment_payload,
            "created_at": getattr(tx, "created_at", "") or "",
            "updated_at": getattr(tx, "updated_at", "") or "",
        })

        if progress_callback and (idx + 1) % step_interval == 0:
            pct = 15 + int((idx / max(1, total_raw)) * 25)
            progress_callback(pct, f"Menghitung saldo berjalan ({idx + 1}/{total_raw})...")

    tx_items_with_balance.reverse()

    if progress_callback:
        progress_callback(45, "Menerapkan kriteria filter...")
    if simulate_workload and total_raw < 500:
        time.sleep(0.06)

    # 2. Date range + type/category/text filtering
    start_dt = None
    end_dt = None
    try:
        start_dt = datetime.strptime(start_date, "%d/%m/%Y").date() if start_date else None
    except ValueError:
        start_dt = None
    try:
        end_dt = datetime.strptime(end_date, "%d/%m/%Y").date() if end_date else None
    except ValueError:
        end_dt = None

    filtered_items = []
    for item in tx_items_with_balance:
        if cancelled and cancelled():
            return {}
        if filter_type != "Semua" and item["type"] != filter_type:
            continue
        if filter_category != "Semua" and item["category"] != filter_category:
            continue
        if search_lower:
            haystack = f"{item['notes']} {item['category']}".lower()
            if search_lower not in haystack:
                continue
        if start_dt or end_dt:
            try:
                tx_dt = datetime.strptime(item["date"], "%d/%m/%Y").date()
            except ValueError:
                continue
            if start_dt and tx_dt < start_dt:
                continue
            if end_dt and tx_dt > end_dt:
                continue
        filtered_items.append(item)

    if progress_callback:
        progress_callback(70, "Mengagregasi metrik ringkasan...")

    # 3. Summary metrics (accurate even for an empty result set)
    total_pemasukan = sum(item["nominal"] for item in filtered_items if item["type"] == TransactionType.PEMASUKAN)
    total_pengeluaran = sum(item["nominal"] for item in filtered_items if item["type"] == TransactionType.PENGELUARAN)
    saldo_bersih = total_pemasukan - total_pengeluaran

    summary = {
        "total_pemasukan": format_rupiah(total_pemasukan),
        "total_pengeluaran": format_rupiah(total_pengeluaran),
        "saldo_bersih": format_rupiah(saldo_bersih),
        "jumlah_transaksi": str(len(filtered_items)),
    }

    # 4. Virtual window pagination
    total_items = len(filtered_items)
    total_pages = max(1, math.ceil(total_items / page_size))
    target_page = max(1, min(current_page, total_pages))
    start_idx = (target_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_items)
    page_items = filtered_items[start_idx:end_idx]

    pagination_info = {
        "current_page": target_page,
        "total_pages": total_pages,
        "total_records": total_items,
        "start_index": start_idx + 1 if total_items > 0 else 0,
        "end_index": end_idx,
        "has_prev": target_page > 1,
        "has_next": target_page < total_pages,
    }

    if progress_callback:
        progress_callback(100, "Pemrosesan selesai.")

    return {
        "filtered_items": filtered_items,
        "page_items": page_items,
        "summary": summary,
        "pagination_info": pagination_info,
        "total_count": total_items,
    }


class GenericWorker(QRunnable):
    """
    Reusable worker runnable to execute any callable function in a QThreadPool background thread.
    """
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        self.signals.started.emit()
        try:
            # Inject progress callback if requested
            if "progress_callback" in self.kwargs:
                self.kwargs["progress_callback"] = self.signals.progress.emit
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


class FilterTransactionsWorker(QThread):
    """
    Dedicated Background Worker Thread for heavy transaction filtering,
    chronological running balance calculations, summary aggregations,
    and virtual window pagination.
    
    CRITICAL ARCHITECTURAL RULE:
    This worker operates strictly on plain Python data structures.
    It never touches or allocates QWidget or QPixmap objects, ensuring
    100% thread safety and preserving icon symmetry on the GUI Main Thread.
    """
    progress = Signal(int, str)
    result_ready = Signal(dict)
    error = Signal(str)

    def __init__(
        self,
        transactions_snapshot: list,
        filter_type: str,
        filter_category: str,
        start_date: str,
        end_date: str,
        page_size: int = 50,
        current_page: int = 1,
        simulate_workload: bool = False,
        base_balance: int = 0,
        search_text: str = "",
        attachments_snapshot: dict | None = None,
        parent=None
    ):
        super().__init__(parent)
        self.transactions = list(transactions_snapshot)
        self.filter_type = filter_type
        self.filter_category = filter_category
        self.start_date = start_date
        self.end_date = end_date
        self.page_size = max(10, page_size)
        self.current_page = current_page
        self.simulate_workload = simulate_workload
        self.base_balance = base_balance
        self.search_text = search_text
        self.attachments = dict(attachments_snapshot or {})
        self._is_cancelled = False

    def cancel(self):
        """Signals the worker to abort early if a new filter request arrives."""
        self._is_cancelled = True

    def run(self):
        try:
            payload = build_history_payload(
                transactions_snapshot=self.transactions,
                filter_type=self.filter_type,
                filter_category=self.filter_category,
                start_date=self.start_date,
                end_date=self.end_date,
                page_size=self.page_size,
                current_page=self.current_page,
                base_balance=self.base_balance,
                search_text=self.search_text,
                attachments_snapshot=self.attachments,
                progress_callback=self.progress.emit,
                cancelled=lambda: self._is_cancelled,
                simulate_workload=self.simulate_workload,
            )
            if payload:
                self.result_ready.emit(payload)
        except Exception as e:
            self.error.emit(str(e))


class BulkDataGeneratorWorker(QThread):
    """
    Background Worker Thread that generates thousands of mock transactions
    without blocking the Main Thread's event loop.
    Demonstrates active UI responsiveness during heavy workload injection.
    """
    progress = Signal(int, str)
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, count: int = 5000, parent=None):
        super().__init__(parent)
        self.count = count

    def run(self):
        try:
            from src.core.mock_data import TransactionModel, TransactionType
            
            self.progress.emit(5, f"Memulai pembuatan {self.count:,} data transaksi...")
            generated = []
            chunk_size = max(50, self.count // 20)

            for i in range(self.count):
                t_type = TransactionType.PEMASUKAN if i % 2 == 0 else TransactionType.PENGELUARAN
                cat = "Gaji" if t_type == TransactionType.PEMASUKAN else ("Makan" if i % 3 == 0 else "Transport")
                amount = 25000 + ((i % 100) * 1500)
                
                day = (i % 28) + 1
                month = ((i // 28) % 12) + 1
                date_str = f"{day:02d}/{month:02d}/2026"

                generated.append(TransactionModel(
                    id=f"bulk_tx_{i+1}",
                    type=t_type,
                    category=cat,
                    amount=amount,
                    date=date_str,
                    notes=f"Transaksi simulasi #{i+1} via Background Worker"
                ))

                if (i + 1) % chunk_size == 0 or (i + 1) == self.count:
                    pct = int(((i + 1) / self.count) * 95)
                    self.progress.emit(pct, f"Menghasilkan data transaksi: {i + 1:,} / {self.count:,}...")
                    # Brief sleep to allow visible GUI updates and event loop breathing
                    time.sleep(0.02)

            self.progress.emit(100, f"Selesai menghasilkan {self.count:,} data!")
            self.finished.emit(generated)

        except Exception as e:
            self.error.emit(str(e))


class ExportReportWorker(QThread):
    """
    Background Worker Thread that exports transaction records into a CSV file.
    Prevents file I/O lockup on the Main Thread.
    """
    progress = Signal(int, str)
    finished = Signal(str)  # output file path
    error = Signal(str)

    def __init__(self, file_path: str, items: list, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.items = items

    def run(self):
        try:
            total = len(self.items)
            self.progress.emit(5, f"Mempersiapkan ekspor {total:,} baris...")

            with open(self.file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Header
                writer.writerow(["ID", "Tanggal", "Jenis", "Kategori", "Keterangan", "Nominal", "Saldo Setelah"])

                step = max(1, total // 20)
                for idx, item in enumerate(self.items):
                    writer.writerow([
                        item.get("id", ""),
                        item.get("date", ""),
                        item.get("type", ""),
                        item.get("category", ""),
                        item.get("notes", ""),
                        item.get("nominal_formatted", ""),
                        item.get("saldo_setelah", "")
                    ])

                    if (idx + 1) % step == 0 or (idx + 1) == total:
                        pct = int(((idx + 1) / total) * 95)
                        self.progress.emit(pct, f"Menulis baris {idx + 1:,} dari {total:,} ke file...")
                        time.sleep(0.01)

            self.progress.emit(100, "Ekspor CSV berhasil!")
            self.finished.emit(self.file_path)

        except Exception as e:
            self.error.emit(str(e))
