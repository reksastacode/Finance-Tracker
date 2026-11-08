"""
Persistent Data Store for Keuangan Mandiri.
Backed by local SQLite database (src/database/db_manager.py) to ensure
100% data persistence across application restarts, while preserving full
backward compatibility for existing ViewModels, Views, and unit tests.
"""
from typing import List
from datetime import datetime

from src.core.constants import TransactionType, TargetPriority
from src.database.models import (
    CategoryModel,
    TargetModel,
    TransactionModel,
    TargetAllocationModel
)
from src.database.db_manager import DatabaseManager, get_db


class InMemoryDataStore:
    """
    DataStore providing persistent CRUD operations over SQLite 3 database.
    Retains the legacy class name 'InMemoryDataStore' for backward compatibility.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InMemoryDataStore, cls).__new__(cls)
            cls._instance._init_store()
        return cls._instance

    def _init_store(self):
        """Initializes database connection and synchronizes caches."""
        self.db = DatabaseManager.instance()
        self._attachments = {}
        self._load_base_balance()
        self.reload()

    def _load_base_balance(self):
        """Loads base_balance from SQLite app_settings, defaults to 0."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_settings WHERE key = 'base_balance';")
        row = cursor.fetchone()
        cursor.close()
        self.base_balance = int(row["value"]) if row else 0

    def reload(self):
        """Reloads all datasets directly from SQLite database into memory cache."""
        self._categories: List[CategoryModel] = self.db.get_all_categories()
        self._targets: List[TargetModel] = self.db.get_all_targets()
        self._transactions: List[TransactionModel] = self.db.get_all_transactions()
        self._target_allocations: List[TargetAllocationModel] = self.db.get_all_target_allocations()
        self._attachments = self.db.get_attachments_map()

    def reload_from_database(self):
        """Alias for reload()."""
        self.reload()

    # =========================================================================
    # PROPERTIES (Direct access as lists for UI, ViewModels, and Workers)
    # =========================================================================

    @property
    def categories(self) -> List[CategoryModel]:
        return self._categories

    @categories.setter
    def categories(self, value: List[CategoryModel]):
        self._categories = list(value)

    @property
    def targets(self) -> List[TargetModel]:
        return self._targets

    @targets.setter
    def targets(self, value: List[TargetModel]):
        self._targets = list(value)

    @property
    def transactions(self) -> List[TransactionModel]:
        return self._transactions

    @transactions.setter
    def transactions(self, value: List[TransactionModel]):
        self._transactions = list(value)
        # Update SQLite if batch replaced.  Old attachment files would become
        # orphans because their transaction rows are cascaded away.
        self.db.bulk_replace_transactions(self._transactions)
        self._attachments = {}
        try:
            from src.storage.attachments import get_attachment_service

            get_attachment_service().clear_all()
        except Exception:
            pass

    @property
    def target_allocations(self) -> List[TargetAllocationModel]:
        return self._target_allocations

    @target_allocations.setter
    def target_allocations(self, value: List[TargetAllocationModel]):
        self._target_allocations = list(value)

    @property
    def attachments(self) -> dict:
        return dict(self._attachments)

    # =========================================================================
    # TRANSACTION CRUD (Table & Form Input Component)
    # =========================================================================

    def add_transaction(
        self,
        tx_type: str,
        category: str,
        amount: int,
        tx_date: str,
        notes: str,
        attachment_path: str = "",
    ) -> TransactionModel:
        """CREATE: Inserts a new transaction into SQLite and in-memory cache."""
        new_tx = self.db.add_transaction(tx_type, category, amount, tx_date, notes)
        if attachment_path:
            try:
                from src.storage.attachments import get_attachment_service

                metadata = get_attachment_service().store(attachment_path)
                attachment = self.db.add_attachment(
                    transaction_id=new_tx.id,
                    stored_name=metadata["stored_name"],
                    original_name=metadata["original_name"],
                    mime_type=metadata["mime_type"],
                    size_bytes=metadata["size_bytes"],
                    sha256=metadata["sha256"],
                )
                self._attachments[new_tx.id] = attachment
            except Exception:
                # Do not leave a transaction without its requested receipt.
                self.db.delete_transaction(new_tx.id)
                raise
        self._transactions.insert(0, new_tx)
        return new_tx

    def delete_transaction(self, tx_id: str) -> bool:
        """DELETE: Deletes transaction from SQLite and updates cache."""
        attachment = self._attachments.get(tx_id) or self.db.get_attachment_for_transaction(tx_id)
        success = self.db.delete_transaction(tx_id)
        if success:
            self._transactions = [tx for tx in self._transactions if tx.id != tx_id]
            self._attachments.pop(tx_id, None)
            if attachment:
                try:
                    from src.storage.attachments import get_attachment_service

                    get_attachment_service().delete_file(attachment.stored_name)
                except Exception:
                    pass
        return success

    def get_attachment_for_transaction(self, tx_id: str):
        attachment = self._attachments.get(tx_id)
        if attachment is not None:
            return attachment
        return self.db.get_attachment_for_transaction(tx_id)

    def get_total_pemasukan(self) -> int:
        """READ: Total income from SQLite."""
        return self.db.get_total_pemasukan()

    def get_total_pengeluaran(self) -> int:
        """READ: Total expenses from SQLite."""
        return self.db.get_total_pengeluaran()

    def get_current_balance(self) -> int:
        """READ: Calculated balance from SQLite."""
        return self.db.get_current_balance(self.base_balance)

    # =========================================================================
    # CATEGORY CRUD (Grid Component)
    # =========================================================================

    def add_category(self, name: str, cat_type: str, description: str = "") -> CategoryModel:
        """CREATE: Adds a new category to SQLite and cache."""
        new_cat = self.db.add_category(name, cat_type, description)
        self._categories.append(new_cat)
        return new_cat

    def update_category(self, cat_id: str, name: str, description: str = "") -> bool:
        """UPDATE: Modifies existing category in SQLite and cache."""
        success = self.db.update_category(cat_id, name, description)
        if success:
            for c in self._categories:
                if c.id == cat_id:
                    c.name = name
                    c.description = description
                    break
        return success

    def delete_category(self, cat_id: str) -> bool:
        """DELETE: Removes category from SQLite and cache."""
        success = self.db.delete_category(cat_id)
        if success:
            self._categories = [c for c in self._categories if c.id != cat_id]
        return success

    # =========================================================================
    # TARGET CRUD (Grid & Form Dialog Component)
    # =========================================================================

    def add_target(self, name: str, target_amount: int, deadline_date: str, start_date: str, priority: str, notes: str) -> TargetModel:
        """CREATE: Inserts a new financial goal into SQLite and cache."""
        new_t = self.db.add_target(name, target_amount, deadline_date, start_date, priority, notes)
        self._targets.append(new_t)
        return new_t

    def update_target(self, target_id: str, name: str, target_amount: int, deadline_date: str, start_date: str, priority: str, notes: str) -> bool:
        """UPDATE: Updates an existing financial goal in SQLite and cache."""
        success = self.db.update_target(target_id, name, target_amount, deadline_date, start_date, priority, notes)
        if success:
            for t in self._targets:
                if t.id == target_id:
                    t.name = name
                    t.target_amount = target_amount
                    t.deadline_date = deadline_date
                    t.start_date = start_date
                    t.priority = priority
                    t.notes = notes
                    break
        return success

    def delete_target(self, target_id: str) -> bool:
        """DELETE: Deletes target from SQLite and cache."""
        success = self.db.delete_target(target_id)
        if success:
            self._targets = [t for t in self._targets if t.id != target_id]
            self._target_allocations = [a for a in self._target_allocations if a.target_id != target_id]
        return success

    def deposit_to_target(self, target_id: str, amount: int, notes: str = "") -> bool:
        """DEPOSIT: Allocates funds to target in SQLite with atomic transaction."""
        success = self.db.deposit_to_target(target_id, amount, notes)
        if success:
            # Sync target collected amount
            for t in self._targets:
                if t.id == target_id:
                    t.collected_amount += amount
                    break
            # Reload allocations and transactions
            self._target_allocations = self.db.get_all_target_allocations()
            self._transactions = self.db.get_all_transactions()
        return success

    def get_total_target_terkumpul(self) -> int:
        return self.db.get_total_target_terkumpul()

    def get_total_target_goal(self) -> int:
        return self.db.get_total_target_goal()

    def reset_database(self, keep_categories: bool = True):
        """Resets SQLite database and refreshes all internal in-memory caches."""
        self.db.reset_database(keep_categories=keep_categories)
        try:
            from src.storage.attachments import get_attachment_service

            get_attachment_service().clear_all()
        except Exception:
            pass
        self._load_base_balance()
        self.reload_from_database()


# Unified Singleton Instance
mock_store = InMemoryDataStore()
