"""
Local storage foundation for Keuangan Mandiri.

This package centralizes filesystem paths, configuration, caching, encryption,
backups, and attachment storage.  Modules are intentionally imported lazily by
their consumers so that importing the package never performs filesystem or
DPAPI side effects.
"""
