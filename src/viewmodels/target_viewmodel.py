"""
Target ViewModel.
Manages financial savings targets, progress calculations, target addition/editing,
and deposit (Isi Target) events.
"""
from PySide6.QtCore import Signal, Slot
from src.viewmodels.base_viewmodel import BaseViewModel
from src.core.mock_data import mock_store, TargetPriority
from src.core.utils import format_rupiah, parse_rupiah

class TargetViewModel(BaseViewModel):
    # Signals
    target_summary_updated = Signal(dict)
    targets_updated = Signal(list)
    target_allocations_updated = Signal(list)
    target_operation_completed = Signal(bool, str)
    deposit_completed = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def refresh(self):
        """Refreshes all target cards and summaries."""
        self._load_summary()
        self._load_targets()
        self._load_allocations()

    def _load_summary(self):
        active_count = len(mock_store.targets)
        total_target_amount = sum(t.target_amount for t in mock_store.targets)
        terkumpul = sum(t.collected_amount for t in mock_store.targets)
        progress_pct = int((terkumpul / total_target_amount) * 100) if total_target_amount > 0 else 0

        summary = {
            "total_target_aktif": str(active_count),
            "total_target_keuangan": format_rupiah(total_target_amount or 18_111_000),
            "terkumpul": format_rupiah(terkumpul or 5_100_000),
            "seluruh_progress": f"{min(progress_pct or 20, 100)}%"
        }
        self.target_summary_updated.emit(summary)

    def _load_targets(self):
        result = []
        for t in mock_store.targets:
            pct = int((t.collected_amount / t.target_amount) * 100) if t.target_amount > 0 else 0
            sisa = max(0, t.target_amount - t.collected_amount)
            
            # Badge colors
            if t.priority == TargetPriority.TINGGI:
                badge_bg = "#FFEBEE"
                badge_fg = "#E57373"
            elif t.priority == TargetPriority.SEDANG:
                badge_bg = "#FFF8E1"
                badge_fg = "#FFB74D"
            else:
                badge_bg = "#E8F5E9"
                badge_fg = "#81C784"

            result.append({
                "id": t.id,
                "name": t.name,
                "target_amount": t.target_amount,
                "target_amount_formatted": format_rupiah(t.target_amount),
                "collected_amount": t.collected_amount,
                "collected_amount_formatted": format_rupiah(t.collected_amount),
                "sisa_formatted": format_rupiah(sisa),
                "progress_pct": min(pct, 100),
                "deadline_date": t.deadline_date,
                "start_date": t.start_date,
                "priority": t.priority,
                "badge_bg": badge_bg,
                "badge_fg": badge_fg,
                "notes": t.notes
            })
        self.targets_updated.emit(result)

    def _load_allocations(self):
        allocs = []
        for a in mock_store.target_allocations:
            allocs.append({
                "id": a.id,
                "target_id": a.target_id,
                "target_name": a.target_name,
                "nominal_formatted": format_rupiah(a.amount),
                "date": a.date,
                "notes": a.notes
            })
        self.target_allocations_updated.emit(allocs)

    @Slot(str, str, str, str, str, str)
    def add_target(self, name: str, amount_str: str, deadline: str, start_date: str, priority: str, notes: str):
        """Slot for creating a new financial target."""
        if not name.strip():
            self.target_operation_completed.emit(False, "Nama target tidak boleh kosong!")
            self.notify_toast("Nama target tidak boleh kosong!", "warning")
            return

        amount = parse_rupiah(amount_str)
        if amount <= 0:
            self.target_operation_completed.emit(False, "Nominal target harus lebih dari 0!")
            self.notify_toast("Nominal target harus lebih dari 0!", "warning")
            return

        mock_store.add_target(
            name=name.strip(),
            target_amount=amount,
            deadline_date=deadline or "31 Des 2027",
            start_date=start_date or "01 Jan 2026",
            priority=priority or TargetPriority.SEDANG,
            notes=notes.strip()
        )
        self.notify_data_changed()
        self.notify_toast("Target keuangan berhasil dibuat!", "success")
        self.target_operation_completed.emit(True, "Target keuangan berhasil dibuat!")

    @Slot(str, str, str, str, str, str, str)
    def update_target(self, target_id: str, name: str, amount_str: str, deadline: str, start_date: str, priority: str, notes: str):
        """Slot for updating an existing target."""
        if not name.strip():
            self.target_operation_completed.emit(False, "Nama target tidak boleh kosong!")
            self.notify_toast("Nama target tidak boleh kosong!", "warning")
            return

        amount = parse_rupiah(amount_str)
        if amount <= 0:
            self.target_operation_completed.emit(False, "Nominal target harus lebih dari 0!")
            self.notify_toast("Nominal target harus lebih dari 0!", "warning")
            return

        success = mock_store.update_target(
            target_id=target_id,
            name=name.strip(),
            target_amount=amount,
            deadline_date=deadline,
            start_date=start_date,
            priority=priority,
            notes=notes.strip()
        )
        if success:
            self.notify_data_changed()
            self.notify_toast("Target keuangan berhasil diperbarui!", "success")
            self.target_operation_completed.emit(True, "Target keuangan berhasil diperbarui!")
        else:
            self.notify_toast("Gagal memperbarui target.", "error")
            self.target_operation_completed.emit(False, "Gagal memperbarui target.")

    @Slot(str)
    def delete_target(self, target_id: str):
        """Slot for deleting a target."""
        success = mock_store.delete_target(target_id)
        if success:
            self.notify_data_changed()
            self.notify_toast("Target berhasil dihapus!", "info")
            self.target_operation_completed.emit(True, "Target berhasil dihapus!")
        else:
            self.notify_toast("Gagal menghapus target.", "error")
            self.target_operation_completed.emit(False, "Gagal menghapus target.")

    @Slot(str, str, str)
    def deposit_funds(self, target_id: str, amount_str: str, notes: str):
        """Slot to handle 'Isi Target' event."""
        amount = parse_rupiah(amount_str)
        if amount <= 0:
            self.deposit_completed.emit(False, "Nominal tabungan tidak valid!")
            self.notify_toast("Nominal tabungan tidak valid!", "warning")
            return

        curr_balance = mock_store.get_current_balance()
        if amount > curr_balance:
            self.deposit_completed.emit(False, "Saldo tidak mencukupi untuk alokasi ini!")
            self.notify_toast("Saldo tidak mencukupi!", "error")
            return

        success = mock_store.deposit_to_target(target_id, amount, notes)
        if success:
            self.notify_data_changed()
            self.notify_toast("Dana berhasil ditambahkan ke target!", "success")
            self.deposit_completed.emit(True, "Dana berhasil ditambahkan ke target!")
        else:
            self.deposit_completed.emit(False, "Target tidak ditemukan.")
            self.notify_toast("Gagal menambahkan dana.", "error")
