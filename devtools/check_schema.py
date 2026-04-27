import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import engine
from sqlalchemy import inspect

def check_all_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Total tables: {len(tables)}")
    for table_name in tables:
        print(f"\nTable: {table_name}")
        try:
            columns = inspector.get_columns(table_name)
            for column in columns:
                print(f" - {column['name']}: {column['type']} (Nullable: {column['nullable']})")
        except Exception as e:
            print(f" Error: {e}")

if __name__ == "__main__":
    check_all_tables()
