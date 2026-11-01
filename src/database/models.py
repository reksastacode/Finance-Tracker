"""
Domain Data Models for Keuangan Mandiri.
Standard dataclasses representing persistent entities in SQLite,
complete with audit timestamps (created_at, updated_at).
"""
from dataclasses import dataclass, field
from datetime import datetime


def _current_timestamp_str() -> str:
    """Returns formatted ISO-like timestamp string for database records."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class CategoryModel:
    id: str
    name: str
    type: str  # "Pengeluaran" or "Pemasukan"
    description: str = ""
    created_at: str = field(default_factory=_current_timestamp_str)
    updated_at: str = field(default_factory=_current_timestamp_str)


@dataclass
class TargetModel:
    id: str
    name: str
    target_amount: int
    collected_amount: int = 0
    start_date: str = ""
    deadline_date: str = ""
    priority: str = "Sedang"  # "Tinggi", "Sedang", "Rendah"
    notes: str = ""
    created_at: str = field(default_factory=_current_timestamp_str)
    updated_at: str = field(default_factory=_current_timestamp_str)


@dataclass
class TransactionModel:
    id: str
    type: str  # "Pemasukan", "Pengeluaran", "Target"
    category: str
    amount: int
    date: str  # "DD/MM/YYYY"
    notes: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    created_at: str = field(default_factory=_current_timestamp_str)
    updated_at: str = field(default_factory=_current_timestamp_str)


@dataclass
class TargetAllocationModel:
    id: str
    target_id: str
    target_name: str
    amount: int
    date: str  # "DD/MM/YYYY"
    notes: str = ""
    created_at: str = field(default_factory=_current_timestamp_str)
