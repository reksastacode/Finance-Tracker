"""
Dashboard ViewModel.
Manages summary calculations, chart series data, calendar aggregates,
and recent activity feeds through PySide6 Signals and Slots based on current system date.
"""
from datetime import date, timedelta
import calendar
from PySide6.QtCore import Signal, Slot
from src.viewmodels.base_viewmodel import BaseViewModel
from src.core.mock_data import mock_store, TransactionType
from src.core.utils import format_rupiah, BULAN_SINGKAT, BULAN

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
        today = date.today()
        self._calendar_year = today.year
        self._calendar_month = today.month

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
        """Generates chart series dynamically up to the current computer date."""
        today = date.today()
        current_day = today.day
        current_month = today.month
        current_year = today.year
        month_abbr = BULAN_SINGKAT[current_month - 1]

        if self._current_chart_period == "Minggu ini":
            # Current calendar week (Monday to Sunday)
            start_of_week = today - timedelta(days=today.weekday())
            labels = []
            for i in range(7):
                d = start_of_week + timedelta(days=i)
                labels.append(f"{d.day} {BULAN_SINGKAT[d.month - 1]}")

            # Days elapsed in current week (Monday=1 .. Sunday=7)
            cutoff = today.weekday() + 1

            seed_p = [1.2, 0.8, 1.5, 0.4, 1.8, 0.9, 2.2]
            seed_k = [0.5, 0.7, 0.3, 0.8, 1.2, 0.6, 1.0]
            seed_t = [0.6, 0.9, 1.3, 1.7, 2.1, 2.5, 2.8]

            pemasukan_series = seed_p[:cutoff]
            pengeluaran_series = seed_k[:cutoff]
            target_series = seed_t[:cutoff]
            max_val = 3.5

        elif self._current_chart_period == "Bulan ini":
            # Days in the current month (e.g. 30 or 31 days)
            num_days = calendar.monthrange(current_year, current_month)[1]
            labels = [f"{d} {month_abbr}" for d in range(1, num_days + 1)]
            cutoff = max(1, min(current_day, num_days))

            seed_p = [1.0, 0.2, 0.5, 1.2, 0.3, 0.0, 1.5, 0.8, 0.4, 2.0, 0.5, 0.2, 0.8, 1.0, 3.5, 0.6, 0.2, 0.4, 1.2, 0.8, 1.5, 0.3, 0.6, 2.2, 0.7, 1.0, 0.4, 1.8, 0.5, 2.5, 1.2]
            seed_k = [0.4, 0.6, 0.3, 0.8, 0.2, 0.5, 0.9, 0.4, 0.7, 1.5, 0.3, 0.8, 0.5, 0.6, 1.8, 0.4, 0.7, 0.3, 0.9, 1.2, 0.6, 0.4, 0.8, 1.4, 0.5, 0.8, 0.3, 1.1, 0.7, 1.6, 0.9]

            pemasukan_series = [seed_p[i % len(seed_p)] for i in range(cutoff)]
            pengeluaran_series = [seed_k[i % len(seed_k)] for i in range(cutoff)]
            target_series = [round(0.2 + (i * 0.15), 2) for i in range(cutoff)]
            max_val = 5.0

        else: # Tahun ini
            labels = list(BULAN_SINGKAT)
            cutoff = max(1, min(current_month, 12))

            seed_p = [5.0, 6.2, 7.0, 6.5, 8.0, 9.0, 8.5, 10.0, 11.5, 10.0, 12.0, 14.0]
            seed_k = [3.0, 3.8, 4.5, 4.0, 5.2, 6.0, 5.5, 6.8, 7.0, 6.5, 7.8, 8.5]
            seed_t = [1.5, 2.8, 4.0, 5.5, 7.0, 8.5, 9.8, 11.2, 12.5, 13.8, 15.0, 16.5]

            pemasukan_series = seed_p[:cutoff]
            pengeluaran_series = seed_k[:cutoff]
            target_series = seed_t[:cutoff]
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
        """Calendar daily aggregate tags based on active month."""
        month_name = f"{BULAN[self._calendar_month - 1]} {self._calendar_year}"
        
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
            "month_name": month_name,
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
