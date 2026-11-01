"""
Dashboard ViewModel.
Manages summary calculations, chart series data, calendar aggregates,
and recent activity feeds through PySide6 Signals and Slots based on current system date.
All metrics are reactively computed from actual persistent database records.
"""
from datetime import date, timedelta
import calendar
from PySide6.QtCore import Signal, Slot
from src.viewmodels.base_viewmodel import BaseViewModel
from src.core.mock_data import mock_store, TransactionType
from src.core.utils import format_rupiah, BULAN_SINGKAT, BULAN


def _parse_tx_date(d_str: str):
    """Safely parse DD/MM/YYYY transaction date string into datetime.date object."""
    if not d_str:
        return None
    try:
        parts = d_str.split("/")
        if len(parts) == 3:
            return date(int(parts[2]), int(parts[1]), int(parts[0]))
    except Exception:
        pass
    return None


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
        total_target = sum(t.collected_amount for t in mock_store.targets)

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
        """Generates chart series dynamically from actual transaction records."""
        today = date.today()
        current_day = today.day
        current_month = today.month
        current_year = today.year
        month_abbr = BULAN_SINGKAT[current_month - 1]

        # Pre-group transactions by date
        tx_by_date = {}
        for tx in mock_store.transactions:
            d = _parse_tx_date(tx.date)
            if d:
                if d not in tx_by_date:
                    tx_by_date[d] = {"p": 0, "k": 0, "t": 0}
                if tx.type == TransactionType.PEMASUKAN:
                    tx_by_date[d]["p"] += tx.amount
                elif tx.type == TransactionType.PENGELUARAN:
                    tx_by_date[d]["k"] += tx.amount
                elif tx.type == TransactionType.TARGET:
                    tx_by_date[d]["t"] += tx.amount

        if self._current_chart_period == "Minggu ini":
            start_of_week = today - timedelta(days=today.weekday())
            labels = []
            for i in range(7):
                d = start_of_week + timedelta(days=i)
                labels.append(f"{d.day} {BULAN_SINGKAT[d.month - 1]}")

            cutoff = today.weekday() + 1
            pemasukan_series = []
            pengeluaran_series = []
            target_series = []

            for i in range(cutoff):
                d = start_of_week + timedelta(days=i)
                entry = tx_by_date.get(d, {"p": 0, "k": 0, "t": 0})
                pemasukan_series.append(round(entry["p"] / 1_000_000, 2))
                pengeluaran_series.append(round(entry["k"] / 1_000_000, 2))
                target_series.append(round(entry["t"] / 1_000_000, 2))

        elif self._current_chart_period == "Bulan ini":
            num_days = calendar.monthrange(current_year, current_month)[1]
            labels = [f"{d} {month_abbr}" for d in range(1, num_days + 1)]
            cutoff = max(1, min(current_day, num_days))

            pemasukan_series = []
            pengeluaran_series = []
            target_series = []

            for d_num in range(1, cutoff + 1):
                d = date(current_year, current_month, d_num)
                entry = tx_by_date.get(d, {"p": 0, "k": 0, "t": 0})
                pemasukan_series.append(round(entry["p"] / 1_000_000, 2))
                pengeluaran_series.append(round(entry["k"] / 1_000_000, 2))
                target_series.append(round(entry["t"] / 1_000_000, 2))

        else: # Tahun ini
            labels = list(BULAN_SINGKAT)
            cutoff = max(1, min(current_month, 12))

            monthly_data = {m: {"p": 0, "k": 0, "t": 0} for m in range(1, 13)}
            for d, entry in tx_by_date.items():
                if d.year == current_year:
                    monthly_data[d.month]["p"] += entry["p"]
                    monthly_data[d.month]["k"] += entry["k"]
                    monthly_data[d.month]["t"] += entry["t"]

            pemasukan_series = [round(monthly_data[m]["p"] / 1_000_000, 2) for m in range(1, cutoff + 1)]
            pengeluaran_series = [round(monthly_data[m]["k"] / 1_000_000, 2) for m in range(1, cutoff + 1)]
            target_series = [round(monthly_data[m]["t"] / 1_000_000, 2) for m in range(1, cutoff + 1)]

        all_vals = pemasukan_series + pengeluaran_series + target_series
        max_val = max(all_vals) if all_vals else 0.0
        if max_val <= 0:
            max_val = 1.0
        elif max_val < 3.0:
            max_val = 3.0
        elif max_val < 6.0:
            max_val = 6.0
        elif max_val < 12.0:
            max_val = 12.0
        else:
            max_val = round(max_val * 1.2, 1)

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
        """Calendar daily aggregate tags based on active month and real transactions."""
        month_name = f"{BULAN[self._calendar_month - 1]} {self._calendar_year}"

        day_totals = {}
        for tx in mock_store.transactions:
            d = _parse_tx_date(tx.date)
            if d and d.year == self._calendar_year and d.month == self._calendar_month:
                day = d.day
                if day not in day_totals:
                    day_totals[day] = {"Pemasukan": 0, "Pengeluaran": 0, "Target": 0}
                if tx.type in day_totals[day]:
                    day_totals[day][tx.type] += tx.amount

        def format_chip(amount: int, prefix: str) -> str:
            if amount >= 1_000_000:
                val = amount / 1_000_000
                return f"{prefix}Rp{int(val) if val.is_integer() else f'{val:.1f}'}jt"
            elif amount >= 1_000:
                return f"{prefix}Rp{amount // 1000}k"
            else:
                return f"{prefix}Rp{amount}"

        day_events = {}
        for day, totals in day_totals.items():
            events = []
            if totals["Pengeluaran"] > 0:
                events.append({
                    "type": "Pengeluaran",
                    "label": format_chip(totals["Pengeluaran"], "-"),
                    "color": "#C98787"
                })
            if totals["Target"] > 0:
                events.append({
                    "type": "Target",
                    "label": format_chip(totals["Target"], "$"),
                    "color": "#A99ABF"
                })
            if totals["Pemasukan"] > 0:
                events.append({
                    "type": "Pemasukan",
                    "label": format_chip(totals["Pemasukan"], "+"),
                    "color": "#7FAE8A"
                })
            if events:
                day_events[day] = events

        self.calendar_data_updated.emit({
            "year": self._calendar_year,
            "month": self._calendar_month,
            "month_name": month_name,
            "events": day_events
        })

    def _update_recent_transactions(self):
        recent = []
        for tx in mock_store.transactions[:6]:
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
        for t in mock_store.targets[:4]:
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
