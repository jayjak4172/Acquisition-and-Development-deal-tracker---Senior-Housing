"""
Export deals from database to CSV/Excel
"""

from database import DealDatabase
import os

def export_to_excel():
    """Export deals to CSV and open in Excel"""
    db = DealDatabase()
    
    # Export to CSV
    filename = "deals_export.csv"
    db.export_to_csv(filename)
    
    # Try to open in Excel
    try:
        if os.name == 'nt':  # Windows
            os.startfile(filename)
        else:  # Mac/Linux
            import subprocess
            subprocess.call(['open', filename])
    except:
        print(f"Could not auto-open. Please open manually: {filename}")

if __name__ == "__main__":
    export_to_excel()
