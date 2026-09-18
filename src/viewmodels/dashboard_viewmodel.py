"""
Dashboard ViewModel.
Manages summary calculations, chart series data, calendar aggregates,
and recent activity feeds through PySide6 Signals and Slots.
"""
from PySide6.QtCore import Signal, Slot
from src.viewmodels.base_viewmodel import BaseViewModel
from src.core.mock_data import mock_store, TransactionType
from src.core.utils import format_rupiah

class DashboardViewModel(BaseViewModel):
    # Signals to notify View
    summary_updated = Signal(dict)
    chart_data_updated = Signal(dict)
    calendar_data_updated = Signal(dict)
    recent_transactions_updated = Signal(list)
    targets_preview_updated = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_chart_period = "Minggu ini"
        self._calendar_year = 2026
        self._calendar_month = 9  # September 2026 per mock

    def refresh(self):
        """Refreshes all dashboard metrics and emits change signals."""
        self._update_summary()
        self._update_chart()
        self._update_calendar()
        self._update_recent_transactions()
        self._update_targets_preview()

    def _update_summary(self):
        saldo = mock_store.get_current_balance()
        pemasukan = mock_store.get_total_pemasukan()
        pengeluaran = mock_store.get_total_pengeluaran()
        total_target = sum(t.collected_amount for t in mock_store.targets[:3]) or 5_000_000

        data = {
            "saldo_saat_ini": format_rupiah(saldo),
            "total_pemasukan": format_rupiah(pemasukan),
            "total_pengeluaran": format_rupiah(pengeluaran),
            "total_target": format_rupiah(total_target),
            "raw_saldo": saldo,
            "raw_pemasukan": pemasukan,
            "raw_pengeluaran": pengeluaran,
            "raw_target": total_target,
        }
        self.summary_updated.emit(data)

    def _update_chart(self):
        """Generates chart points based on selected period."""
        if self._current_chart_period == "Minggu ini":
            # 7 days from the start of the month (1 Sep - 7 Sep)
            labels = ["1 Sep", "2 Sep", "3 Sep", "4 Sep", "5 Sep", "6 Sep", "7 Sep"]
            pemasukan_series = [1.0, 0.2, 0.8, 1.5, 0.4, 0.9, 1.8]     # in millions
            pengeluaran_series = [0.3, 0.7, 0.2, 0.8, 0.5, 1.2, 0.6]
            target_series = [0.5, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8]
            max_val = 3.5
        elif self._current_chart_period == "Bulan ini":
            # 30 days of the month (1 to 30 September)
            labels = [f"{i} Sep" for i in range(1, 31)]
            # Realistic monthly trend data spanning 30 days
            pemasukan_series = [
                1.0, 0.2, 0.5, 1.2, 0.3, 0.0, 1.5, 0.8, 0.4, 2.0,
                0.5, 0.2, 0.8, 1.0, 3.5, 0.6, 0.2, 0.4, 1.2, 0.8,
                1.5, 0.3, 0.6, 2.2, 0.7, 1.0, 0.4, 1.8, 0.5, 2.5
            ]
            pengeluaran_series = [
                0.4, 0.6, 0.3, 0.8, 0.2, 0.5, 0.9, 0.4, 0.7, 1.5,
                0.3, 0.8, 0.5, 0.6, 1.8, 0.4, 0.7, 0.3, 0.9, 1.2,
                0.6, 0.4, 0.8, 1.4, 0.5, 0.8, 0.3, 1.1, 0.7, 1.6
            ]
            target_series = [
                round(0.2 + (i * 0.16), 2) for i in range(30)
            ]
            max_val = 6.0
        else: # Tahun ini
            labels = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"]
            pemasukan_series = [5.0, 6.2, 7.0, 6.5, 8.0, 9.0, 8.5, 10.0, 11.5, 10.0, 12.0, 14.0]
            pengeluaran_series = [3.0, 3.8, 4.5, 4.0, 5.2, 6.0, 5.5, 6.8, 7.0, 6.5, 7.8, 8.5]
            target_series = [1.5, 2.8, 4.0, 5.5, 7.0, 8.5, 9.8, 11.2, 12.5, 13.8, 15.0, 16.5]
            max_val = 18.0

        payload = {
            "period": self._current_chart_period,
            "labels": labels,
            "pemasukan": pemasukan_series,
            "pengeluaran": pengeluaran_series,
            "target": target_series,
            "max_val": max_val
        }
        self.chart_data_updated.emit(payload)

    def _update_calendar(self):
        """Calendar daily aggregate tags."""
        day_events = {
            1: [{"type": "Pengeluaran", "label": "-Rp80k", "color": "#C98787"}],
            4: [{"type": "Target", "label": "$Rp790k", "color": "#A99ABF"}],
            5: [{"type": "Pemasukan", "label": "+Rp100k", "color": "#7FAE8A"}],
            9: [{"type": "Pengeluaran", "label": "-Rp50k", "color": "#C98787"}],
            13: [{"type": "Pengeluaran", "label": "-Rp59k", "color": "#C98787"}],
            16: [{"type": "Target", "label": "$Rp890k", "color": "#A99ABF"}],
            19: [{"type": "Target", "label": "$Rp200k", "color": "#A99ABF"}],
            22: [{"type": "Pengeluaran", "label": "-Rp69k", "color": "#C98787"}],
            24: [{"type": "Pemasukan", "label": "+Rp140k", "color": "#7FAE8A"}],
            25: [{"type": "Pengeluaran", "label": "-Rp69k", "color": "#C98787"}],
            28: [{"type": "Pemasukan", "label": "+Rp10k", "color": "#7FAE8A"}],
        }
        self.calendar_data_updated.emit({
            "year": self._calendar_year,
            "month": self._calendar_month,
            "month_name": "September 2026",
            "events": day_events
        })

    def _update_recent_transactions(self):
        recent = []
        for tx in mock_store.transactions[:3]:
            if tx.type == TransactionType.PEMASUKAN:
                amount_str = f"+{format_rupiah(tx.amount)}"
                color = "#7FAE8A"
            elif tx.type == TransactionType.PENGELUARAN:
                amount_str = f"-{format_rupiah(tx.amount)}"
                color = "#C98787"
            else:
                amount_str = format_rupiah(tx.amount)
                color = "#A99ABF"

            recent.append({
                "id": tx.id,
                "title": tx.notes if tx.notes else tx.category,
                "category": tx.category,
                "type": tx.type,
                "date": tx.date,
                "amount_formatted": amount_str,
                "color": color
            })
        self.recent_transactions_updated.emit(recent)

    def _update_targets_preview(self):
        preview = []
        for t in mock_store.targets[:2]:
            percent = int((t.collected_amount / t.target_amount) * 100) if t.target_amount > 0 else 0
            preview.append({
                "id": t.id,
                "name": t.name,
                "collected_formatted": format_rupiah(t.collected_amount),
                "target_formatted": format_rupiah(t.target_amount),
                "progress_percent": min(percent, 100),
                "priority": t.priority,
            })
        self.targets_preview_updated.emit(preview)

    @Slot(str)
    def set_chart_period(self, period: str):
        """Slot to handle chart period dropdown changes."""
        self._current_chart_period = period
        self._update_chart()

    @Slot(int, int)
    def set_calendar_month(self, year: int, month: int):
        """Slot to navigate calendar month."""
        self._calendar_year = year
        self._calendar_month = month
        self._update_calendar()
