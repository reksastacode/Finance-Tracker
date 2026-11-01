"""
Database Manager for Keuangan Mandiri.
Implements local persistent storage using SQLite 3 with WAL mode,
thread-safe connection pooling, full CRUD operations, automatic audit timestamps
(created_at, updated_at), database triggers, and automatic seeding.
"""
import os
import uuid
import random
import sqlite3
import threading
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from src.core.constants import TransactionType, TargetPriority
from src.database.models import (
    CategoryModel,
    TargetModel,
    TransactionModel,
    TargetAllocationModel,
    _current_timestamp_str
)

# Resolve default SQLite database path in project root / data
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
DEFAULT_DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DATA_DIR, "keuangan_mandiri.db")


class DatabaseManager:
    """
    Central database manager handling SQLite connections, schema initialization,
    automatic column migrations, audit triggers, and transactional CRUD operations.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._thread_local = threading.local()

        # Ensure database directory exists
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

        # Initialize schema, migrations, and seed data
        self._init_schema()
        self._seed_initial_data_if_empty()

    @classmethod
    def instance(cls, db_path: str = DEFAULT_DB_PATH) -> "DatabaseManager":
        """Singleton accessor."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = DatabaseManager(db_path)
            return cls._instance

    @classmethod
    def reset_instance(cls, db_path: str = DEFAULT_DB_PATH) -> "DatabaseManager":
        """Resets singleton instance (useful for test isolation)."""
        with cls._lock:
            cls._instance = DatabaseManager(db_path)
            return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        """
        Retrieves a thread-safe connection instance for the calling thread.
        Enables WAL mode and foreign key constraints for reliable concurrency.
        """
        if not hasattr(self._thread_local, "conn") or self._thread_local.conn is None:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if self.db_path != ":memory:":
                cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA synchronous = NORMAL;")
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("PRAGMA cache_size = -64000;")  # 64MB memory cache
            cursor.close()
            self._thread_local.conn = conn

        return self._thread_local.conn

    def _init_schema(self):
        """Creates tables, audit timestamps, triggers, and indexes."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. Categories Table (Grid Component)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Targets Table (Grid & Modal Form Component)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS targets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                target_amount INTEGER NOT NULL,
                collected_amount INTEGER NOT NULL DEFAULT 0,
                start_date TEXT,
                deadline_date TEXT,
                priority TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. Transactions Table (Table & Form Input Component)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount INTEGER NOT NULL,
                date TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. Target Allocations Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS target_allocations (
                id TEXT PRIMARY KEY,
                target_id TEXT NOT NULL,
                target_name TEXT NOT NULL,
                amount INTEGER NOT NULL,
                date TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 5. Application Settings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)

        # --- Automatic Schema Migrations (Ensure created_at and updated_at exist) ---
        self._ensure_column(cursor, "categories", "created_at", "TIMESTAMP")
        self._ensure_column(cursor, "categories", "updated_at", "TIMESTAMP")
        self._ensure_column(cursor, "targets", "created_at", "TIMESTAMP")
        self._ensure_column(cursor, "targets", "updated_at", "TIMESTAMP")
        self._ensure_column(cursor, "transactions", "created_at", "TIMESTAMP")
        self._ensure_column(cursor, "transactions", "updated_at", "TIMESTAMP")
        self._ensure_column(cursor, "target_allocations", "created_at", "TIMESTAMP")

        # --- Audit Triggers for automatic updated_at maintenance ---
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_categories_updated_at
            AFTER UPDATE ON categories
            FOR EACH ROW
            BEGIN
                UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_targets_updated_at
            AFTER UPDATE ON targets
            FOR EACH ROW
            BEGIN
                UPDATE targets SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_transactions_updated_at
            AFTER UPDATE ON transactions
            FOR EACH ROW
            BEGIN
                UPDATE transactions SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
        """)

        # --- Performance & Timestamp Indexes ---
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_type ON transactions(type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_category ON transactions(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_created ON transactions(created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cat_type ON categories(type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cat_created ON categories(created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_targets_created ON targets(created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alloc_target ON target_allocations(target_id);")

        conn.commit()
        cursor.close()

    def _ensure_column(self, cursor: sqlite3.Cursor, table_name: str, column_name: str, col_def: str):
        """Adds column to table if it doesn't already exist (safe migration)."""
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row["name"] for row in cursor.fetchall()]
        if column_name not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {col_def};")
            cursor.execute(f"UPDATE {table_name} SET {column_name} = CURRENT_TIMESTAMP WHERE {column_name} IS NULL;")

    def _seed_initial_data_if_empty(self):
        """Seeds standard categories if DB is empty, keeping transactions at 0 for real user input."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM categories;")
        cat_count = cursor.fetchone()["cnt"]

        if cat_count == 0:
            now_ts = _current_timestamp_str()

            # 1. Seed Categories
            initial_categories = [
                CategoryModel(str(uuid.uuid4()), "Makan", TransactionType.PENGELUARAN, "Pengeluaran untuk makan dan minum", now_ts, now_ts),
                CategoryModel(str(uuid.uuid4()), "Transportasi", TransactionType.PENGELUARAN, "Pengeluaran untuk perjalanan dan transportasi", now_ts, now_ts),
                CategoryModel(str(uuid.uuid4()), "Hiburan", TransactionType.PENGELUARAN, "Pengeluaran untuk hiburan dan rekreasi", now_ts, now_ts),
                CategoryModel(str(uuid.uuid4()), "Pendidikan", TransactionType.PENGELUARAN, "Pengeluaran untuk keperluan pendidikan dan kursus", now_ts, now_ts),
                CategoryModel(str(uuid.uuid4()), "Belanja", TransactionType.PENGELUARAN, "Pengeluaran untuk kebutuhan belanja", now_ts, now_ts),
                CategoryModel(str(uuid.uuid4()), "Kesehatan", TransactionType.PENGELUARAN, "Pengeluaran untuk kesehatan dan obat-obatan", now_ts, now_ts),
                CategoryModel(str(uuid.uuid4()), "Liburan", TransactionType.PENGELUARAN, "Pengeluaran untuk liburan (foya-foya)", now_ts, now_ts),
                CategoryModel(str(uuid.uuid4()), "Transfer", TransactionType.PENGELUARAN, "Pengeluaran untuk orang tua dll", now_ts, now_ts),
                CategoryModel(str(uuid.uuid4()), "Gaji", TransactionType.PEMASUKAN, "Pemasukan dari gaji bulanan", now_ts, now_ts),
                CategoryModel(str(uuid.uuid4()), "Uang saku", TransactionType.PEMASUKAN, "Pemasukan dari orang tua", now_ts, now_ts),
                CategoryModel(str(uuid.uuid4()), "Transfer masuk", TransactionType.PEMASUKAN, "Pemasukan Transfer dari kakak dll", now_ts, now_ts),
                CategoryModel(str(uuid.uuid4()), "Bonus Gaji", TransactionType.PEMASUKAN, "Pemasukan dari bonus gaji bulanan", now_ts, now_ts),
            ]
            cursor.executemany(
                "INSERT INTO categories (id, name, type, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?);",
                [(c.id, c.name, c.type, c.description, c.created_at, c.updated_at) for c in initial_categories]
            )
            cursor.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('database_initialized', 'true');")
            cursor.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('base_balance', '0');")
            conn.commit()

        cursor.close()

    def seed_demo_dataset(self):
        """Seeds full demo dataset (2000 transactions, 6 targets, allocations) for presentations/benchmarks."""
        conn = self.get_connection()
        cursor = conn.cursor()
        now_ts = _current_timestamp_str()

        # 2. Seed Targets
        initial_targets = [
            TargetModel("t1", "Beli PC", 10_000_000, 5_000_000, "25/12/2025", "25 Des 2027", TargetPriority.SEDANG, "Rencananya beli untuk kebutuhan kuliah dan kerja nanti", now_ts, now_ts),
            TargetModel("t2", "Beli Lambo", 7_000_000_000, 1_000_000, "01/01/2026", "25 Des 2035", TargetPriority.TINGGI, "Mobil impian keluarga", now_ts, now_ts),
            TargetModel("t3", "Beli Emas", 15_000_000, 3_000_000, "10/02/2026", "25 Des 2027", TargetPriority.TINGGI, "Investasi masa depan", now_ts, now_ts),
            TargetModel("t4", "Liburan di Eropa", 25_000_000, 10_000_000, "01/03/2026", "12 Agt 2027", TargetPriority.RENDAH, "Liburan musim panas", now_ts, now_ts),
            TargetModel("t5", "Beli Ducati", 1_000_000_000, 50_000_000, "15/01/2026", "30 Apr 2028", TargetPriority.SEDANG, "Motor touring impian", now_ts, now_ts),
            TargetModel("t6", "Beli Penthouse", 15_000_000_000, 100_000_000, "01/01/2026", "01 Jan 2040", TargetPriority.TINGGI, "Tempat tinggal mewah masa depan", now_ts, now_ts),
        ]
        cursor.executemany(
            "INSERT INTO targets (id, name, target_amount, collected_amount, start_date, deadline_date, priority, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            [(t.id, t.name, t.target_amount, t.collected_amount, t.start_date, t.deadline_date, t.priority, t.notes, t.created_at, t.updated_at) for t in initial_targets]
        )

        # 3. Seed Target Allocations
        initial_allocations = [
            TargetAllocationModel("ta1", "t1", "Beli PC", 3_000_000, "05/09/2026", "Target Beli PC", now_ts),
            TargetAllocationModel("ta2", "t2", "Beli Lambo", 500_000, "01/09/2026", "Target Beli Lambo", now_ts),
            TargetAllocationModel("ta3", "t3", "Beli Emas", 3_000_000, "28/08/2026", "Target Beli Emas", now_ts),
            TargetAllocationModel("ta4", "t4", "Liburan di Eropa", 10_000_000, "18/08/2026", "Target liburan di Eropa", now_ts),
            TargetAllocationModel("ta5", "t5", "Beli Ducati", 50_000_000, "26/07/2026", "Target Beli Ducati", now_ts),
            TargetAllocationModel("ta6", "t6", "Beli Penthouse", 100_000_000, "13/07/2026", "Target Beli Penthouse", now_ts),
            TargetAllocationModel("ta7", "t1", "Beli PC", 2_000_000, "01/07/2026", "Target Beli PC", now_ts),
            TargetAllocationModel("ta8", "t2", "Beli Lambo", 500_000, "14/06/2026", "Target Beli Lambo", now_ts),
        ]
        cursor.executemany(
            "INSERT INTO target_allocations (id, target_id, target_name, amount, date, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
            [(a.id, a.target_id, a.target_name, a.amount, a.date, a.notes, a.created_at) for a in initial_allocations]
        )

        # 4. Seed Settings
        cursor.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('base_balance', '12000000');")

        # 5. Seed 2,000 Transactions (11 fixed + 1,989 generated)
        initial_11_txs = [
            TransactionModel("tx1", TransactionType.PEMASUKAN, "Gaji", 9_000_000, "01/08/2026", "Gaji bulan Agustus", created_at=now_ts, updated_at=now_ts),
            TransactionModel("tx2", TransactionType.PEMASUKAN, "Uang saku", 5_000_000, "04/08/2026", "Uang saku dari orang tua", created_at=now_ts, updated_at=now_ts),
            TransactionModel("tx3", TransactionType.PENGELUARAN, "Makan", 79_000, "06/08/2026", "Makan malam", created_at=now_ts, updated_at=now_ts),
            TransactionModel("tx4", TransactionType.TARGET, "Beli Lambo", 2_390_000, "14/08/2026", "GASS POLLL, ASSIAPP", created_at=now_ts, updated_at=now_ts),
            TransactionModel("tx5", TransactionType.PENGELUARAN, "Hiburan", 80_000, "26/08/2026", "Nonton bioskop", created_at=now_ts, updated_at=now_ts),
            TransactionModel("tx6", TransactionType.TARGET, "Beli PC", 300_000, "30/08/2026", "Beli PC impian", created_at=now_ts, updated_at=now_ts),
            TransactionModel("tx7", TransactionType.PEMASUKAN, "Gaji", 7_000_000, "01/09/2026", "Gaji bulan September", created_at=now_ts, updated_at=now_ts),
            TransactionModel("tx8", TransactionType.PENGELUARAN, "Belanja", 400_000, "02/09/2026", "Belanja bulanan", created_at=now_ts, updated_at=now_ts),
            TransactionModel("tx9", TransactionType.TARGET, "Liburan di Eropa", 2_000_000, "01/09/2026", "Tabungan liburan", created_at=now_ts, updated_at=now_ts),
            TransactionModel("tx10", TransactionType.PENGELUARAN, "Makan", 200_000, "09/09/2026", "Makan", created_at=now_ts, updated_at=now_ts),
            TransactionModel("tx11", TransactionType.PEMASUKAN, "Gaji", 5_000_000, "15/09/2026", "Gaji Bulanan", created_at=now_ts, updated_at=now_ts),
        ]

        all_txs: List[TransactionModel] = list(initial_11_txs)
        target_count = 2000
        rng = random.Random(2026)

        pengeluaran_catalog = [
            ("Makan", 20_000, 85_000, ["Makan siang di kantor", "Sarapan bubur ayam", "Makan malam penyet", "Kopi & snack sore", "Makan bersama di warung", "Makan malam soto mie"]),
            ("Transportasi", 15_000, 50_000, ["Bensin motor harian", "Ongkos ojek online", "Tarif parkir & tol", "Top up kartu transportasi", "Bensin mobil mingguan"]),
            ("Belanja", 60_000, 350_000, ["Belanja kebutuhan pokok", "Beli sabun & detergen", "Belanja sayur & buah di pasar", "Kebutuhan harian rumah tangga", "Belanja di supermarket"]),
            ("Hiburan", 40_000, 150_000, ["Tiket nonton bioskop", "Langganan streaming film", "Beli kopi di coffee shop", "Voucher game favorit", "Buku novel akhir pekan"]),
            ("Kesehatan", 30_000, 200_000, ["Beli vitamin & suplemen", "Obat flu di apotek", "Koyo & minyak angin", "Pemeriksaan kesehatan di klinik", "Pembersih luka & perban"]),
            ("Pendidikan", 80_000, 450_000, ["Beli buku kuliah", "Langganan platform belajar", "Alat tulis & fotokopi modul", "Kursus online bersertifikat"]),
            ("Liburan", 120_000, 500_000, ["Tiket rekreasi akhir pekan", "Jajan di tempat wisata", "Sewa perlengkapan liburan", "Tiket museum"]),
            ("Transfer", 100_000, 500_000, ["Transfer bantuan adik", "Transfer uang jajan keluarga", "Patungan acara kantor", "Iuran lingkungan bulanan"]),
        ]

        pemasukan_catalog = [
            ("Gaji", 5_000_000, 12_000_000, ["Gaji pokok bulanan", "Honor project freelance", "Pemasukan kerja sampingan", "Fee konsultasi visual"]),
            ("Bonus Gaji", 1_000_000, 4_000_000, ["Bonus performa bulanan", "Uang lembur proyek", "Insentif pencapaian target", "Bonus apresiasi tim"]),
            ("Uang saku", 500_000, 1_500_000, ["Uang saku dari orang tua", "Kiriman keluarga", "Bantuan operasional bulanan"]),
            ("Transfer masuk", 250_000, 1_200_000, ["Transfer pelunasan patungan", "Hasil penjualan preloved", "Uang ganti reimburse"]),
        ]

        target_catalog = [
            ("Beli PC", 200_000, 800_000, "Tabungan berkala untuk Beli PC"),
            ("Beli Lambo", 500_000, 1_500_000, "Alokasi target Beli Lambo"),
            ("Beli Emas", 300_000, 1_000_000, "Nabung beli emas batangan"),
            ("Liburan di Eropa", 250_000, 800_000, "Tabungan persiapan liburan di Eropa"),
            ("Beli Ducati", 400_000, 1_200_000, "Tabungan impian Beli Ducati"),
            ("Beli Penthouse", 500_000, 2_000_000, "Tabungan properti Penthouse masa depan"),
        ]

        months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]

        for idx in range(len(all_txs) + 1, target_count + 1):
            roll = rng.random()
            m = rng.choice(months)
            d = rng.randint(1, 28)
            date_str = f"{d:02d}/{m}/2026"

            if roll < 0.65:
                cat, min_a, max_a, notes_list = rng.choice(pengeluaran_catalog)
                amt = rng.randint(min_a // 1000, max_a // 1000) * 1000
                note = rng.choice(notes_list)
                all_txs.append(TransactionModel(f"tx{idx}", TransactionType.PENGELUARAN, cat, amt, date_str, note, created_at=now_ts, updated_at=now_ts))
            elif roll < 0.90:
                cat, min_a, max_a, notes_list = rng.choice(pemasukan_catalog)
                amt = rng.randint(min_a // 10000, max_a // 10000) * 10000
                note = rng.choice(notes_list)
                all_txs.append(TransactionModel(f"tx{idx}", TransactionType.PEMASUKAN, cat, amt, date_str, note, created_at=now_ts, updated_at=now_ts))
            else:
                cat, min_a, max_a, note = rng.choice(target_catalog)
                amt = rng.randint(min_a // 10000, max_a // 10000) * 10000
                all_txs.append(TransactionModel(f"tx{idx}", TransactionType.TARGET, cat, amt, date_str, note, created_at=now_ts, updated_at=now_ts))

        cursor.executemany(
            "INSERT INTO transactions (id, type, category, amount, date, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
            [(tx.id, tx.type, tx.category, tx.amount, tx.date, tx.notes, tx.created_at, tx.updated_at) for tx in all_txs]
        )

        cursor.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('database_initialized', 'true');")
        conn.commit()

        cursor.close()

    def reset_database(self, keep_categories: bool = True):
        """
        Resets and clears the SQLite database to a blank state for real user data entry.
        
        Args:
            keep_categories: If True, retains category templates so the user can
                             immediately start creating transactions from the form without
                             having to manually recreate standard categories first.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions;")
        cursor.execute("DELETE FROM target_allocations;")
        cursor.execute("DELETE FROM targets;")
        if not keep_categories:
            cursor.execute("DELETE FROM categories;")
        cursor.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('database_initialized', 'true');")
        cursor.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('base_balance', '0');")
        conn.commit()
        cursor.close()

    # =========================================================================
    # CATEGORY CRUD OPERATIONS (Grid Component)
    # =========================================================================

    def get_transaction_count(self) -> int:
        """Returns total count of transactions in SQLite."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM transactions;")
        cnt = cursor.fetchone()["cnt"]
        cursor.close()
        return cnt

    def get_all_categories(self, cat_type: Optional[str] = None) -> List[CategoryModel]:
        """READ: Retrieves all categories with audit timestamps, ordered alphabetically."""
        conn = self.get_connection()
        cursor = conn.cursor()
        if cat_type:
            cursor.execute("SELECT id, name, type, description, created_at, updated_at FROM categories WHERE type = ? ORDER BY name ASC;", (cat_type,))
        else:
            cursor.execute("SELECT id, name, type, description, created_at, updated_at FROM categories ORDER BY name ASC;")
        rows = cursor.fetchall()
        cursor.close()
        return [
            CategoryModel(
                r["id"], r["name"], r["type"], r["description"] or "",
                created_at=r["created_at"] or _current_timestamp_str(),
                updated_at=r["updated_at"] or _current_timestamp_str()
            )
            for r in rows
        ]

    def add_category(self, name: str, cat_type: str, description: str = "") -> CategoryModel:
        """CREATE: Inserts a new category with created_at and updated_at."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cat_id = str(uuid.uuid4())[:8]
        now_ts = _current_timestamp_str()
        cursor.execute(
            "INSERT INTO categories (id, name, type, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?);",
            (cat_id, name, cat_type, description, now_ts, now_ts)
        )
        conn.commit()
        cursor.close()
        return CategoryModel(cat_id, name, cat_type, description, created_at=now_ts, updated_at=now_ts)

    def update_category(self, cat_id: str, name: str, description: str = "") -> bool:
        """UPDATE: Updates category name and description, refreshing updated_at."""
        conn = self.get_connection()
        cursor = conn.cursor()
        now_ts = _current_timestamp_str()
        cursor.execute(
            "UPDATE categories SET name = ?, description = ?, updated_at = ? WHERE id = ?;",
            (name, description, now_ts, cat_id)
        )
        conn.commit()
        updated = cursor.rowcount > 0
        cursor.close()
        return updated

    def delete_category(self, cat_id: str) -> bool:
        """DELETE: Removes a category from SQLite."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?;", (cat_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        return deleted

    # =========================================================================
    # TARGET CRUD OPERATIONS (Grid & Form Dialog Component)
    # =========================================================================

    def get_all_targets(self) -> List[TargetModel]:
        """READ: Retrieves all targets ordered by creation timestamp."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, target_amount, collected_amount, start_date, deadline_date, priority, notes, created_at, updated_at FROM targets ORDER BY created_at ASC;")
        rows = cursor.fetchall()
        cursor.close()
        return [
            TargetModel(
                r["id"], r["name"], r["target_amount"], r["collected_amount"],
                r["start_date"] or "", r["deadline_date"] or "", r["priority"] or "Sedang", r["notes"] or "",
                created_at=r["created_at"] or _current_timestamp_str(),
                updated_at=r["updated_at"] or _current_timestamp_str()
            )
            for r in rows
        ]

    def add_target(self, name: str, target_amount: int, deadline_date: str, start_date: str, priority: str, notes: str) -> TargetModel:
        """CREATE: Inserts a new financial target with audit timestamps."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM targets;")
        count = cursor.fetchone()["total"]
        t_id = f"t{count + 1}_{str(uuid.uuid4())[:4]}"
        now_ts = _current_timestamp_str()
        cursor.execute(
            "INSERT INTO targets (id, name, target_amount, collected_amount, start_date, deadline_date, priority, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            (t_id, name, target_amount, 0, start_date, deadline_date, priority, notes, now_ts, now_ts)
        )
        conn.commit()
        cursor.close()
        return TargetModel(t_id, name, target_amount, 0, start_date, deadline_date, priority, notes, created_at=now_ts, updated_at=now_ts)

    def update_target(self, target_id: str, name: str, target_amount: int, deadline_date: str, start_date: str, priority: str, notes: str) -> bool:
        """UPDATE: Updates target details and refreshes updated_at."""
        conn = self.get_connection()
        cursor = conn.cursor()
        now_ts = _current_timestamp_str()
        cursor.execute(
            "UPDATE targets SET name = ?, target_amount = ?, deadline_date = ?, start_date = ?, priority = ?, notes = ?, updated_at = ? WHERE id = ?;",
            (name, target_amount, deadline_date, start_date, priority, notes, now_ts, target_id)
        )
        conn.commit()
        updated = cursor.rowcount > 0
        cursor.close()
        return updated

    def delete_target(self, target_id: str) -> bool:
        """DELETE: Removes a target and its allocations atomically."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM targets WHERE id = ?;", (target_id,))
        cursor.execute("DELETE FROM target_allocations WHERE target_id = ?;", (target_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        return deleted

    def deposit_to_target(self, target_id: str, amount: int, notes: str = "", date_str: str = "") -> bool:
        """
        Transactional deposit into target:
        1. Updates target collected_amount and updated_at
        2. Inserts allocation record with created_at
        3. Inserts transaction of type TARGET with created_at
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, collected_amount FROM targets WHERE id = ?;", (target_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return False

        target_name = row["name"]
        new_collected = row["collected_amount"] + amount
        tx_date = date_str or datetime.now().strftime("%d/%m/%Y")
        now_ts = _current_timestamp_str()

        cursor.execute("UPDATE targets SET collected_amount = ?, updated_at = ? WHERE id = ?;", (new_collected, now_ts, target_id))

        # Insert Allocation
        alloc_id = str(uuid.uuid4())[:8]
        cursor.execute(
            "INSERT INTO target_allocations (id, target_id, target_name, amount, date, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
            (alloc_id, target_id, target_name, amount, tx_date, notes or f"Tabungan ke {target_name}", now_ts)
        )

        # Insert Transaction
        tx_id = f"tx_alloc_{str(uuid.uuid4())[:6]}"
        cursor.execute(
            "INSERT INTO transactions (id, type, category, amount, date, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
            (tx_id, TransactionType.TARGET, target_name, amount, tx_date, notes or f"Tabungan ke {target_name}", now_ts, now_ts)
        )

        conn.commit()
        cursor.close()
        return True

    def get_all_target_allocations(self) -> List[TargetAllocationModel]:
        """READ: Retrieves all target allocations sorted by newest created_at."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, target_id, target_name, amount, date, notes, created_at FROM target_allocations ORDER BY created_at DESC, rowid DESC;")
        rows = cursor.fetchall()
        cursor.close()
        return [
            TargetAllocationModel(
                r["id"], r["target_id"], r["target_name"], r["amount"], r["date"], r["notes"] or "",
                created_at=r["created_at"] or _current_timestamp_str()
            )
            for r in rows
        ]

    # =========================================================================
    # TRANSACTION CRUD OPERATIONS (Table & Form Input Component)
    # =========================================================================

    def get_all_transactions(self) -> List[TransactionModel]:
        """READ: Retrieves all transactions ordered chronologically (newest first)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, type, category, amount, date, notes, created_at, updated_at
            FROM transactions
            ORDER BY rowid DESC;
        """)
        rows = cursor.fetchall()
        cursor.close()
        return [
            TransactionModel(
                r["id"], r["type"], r["category"], r["amount"], r["date"], r["notes"] or "",
                created_at=r["created_at"] or _current_timestamp_str(),
                updated_at=r["updated_at"] or _current_timestamp_str()
            )
            for r in rows
        ]

    def add_transaction(self, tx_type: str, category: str, amount: int, tx_date: str, notes: str) -> TransactionModel:
        """CREATE: Inserts a new transaction into SQLite with created_at and updated_at."""
        conn = self.get_connection()
        cursor = conn.cursor()
        tx_id = str(uuid.uuid4())[:8]
        now_ts = _current_timestamp_str()
        cursor.execute(
            "INSERT INTO transactions (id, type, category, amount, date, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
            (tx_id, tx_type, category, amount, tx_date, notes, now_ts, now_ts)
        )
        conn.commit()
        cursor.close()
        return TransactionModel(tx_id, tx_type, category, amount, tx_date, notes, created_at=now_ts, updated_at=now_ts)

    def delete_transaction(self, tx_id: str) -> bool:
        """DELETE: Removes a transaction from SQLite."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?;", (tx_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        return deleted

    def bulk_replace_transactions(self, transactions: List[TransactionModel]):
        """Replaces all transactions with audit timestamps."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions;")
        now_ts = _current_timestamp_str()
        cursor.executemany(
            "INSERT INTO transactions (id, type, category, amount, date, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
            [
                (
                    tx.id, tx.type, tx.category, tx.amount, tx.date, tx.notes,
                    getattr(tx, "created_at", now_ts), getattr(tx, "updated_at", now_ts)
                )
                for tx in transactions
            ]
        )
        conn.commit()
        cursor.close()

    # =========================================================================
    # AGGREGATION & METRICS QUERIES
    # =========================================================================

    def get_total_pemasukan(self) -> int:
        """SQL SUM aggregation for Income."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM transactions WHERE type = ?;", (TransactionType.PEMASUKAN,))
        total = cursor.fetchone()["total"]
        cursor.close()
        return int(total)

    def get_total_pengeluaran(self) -> int:
        """SQL SUM aggregation for Expense."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM transactions WHERE type = ?;", (TransactionType.PENGELUARAN,))
        total = cursor.fetchone()["total"]
        cursor.close()
        return int(total)

    def get_total_target_terkumpul(self) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(collected_amount), 0) AS total FROM targets;")
        total = cursor.fetchone()["total"]
        cursor.close()
        return int(total)

    def get_total_target_goal(self) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(target_amount), 0) AS total FROM targets;")
        total = cursor.fetchone()["total"]
        cursor.close()
        return int(total)

    def get_current_balance(self, base_balance: Optional[int] = None) -> int:
        """Calculates current financial balance via SQL aggregations."""
        if base_balance is None:
            try:
                base_balance = int(self.get_setting("base_balance", "0"))
            except (ValueError, TypeError):
                base_balance = 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN type = 'Pemasukan' THEN amount ELSE 0 END), 0) AS inc,
                COALESCE(SUM(CASE WHEN type = 'Pengeluaran' THEN amount ELSE 0 END), 0) AS exp,
                COALESCE(SUM(CASE WHEN type = 'Target' THEN amount ELSE 0 END), 0) AS tgt
            FROM transactions;
        """)
        row = cursor.fetchone()
        cursor.close()
        inc = int(row["inc"])
        exp = int(row["exp"])
        tgt = int(row["tgt"])
        return base_balance + inc - exp - tgt

    # =========================================================================
    # SETTINGS & DIAGNOSTICS
    # =========================================================================

    def get_setting(self, key: str, default: str = "") -> str:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_settings WHERE key = ?;", (key,))
        row = cursor.fetchone()
        cursor.close()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?);", (key, value))
        conn.commit()
        cursor.close()

    def close_connection(self):
        """Closes current thread's connection and checkpoints WAL."""
        if hasattr(self._thread_local, "conn") and self._thread_local.conn is not None:
            try:
                self._thread_local.conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                self._thread_local.conn.close()
            except Exception:
                pass
            self._thread_local.conn = None

    def get_db_stats(self) -> Dict[str, Any]:
        """Provides statistical telemetry of the SQLite database for presentation."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM transactions;")
        tx_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM categories;")
        cat_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM targets;")
        tgt_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM target_allocations;")
        alloc_count = cursor.fetchone()["total"]

        cursor.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]

        cursor.close()

        file_size_kb = 0.0
        if self.db_path != ":memory:" and os.path.exists(self.db_path):
            file_size_kb = os.path.getsize(self.db_path) / 1024.0

        return {
            "db_path": self.db_path,
            "journal_mode": journal_mode,
            "file_size_kb": file_size_kb,
            "transaction_count": tx_count,
            "category_count": cat_count,
            "target_count": tgt_count,
            "allocation_count": alloc_count,
            "status": "Connected & Persistent"
        }


def get_db() -> DatabaseManager:
    """Convenience getter for the singleton database manager."""
    return DatabaseManager.instance()
