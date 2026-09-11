"""
Category ViewModel.
Manages category tabs (Pengeluaran vs Pemasukan), category card data,
creation, editing, and deletion events.
"""
from PySide6.QtCore import Signal, Slot
from src.viewmodels.base_viewmodel import BaseViewModel
from src.core.mock_data import mock_store, TransactionType

class CategoryViewModel(BaseViewModel):
    # Signals for View
    categories_updated = Signal(list, str)  # (categories_list, current_tab)
    category_operation_completed = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_tab = TransactionType.PENGELUARAN

    def refresh(self):
        """Refreshes active category list."""
        self._load_categories()

    @Slot(str)
    def set_active_tab(self, tab_type: str):
        """Slot when user switches between Pengeluaran and Pemasukan tabs."""
        self._current_tab = tab_type
        self._load_categories()

    def _load_categories(self):
        filtered = [
            {
                "id": cat.id,
                "name": cat.name,
                "type": cat.type,
                "description": cat.description
            }
            for cat in mock_store.categories
            if cat.type == self._current_tab
        ]
        self.categories_updated.emit(filtered, self._current_tab)

    @Slot(str, str, str)
    def add_category(self, name: str, cat_type: str, description: str):
        """Adds a new category."""
        if not name.strip():
            self.category_operation_completed.emit(False, "Nama kategori tidak boleh kosong!")
            self.notify_toast("Nama kategori tidak boleh kosong!", "warning")
            return

        mock_store.add_category(name.strip(), cat_type or self._current_tab, description.strip())
        self.notify_data_changed()
        self._load_categories()
        self.notify_toast("Kategori berhasil ditambahkan!", "success")
        self.category_operation_completed.emit(True, "Kategori berhasil ditambahkan!")

    @Slot(str, str, str)
    def update_category(self, cat_id: str, name: str, description: str):
        """Updates an existing category."""
        if not name.strip():
            self.category_operation_completed.emit(False, "Nama kategori tidak boleh kosong!")
            self.notify_toast("Nama kategori tidak boleh kosong!", "warning")
            return

        success = mock_store.update_category(cat_id, name.strip(), description.strip())
        if success:
            self.notify_data_changed()
            self._load_categories()
            self.notify_toast("Kategori berhasil diperbarui!", "success")
            self.category_operation_completed.emit(True, "Kategori berhasil diperbarui!")
        else:
            self.notify_toast("Gagal memperbarui kategori.", "error")
            self.category_operation_completed.emit(False, "Gagal memperbarui kategori.")

    @Slot(str)
    def delete_category(self, cat_id: str):
        """Deletes a category."""
        success = mock_store.delete_category(cat_id)
        if success:
            self.notify_data_changed()
            self._load_categories()
            self.notify_toast("Kategori berhasil dihapus!", "info")
            self.category_operation_completed.emit(True, "Kategori berhasil dihapus!")
        else:
            self.notify_toast("Gagal menghapus kategori.", "error")
            self.category_operation_completed.emit(False, "Gagal menghapus kategori.")
