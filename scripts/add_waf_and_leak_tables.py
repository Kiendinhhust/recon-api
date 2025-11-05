"""
One-off migration script to create new tables for:
- waf_detections
- leak_detections

Usage:
    python scripts/add_waf_and_leak_tables.py

It uses the same DATABASE_URL as the app (from .env via app.deps.Settings).
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.deps import engine, Base
from app.storage.models import WafDetection, LeakDetection
from sqlalchemy import inspect


def main():
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())

    to_create = []
    if WafDetection.__tablename__ not in existing:
        to_create.append(WafDetection.__table__)
        print(f"Will create table: {WafDetection.__tablename__}")
    else:
        print(f"Table already exists: {WafDetection.__tablename__}")
    
    if LeakDetection.__tablename__ not in existing:
        to_create.append(LeakDetection.__table__)
        print(f"Will create table: {LeakDetection.__tablename__}")
    else:
        print(f"Table already exists: {LeakDetection.__tablename__}")

    if not to_create:
        print("\nAll target tables already exist. Nothing to do.")
        return

    print(f"\nCreating {len(to_create)} table(s)...")
    Base.metadata.create_all(bind=engine, tables=to_create)
    print("✓ Migration completed successfully!")


if __name__ == "__main__":
    main()

