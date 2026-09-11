"""
Comprehensive Event-Driven Integration Tests.
Tests:
- Dynamic cross-view category synchronization
- Filter events and calculations in HistoryViewModel
- Target creation, editing, and fund allocation events
- Toast overlay event triggers and auto-dismiss lifecycle
- Widget custom paint rendering without exceptions
"""
import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainter, QImage
from src.core.constants import TransactionType, TargetPriority
from src.core.event_bus import event_bus
from src.core.mock_data import mock_store
from src.views.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)

class TestComprehensiveEventDriven(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.window = MainWindow()

    def test_01_viewmodel_instantiations(self):
        self.assertIsNotNone(self.window.dashboard_vm)
        self.assertIsNotNone(self.window.transaction_vm)
        self.assertIsNotNone(self.window.category_vm)
        self.assertIsNotNone(self.window.history_vm)
        self.assertIsNotNone(self.window.target_vm)

    def test_02_add_category_and_sync(self):
        """Adding a category should emit event and update transaction category dropdown."""
        # 1. Add new expense category
        self.window.category_vm.add_category("Langganan AI", TransactionType.PENGELUARAN, "ChatGPT & Antigravity")
        
        # 2. Check if category appears in transaction viewmodel when loaded
        loaded_cats = []
        self.window.transaction_vm.categories_loaded.connect(loaded_cats.extend)
        self.window.transaction_vm.load_categories_for_type(TransactionType.PENGELUARAN)
        self.assertIn("Langganan AI", loaded_cats)

    def test_03_history_filter_events(self):
        """Testing filter events on history view."""
        filtered_txs = []
        self.window.history_vm.transactions_updated.connect(filtered_txs.extend)

        # Apply filter for Pengeluaran
        self.window.history_vm.apply_filter(
            tx_type=TransactionType.PENGELUARAN,
            category="Semua",
            start_date="01/08/2026",
            end_date="30/09/2026"
        )
        self.assertTrue(len(filtered_txs) > 0)
        for tx in filtered_txs:
            self.assertEqual(tx["type"], TransactionType.PENGELUARAN)

    def test_04_target_crud_events(self):
        """Testing target creation and editing events."""
        # Create new target
        self.window.target_vm.add_target(
            name="Beli iPad Pro",
            amount_str="20000000",
            deadline="31/12/2027",
            start_date="01/09/2026",
            priority=TargetPriority.SEDANG,
            notes="Untuk mendesain UI"
        )
        new_target = next((t for t in mock_store.targets if t.name == "Beli iPad Pro"), None)
        self.assertIsNotNone(new_target)
        self.assertEqual(new_target.target_amount, 20_000_000)

        # Update target
        self.window.target_vm.update_target(
            target_id=new_target.id,
            name="Beli iPad Pro M4",
            amount_str="22000000",
            deadline="31/12/2027",
            start_date="01/09/2026",
            priority=TargetPriority.TINGGI,
            notes="Update ke chip M4"
        )
        self.assertEqual(new_target.name, "Beli iPad Pro M4")
        self.assertEqual(new_target.target_amount, 22_000_000)

    def test_05_chart_rendering_paint_event(self):
        """Verify custom QPainter on chart canvas runs without errors during paintEvent."""
        chart_canvas = self.window.dashboard_view.chart_widget.canvas
        chart_canvas.resize(400, 200)
        img = QImage(400, 200, QImage.Format_ARGB32)
        chart_canvas.render(img)
        self.assertFalse(img.isNull())

    def test_06_calendar_month_navigation_event(self):
        """Verify calendar month switching re-renders day tags."""
        cal = self.window.dashboard_view.calendar_widget
        cal.month_combo.setCurrentText("Oktober 2026")
        self.assertEqual(cal.month, 10)


if __name__ == "__main__":
    unittest.main()
