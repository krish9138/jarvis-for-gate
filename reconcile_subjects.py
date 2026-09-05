import sqlite3
from database.connection import get_db_connection

def reconcile():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Mapping of legacy names to refined canonical names
    legacy_map = {
        "Strength of Materials (SOM)": "Strength of Materials",
        "Engineering Thermodynamics": "Thermodynamics",
        "Fluid Mechanics & Hydraulics": "Fluid Mechanics",
        "Theory of Machines & Vibrations": "Theory of Machines",
        "Manufacturing & Material Science": "Manufacturing",
        "Industrial Engineering & Operations Research": "Industrial Engineering",
    }

    # 1. Update tasks & documents foreign keys to point to the canonical subject IDs
    for old_name, canonical_name in legacy_map.items():
        cursor.execute("SELECT id FROM subjects WHERE name = ?", (old_name,))
        old_row = cursor.fetchone()
        cursor.execute("SELECT id FROM subjects WHERE name = ?", (canonical_name,))
        new_row = cursor.fetchone()

        if old_row and new_row:
            old_id = old_row["id"]
            new_id = new_row["id"]

            cursor.execute("UPDATE tasks SET subject_id = ? WHERE subject_id = ?", (new_id, old_id))
            cursor.execute("UPDATE documents SET subject_id = ? WHERE subject_id = ?", (new_id, old_id))
            cursor.execute("UPDATE study_sessions SET subject_id = ? WHERE subject_id = ?", (new_id, old_id))
            cursor.execute("DELETE FROM subjects WHERE id = ?", (old_id,))

    # Keep General Aptitude if present under Foundation / Aptitude
    cursor.execute("UPDATE subjects SET category = 'GATE Mechanical' WHERE name = 'General Aptitude'")

    conn.commit()

    cursor.execute("SELECT id, name, category, target_hours FROM subjects ORDER BY category, name")
    rows = cursor.fetchall()
    print(f"Reconciliation complete! Total canonical subjects in DB: {len(rows)}")
    for r in rows:
        print(f"  [{r['category']}] {r['name']} ({r['target_hours']} hrs)")

    conn.close()

if __name__ == "__main__":
    reconcile()
