"""Single import surface for Alembic autogenerate and metadata creation.

Importing this module registers every ORM model on ``Base.metadata``. Models are
added here as each phase introduces them.
"""
from app.db.base import Base  # noqa: F401

# Phase 1+ model modules are imported here so Base.metadata is complete.
# Example (added as models land):
#   from app.models import company, ticker, alias, article  # noqa: F401


def import_all_models() -> None:
    """Force-import every model module. Safe to call repeatedly."""
    import importlib
    import pkgutil

    import app.models as models_pkg

    for mod in pkgutil.iter_modules(models_pkg.__path__):
        if not mod.name.startswith("_"):
            importlib.import_module(f"app.models.{mod.name}")


import_all_models()
