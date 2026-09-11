"""
Main Window Shell.
Orchestrates the sidebar navigation, page switching inside QStackedWidget,
and global toast notifications.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QFrame
)
from PySide6.QtCore import Qt, Slot, QPoint
from PySide6.QtGui import QIcon

from src.core.constants import AppColors
from src.core.event_bus import event_bus
from src.views.styles import MAIN_STYLESHEET

# ViewModels
from src.viewmodels.dashboard_viewmodel import DashboardViewModel
from src.viewmodels.transaction_viewmodel import TransactionViewModel
from src.viewmodels.category_viewmodel import CategoryViewModel
from src.viewmodels.history_viewmodel import HistoryViewModel
from src.viewmodels.target_viewmodel import TargetViewModel

# Components & Pages
from src.views.components.sidebar import SidebarWidget
from src.views.components.toast import ToastWidget
from src.views.pages.dashboard_view import DashboardView
from src.views.pages.transaction_view import TransactionInputView
from src.views.pages.category_view import CategoryView
from src.views.pages.history_view import HistoryView
from src.views.pages.target_view import TargetView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keuangan Mandiri - Personal Finance Tracker (MVVM)")
        self.setMinimumSize(1150, 740)
        self.resize(1200, 780)

        self._init_viewmodels()
        self._setup_ui()
        self._bind_events()
        self.setStyleSheet(MAIN_STYLESHEET)

    def _init_viewmodels(self):
        self.dashboard_vm = DashboardViewModel(self)
        self.transaction_vm = TransactionViewModel(self)
        self.category_vm = CategoryViewModel(self)
        self.history_vm = HistoryViewModel(self)
        self.target_vm = TargetViewModel(self)

    def _setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = SidebarWidget(self)
        main_layout.addWidget(self.sidebar)

        # 2. Right Stacked Widget Pages
        self.pages_stack = QStackedWidget(self)
        self.pages_stack.setStyleSheet(f"background-color: {AppColors.BACKGROUND};")

        # Instantiate Views
        self.dashboard_view = DashboardView(self.dashboard_vm, self)
        self.transaction_view = TransactionInputView(self.transaction_vm, self)
        self.category_view = CategoryView(self.category_vm, self)
        self.history_view = HistoryView(self.history_vm, self)
        self.target_view = TargetView(self.target_vm, self)

        self.pages_stack.addWidget(self.dashboard_view)    # Index 0
        self.pages_stack.addWidget(self.transaction_view)  # Index 1
        self.pages_stack.addWidget(self.category_view)     # Index 2
        self.pages_stack.addWidget(self.history_view)      # Index 3
        self.pages_stack.addWidget(self.target_view)       # Index 4

        main_layout.addWidget(self.pages_stack, 1)

    def _bind_events(self):
        # Sidebar click -> switch stacked page
        self.sidebar.page_changed.connect(self.pages_stack.setCurrentIndex)

        # Global navigation request -> update sidebar and switch page
        event_bus.navigation_requested.connect(self.navigate_to_page)

        # Global toast notification trigger
        event_bus.toast_requested.connect(self.show_toast_notification)

    @Slot(int)
    def navigate_to_page(self, page_index: int):
        self.sidebar.select_page(page_index)
        self.pages_stack.setCurrentIndex(page_index)

    @Slot(str, str)
    def show_toast_notification(self, message: str, toast_type: str):
        """Spawns an animated overlay toast in the top right corner."""
        toast = ToastWidget(message, toast_type=toast_type, parent=self)
        
        # Position at top right
        margin_right = 24
        margin_top = 20
        pos_x = self.width() - toast.width() - margin_right
        pos_y = margin_top
        toast.move(pos_x, pos_y)
        toast.show_toast()

    def resizeEvent(self, event):
        super().resizeEvent(event)
