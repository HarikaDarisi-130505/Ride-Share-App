import sqlite3
import os

# Legacy SQLite maintenance script kept only for archive/reference.

# Database path
db_path = 'c:/rideapp/infrared-sojourner/backend/rideshare.db'

def clear_rides():
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Disable foreign key checks temporarily to allow deletion
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Delete from tables in order
        print("Cleaning up ride data...")
        cursor.execute("DELETE FROM chat_messages")
        cursor.execute("DELETE FROM ratings")
        cursor.execute("DELETE FROM bookings")
        cursor.execute("DELETE FROM ride_requests")
        cursor.execute("DELETE FROM rides")
        
        # Reset auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('rides', 'ride_requests', 'bookings', 'ratings', 'chat_messages')")

        conn.commit()
        print("✅ Successfully cleared all rides, requests, bookings, messages and ratings.")
        
        # Re-enable foreign key checks
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.close()

    except Exception as e:
        print(f"❌ Error clearing database: {str(e)}")

if __name__ == "__main__":
    clear_rides()
