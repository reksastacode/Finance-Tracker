"""
Utility functions for Indonesian currency formatting, date parsing, and text helpers.
"""
from datetime import datetime, date
import re

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]
BULAN_SINGKAT = [
    "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
    "Jul", "Agt", "Sep", "Okt", "Nov", "Des"
]

def format_rupiah(amount: int | float, with_prefix: bool = True) -> str:
    """Format integer/float to Indonesian Rupiah currency format, e.g. Rp 1.000.000"""
    try:
        val = int(amount)
    except (ValueError, TypeError):
        val = 0
        
    is_negative = val < 0
    formatted = f"{abs(val):,}".replace(",", ".")
    
    if is_negative:
        return f"-Rp {formatted}" if with_prefix else f"-{formatted}"
    return f"Rp {formatted}" if with_prefix else formatted


def parse_rupiah(text: str) -> int:
    """Parse text like 'Rp 1.000.000' or '1000000' into integer."""
    if not text:
        return 0
    # Keep only digits
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return 0
    return int(digits)


def format_indonesian_date(dt: date | datetime | None = None) -> str:
    """Formats date to Indonesian standard, e.g. 'Senin, 3 September 2026'"""
    if dt is None:
        dt = date.today()
    elif isinstance(dt, datetime):
        dt = dt.date()
        
    day_name = HARI[dt.weekday()]
    month_name = BULAN[dt.month - 1]
    return f"{day_name}, {dt.day} {month_name} {dt.year}"


def format_short_date(dt: date | datetime | None = None) -> str:
    """Formats date to 'DD/MM/YYYY', e.g. '25/07/2026'"""
    if dt is None:
        dt = date.today()
    return dt.strftime("%d/%m/%Y")


def format_compact_rupiah(amount: int | float) -> str:
    """
    Format large numbers compactly, e.g.:
    10000000 -> '10 jt'
    500000 -> '500k'
    """
    abs_val = abs(amount)
    sign = "-" if amount < 0 else ("+" if amount > 0 else "")
    
    if abs_val >= 1_000_000_000:
        val = abs_val / 1_000_000_000
        formatted = f"{val:.1f}".rstrip("0").rstrip(".")
        return f"{sign}Rp{formatted} M"
    elif abs_val >= 1_000_000:
        val = abs_val / 1_000_000
        formatted = f"{val:.1f}".rstrip("0").rstrip(".")
        return f"{sign}Rp{formatted} jt"
    elif abs_val >= 1_000:
        val = abs_val / 1_000
        formatted = f"{val:.0f}"
        return f"{sign}Rp{formatted}k"
    else:
        return f"{sign}Rp{abs_val}"
