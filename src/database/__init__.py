"""
Database Layer Package for Keuangan Mandiri.
Implements local data persistence using SQLite 3.
"""
from src.database.db_manager import DatabaseManager, get_db

__all__ = ["DatabaseManager", "get_db"]
