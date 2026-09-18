"""
Automated Verification Test for MVVM Architecture and Event-Driven Mechanics.
Tests PySide6 Signals, Slots, Lifecycle Hooks, Form Formatting, and Cross-ViewModel EventBus.
"""
import os
import sys
import unittest

# Run headless Qt without display
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from src.core.constants import TransactionType, TargetPriority
from src.core.event_bus import event_bus
from src.core.mock_data import mock_store
from src.viewmodels.dashboard_viewmodel import DashboardViewModel
from src.viewmodels.transaction_viewmodel import TransactionViewModel
from src.viewmodels.category_viewmodel import CategoryViewModel
from src.viewmodels.history_viewmodel import HistoryViewModel
from src.viewmodels.target_viewmodel import TargetViewModel
from src.views.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)

class TestEventDrivenMVVM(unittest.TestCase):
    def setUp(self):
        self.dashboard_vm = DashboardViewModel()
        self.tx_vm = TransactionViewModel()
        self.cat_vm = CategoryViewModel()
        self.hist_vm = HistoryViewModel()
        self.target_vm = TargetViewModel()

    def test_01_event_bus_toast_emission(self):
        """Test global toast signal emission and reception."""
        received = []
        def on_toast(msg, t_type):
            received.append((msg, t_type))

        event_bus.toast_requested.connect(on_toast)
        event_bus.toast_requested.emit("Tes Notifikasi", "success")
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], ("Tes Notifikasi", "success"))

    def test_02_transaction_live_input_formatting(self):
        """Test textChanged event formatting to Rupiah."""
        formatted_results = []
        self.tx_vm.formatted_amount_changed.connect(formatted_results.append)

        # Trigger live input event
        self.tx_vm.on_amount_text_changed("1500000")
        self.assertIn("Rp 1.500.000", formatted_results)

    def test_03_transaction_character_counter(self):
        """Test character counter signal on notes change."""
        counter_results = []
        self.tx_vm.character_count_changed.connect(lambda c, m: counter_results.append((c, m)))

        self.tx_vm.on_notes_text_changed("Membeli perlengkapan")
        self.assertEqual(counter_results[-1], (20, 100))

    def test_04_cross_viewmodel_event_propagation(self):
        """Test submitting a transaction updates Dashboard and History via data_changed signal."""
        initial_balance = mock_store.get_current_balance()
        initial_pemasukan = mock_store.get_total_pemasukan()

        dashboard_updates = []
        self.dashboard_vm.summary_updated.connect(dashboard_updates.append)

        # Save new income transaction
        self.tx_vm.save_transaction(
            tx_type=TransactionType.PEMASUKAN,
            raw_amount="500000",
            category="Bonus Gaji",
            tx_date="11/09/2026",
            notes="Bonus proyek visual"
        )

        # Verify mock store updated
        new_pemasukan = mock_store.get_total_pemasukan()
        self.assertEqual(new_pemasukan, initial_pemasukan + 500_000)

        # Refresh dashboard and verify signal emitted
        self.dashboard_vm.refresh()
        self.assertTrue(len(dashboard_updates) > 0)
        self.assertIn("Rp", dashboard_updates[-1]["total_pemasukan"])

    def test_05_category_tab_events(self):
        """Test category switching between Pengeluaran and Pemasukan."""
        results = []
        self.cat_vm.categories_updated.connect(lambda cats, tab: results.append((tab, len(cats))))

        self.cat_vm.set_active_tab(TransactionType.PEMASUKAN)
        self.assertEqual(results[-1][0], TransactionType.PEMASUKAN)
        self.assertTrue(results[-1][1] > 0)

        self.cat_vm.set_active_tab(TransactionType.PENGELUARAN)
        self.assertEqual(results[-1][0], TransactionType.PENGELUARAN)

    def test_06_target_isi_target_allocation_event(self):
        """Test depositing funds into a target updates target collected amount."""
        target_id = "t1" # Beli PC
        initial_collected = next(t.collected_amount for t in mock_store.targets if t.id == target_id)

        self.target_vm.deposit_funds(target_id, "500000", "Nabung tambahan")
        updated_collected = next(t.collected_amount for t in mock_store.targets if t.id == target_id)
        self.assertEqual(updated_collected, initial_collected + 500_000)

    def test_07_main_window_instantiation_and_lifecycle(self):
        """Test full MainWindow creation, widget hierarchy, and page switching."""
        window = MainWindow()
        self.assertEqual(window.pages_stack.count(), 5)
        
        # Test navigation signal
        window.navigate_to_page(1)
        self.assertEqual(window.pages_stack.currentIndex(), 1)
        
        window.navigate_to_page(0)
        self.assertEqual(window.pages_stack.currentIndex(), 0)

        # Test toast display
        window.show_toast_notification("Uji Toast", "info")


if __name__ == "__main__":
    unittest.main()
