"""
In-Memory Mock Store for Keuangan Mandiri.
Holds state for testing all Event-Driven mechanisms in UI and ViewModels
without requiring Database/ORM layer.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import uuid

from src.core.constants import TransactionType, TargetPriority

@dataclass
class CategoryModel:
    id: str
    name: str
    type: str  # "Pengeluaran" or "Pemasukan"
    description: str

@dataclass
class TargetModel:
    id: str
    name: str
    target_amount: int
    collected_amount: int
    start_date: str
    deadline_date: str
    priority: str  # "Tinggi", "Sedang", "Rendah"
    notes: str

@dataclass
class TransactionModel:
    id: str
    type: str  # "Pemasukan", "Pengeluaran", "Target"
    category: str
    amount: int
    date: str  # "DD/MM/YYYY"
    notes: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class TargetAllocationModel:
    id: str
    target_id: str
    target_name: str
    amount: int
    date: str
    notes: str


class InMemoryDataStore:
    """
    Central in-memory store for managing data during the session.
    Provides CRUD-like helper methods and calculates running stats.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InMemoryDataStore, cls).__new__(cls)
            cls._instance._init_data()
        return cls._instance

    def _init_data(self):
        self.categories: List[CategoryModel] = [
            # Pengeluaran
            CategoryModel(str(uuid.uuid4()), "Makan", TransactionType.PENGELUARAN, "Pengeluaran untuk makan dan minum"),
            CategoryModel(str(uuid.uuid4()), "Transportasi", TransactionType.PENGELUARAN, "Pengeluaran untuk perjalanan dan transportasi"),
            CategoryModel(str(uuid.uuid4()), "Hiburan", TransactionType.PENGELUARAN, "Pengeluaran untuk hiburan dan rekreasi"),
            CategoryModel(str(uuid.uuid4()), "Pendidikan", TransactionType.PENGELUARAN, "Pengeluaran untuk keperluan pendidikan dan kursus"),
            CategoryModel(str(uuid.uuid4()), "Belanja", TransactionType.PENGELUARAN, "Pengeluaran untuk kebutuhan belanja"),
            CategoryModel(str(uuid.uuid4()), "Kesehatan", TransactionType.PENGELUARAN, "Pengeluaran untuk kesehatan dan obat-obatan"),
            CategoryModel(str(uuid.uuid4()), "Liburan", TransactionType.PENGELUARAN, "Pengeluaran untuk liburan (foya-foya)"),
            CategoryModel(str(uuid.uuid4()), "Transfer", TransactionType.PENGELUARAN, "Pengeluaran untuk orang tua dll"),
            # Pemasukan
            CategoryModel(str(uuid.uuid4()), "Gaji", TransactionType.PEMASUKAN, "Pemasukan dari gaji bulanan"),
            CategoryModel(str(uuid.uuid4()), "Uang saku", TransactionType.PEMASUKAN, "Pemasukan dari orang tua"),
            CategoryModel(str(uuid.uuid4()), "Transfer masuk", TransactionType.PEMASUKAN, "Pemasukan Transfer dari kakak dll"),
            CategoryModel(str(uuid.uuid4()), "Bonus Gaji", TransactionType.PEMASUKAN, "Pemasukan dari bonus gaji bulanan"),
        ]

        self.targets: List[TargetModel] = [
            TargetModel("t1", "Beli PC", 10_000_000, 5_000_000, "25/12/2025", "25 Des 2027", TargetPriority.SEDANG, "Rencananya beli untuk kebutuhan kuliah dan kerja nanti"),
            TargetModel("t2", "Beli Lambo", 7_000_000_000, 1_000_000, "01/01/2026", "25 Des 2035", TargetPriority.TINGGI, "Mobil impian keluarga"),
            TargetModel("t3", "Beli Emas", 15_000_000, 3_000_000, "10/02/2026", "25 Des 2027", TargetPriority.TINGGI, "Investasi masa depan"),
            TargetModel("t4", "Liburan di Eropa", 25_000_000, 10_000_000, "01/03/2026", "12 Agt 2027", TargetPriority.RENDAH, "Liburan musim panas"),
            TargetModel("t5", "Beli Ducati", 1_000_000_000, 50_000_000, "15/01/2026", "30 Apr 2028", TargetPriority.SEDANG, "Motor touring impian"),
            TargetModel("t6", "Beli Penthouse", 15_000_000_000, 100_000_000, "01/01/2026", "01 Jan 2040", TargetPriority.TINGGI, "Tempat tinggal mewah masa depan"),
        ]

        self.transactions: List[TransactionModel] = [
            TransactionModel("tx1", TransactionType.PEMASUKAN, "Gaji", 9_000_000, "01/08/2026", "Gaji bulan Agustus"),
            TransactionModel("tx2", TransactionType.PEMASUKAN, "Uang saku", 5_000_000, "04/08/2026", "Uang saku dari orang tua"),
            TransactionModel("tx3", TransactionType.PENGELUARAN, "Makan", 79_000, "06/08/2026", "Makan malam"),
            TransactionModel("tx4", TransactionType.TARGET, "Beli Lambo", 2_390_000, "14/08/2026", "GASS POLLL, ASSIAPP"),
            TransactionModel("tx5", TransactionType.PENGELUARAN, "Hiburan", 80_000, "26/08/2026", "Nonton bioskop"),
            TransactionModel("tx6", TransactionType.TARGET, "Beli PC", 300_000, "30/08/2026", "Beli PC impian"),
            TransactionModel("tx7", TransactionType.PEMASUKAN, "Gaji", 7_000_000, "01/09/2026", "Gaji bulan September"),
            TransactionModel("tx8", TransactionType.PENGELUARAN, "Belanja", 400_000, "02/09/2026", "Belanja bulanan"),
            TransactionModel("tx9", TransactionType.TARGET, "Liburan di Eropa", 2_000_000, "01/09/2026", "Tabungan liburan"),
            TransactionModel("tx10", TransactionType.PENGELUARAN, "Makan", 200_000, "09/09/2026", "Makan"),
            TransactionModel("tx11", TransactionType.PEMASUKAN, "Gaji", 5_000_000, "15/09/2026", "Gaji Bulanan"),
        ]

        self.target_allocations: List[TargetAllocationModel] = [
            TargetAllocationModel("ta1", "t1", "Beli PC", 3_000_000, "05/09/2026", "Target Beli PC"),
            TargetAllocationModel("ta2", "t2", "Beli Lambo", 500_000, "01/09/2026", "Target Beli Lambo"),
            TargetAllocationModel("ta3", "t3", "Beli Emas", 3_000_000, "28/08/2026", "Target Beli Emas"),
            TargetAllocationModel("ta4", "t4", "Liburan di Eropa", 10_000_000, "18/08/2026", "Target liburan di Eropa"),
            TargetAllocationModel("ta5", "t5", "Beli Ducati", 50_000_000, "26/07/2026", "Target Beli Ducati"),
            TargetAllocationModel("ta6", "t6", "Beli Penthouse", 100_000_000, "13/07/2026", "Target Beli Penthouse"),
            TargetAllocationModel("ta7", "t1", "Beli PC", 2_000_000, "01/07/2026", "Target Beli PC"),
            TargetAllocationModel("ta8", "t2", "Beli Lambo", 500_000, "14/06/2026", "Target Beli Lambo"),
        ]

        # Initial available starting balance
        self.base_balance = 12_000_000

    def get_total_pemasukan(self) -> int:
        return sum(tx.amount for tx in self.transactions if tx.type == TransactionType.PEMASUKAN)

    def get_total_pengeluaran(self) -> int:
        return sum(tx.amount for tx in self.transactions if tx.type == TransactionType.PENGELUARAN)

    def get_total_target_terkumpul(self) -> int:
        return sum(t.collected_amount for t in self.targets)

    def get_total_target_goal(self) -> int:
        return sum(t.target_amount for t in self.targets)

    def get_current_balance(self) -> int:
        # Balance = Initial base + Pemasukan - Pengeluaran - Target alokasi
        # Let's ensure realistic calculation
        pemasukan = self.get_total_pemasukan()
        pengeluaran = self.get_total_pengeluaran()
        target_txs = sum(tx.amount for tx in self.transactions if tx.type == TransactionType.TARGET)
        return self.base_balance + pemasukan - pengeluaran - target_txs

    def add_transaction(self, tx_type: str, category: str, amount: int, tx_date: str, notes: str) -> TransactionModel:
        tx_id = str(uuid.uuid4())[:8]
        new_tx = TransactionModel(tx_id, tx_type, category, amount, tx_date, notes)
        self.transactions.insert(0, new_tx)
        return new_tx

    def delete_transaction(self, tx_id: str) -> bool:
        initial_len = len(self.transactions)
        self.transactions = [tx for tx in self.transactions if tx.id != tx_id]
        return len(self.transactions) < initial_len

    def add_category(self, name: str, cat_type: str, description: str = "") -> CategoryModel:
        cat_id = str(uuid.uuid4())[:8]
        new_cat = CategoryModel(cat_id, name, cat_type, description)
        self.categories.append(new_cat)
        return new_cat

    def delete_category(self, cat_id: str) -> bool:
        initial_len = len(self.categories)
        self.categories = [c for c in self.categories if c.id != cat_id]
        return len(self.categories) < initial_len

    def update_category(self, cat_id: str, name: str, description: str) -> bool:
        for c in self.categories:
            if c.id == cat_id:
                c.name = name
                c.description = description
                return True
        return False

    def add_target(self, name: str, target_amount: int, deadline_date: str, start_date: str, priority: str, notes: str) -> TargetModel:
        t_id = f"t{len(self.targets) + 1}"
        new_t = TargetModel(t_id, name, target_amount, 0, start_date, deadline_date, priority, notes)
        self.targets.append(new_t)
        return new_t

    def update_target(self, target_id: str, name: str, target_amount: int, deadline_date: str, start_date: str, priority: str, notes: str) -> bool:
        for t in self.targets:
            if t.id == target_id:
                t.name = name
                t.target_amount = target_amount
                t.deadline_date = deadline_date
                t.start_date = start_date
                t.priority = priority
                t.notes = notes
                return True
        return False

    def delete_target(self, target_id: str) -> bool:
        initial_len = len(self.targets)
        self.targets = [t for t in self.targets if t.id != target_id]
        return len(self.targets) < initial_len

    def deposit_to_target(self, target_id: str, amount: int, notes: str = "") -> bool:
        for t in self.targets:
            if t.id == target_id:
                t.collected_amount += amount
                # Add to target allocations
                alloc_id = str(uuid.uuid4())[:8]
                today_str = datetime.now().strftime("%d/%m/%Y")
                self.target_allocations.insert(0, TargetAllocationModel(alloc_id, t.id, t.name, amount, today_str, notes or f"Tabungan ke {t.name}"))
                # Also create a transaction of type TARGET
                self.add_transaction(TransactionType.TARGET, t.name, amount, today_str, notes or f"Tabungan ke {t.name}")
                return True
        return False


# Convenience singleton
mock_store = InMemoryDataStore()
