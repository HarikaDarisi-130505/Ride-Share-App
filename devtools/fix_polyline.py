import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.database import engine
from sqlalchemy import text

def fix_polyline_long():
    with engine.connect() as conn:
        print("Increasing route_polyline column size to LONGTEXT...")
        try:
            # LONGTEXT in MySQL can hold up to 4GB
            conn.execute(text("ALTER TABLE rides MODIFY route_polyline LONGTEXT"))
            conn.commit()
            print("Successfully updated route_polyline to LONGTEXT.")
        except Exception as e:
            print(f"Error updating column: {e}")

if __name__ == "__main__":
    fix_polyline_long()
