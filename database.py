"""
Database Manager - v3.3
UPDATES:
- Added 'broker' field to deals table
- Added 'property_name' field to deals and development_projects
- Fixed unit_per_property calculation logic
- v3.3: Split region into metro + state (kept region for legacy)
"""

import sqlite3
from datetime import datetime
import csv

class DealDatabase:
    def __init__(self, db_path='senior_housing_deals.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with tables and new fields"""
        
        # Create deals table with new fields
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS deals (
                deal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_type TEXT,
                property_name TEXT,
                region TEXT,
                metro TEXT,
                state TEXT,
                seller TEXT,
                buyer TEXT,
                broker TEXT,
                transaction_date DATE,
                announcement_date DATE,
                article_date DATE,
                seller_rationale TEXT,
                buyer_rationale TEXT,
                post_deal_plan TEXT,
                price REAL,
                deal_terms TEXT,
                total_units INTEGER,
                units_per_property REAL,
                property_count INTEGER,
                property_type TEXT,
                year_built INTEGER,
                property_age INTEGER,
                financing_method TEXT,
                financing_details TEXT,
                borrower TEXT,
                lender TEXT,
                financing_purpose TEXT,
                loan_amount REAL,
                loan_terms TEXT,
                source_url TEXT UNIQUE,
                article_title TEXT,
                raw_article_text TEXT,
                extraction_confidence INTEGER,
                date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                operator TEXT,
                operator_change INTEGER DEFAULT 0
            )
        ''')
        
        # Add new columns if they don't exist (for existing databases)
        try:
            self.cursor.execute('ALTER TABLE deals ADD COLUMN broker TEXT')
            print("✓ Added 'broker' field to deals table")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            self.cursor.execute('ALTER TABLE deals ADD COLUMN property_name TEXT')
            print("✓ Added 'property_name' field to deals table")
        except sqlite3.OperationalError:
            pass
        
        # Create development_projects table with property_name
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS development_projects (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT,
                property_name TEXT,
                developer TEXT,
                general_contractor TEXT,
                architect TEXT,
                civil_engineer TEXT,
                landscape_architect TEXT,
                interior_designer TEXT,
                operator TEXT,
                operator_type TEXT,
                region TEXT,
                metro TEXT,
                state TEXT,
                building_type TEXT,
                unit_count INTEGER,
                building_size_sqft REAL,
                land_size_acres REAL,
                total_project_cost REAL,
                funding_method TEXT,
                funding_details TEXT,
                income_target TEXT,
                age_target TEXT,
                amenities TEXT,
                services_provided TEXT,
                announcement_date DATE,
                expected_completion_date DATE,
                project_status TEXT,
                article_date DATE,
                source_url TEXT UNIQUE,
                article_title TEXT,
                raw_article_text TEXT,
                extraction_confidence INTEGER,
                date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')
        
        # Add property_name to development_projects if doesn't exist
        try:
            self.cursor.execute('ALTER TABLE development_projects ADD COLUMN property_name TEXT')
            print("✓ Added 'property_name' field to development_projects table")
        except sqlite3.OperationalError:
            pass
        
        # v3.3: Add metro/state to both tables
        for table in ['deals', 'development_projects']:
            try:
                self.cursor.execute(f'ALTER TABLE {table} ADD COLUMN metro TEXT')
                print(f"✓ Added 'metro' field to {table} table")
            except sqlite3.OperationalError:
                pass
            try:
                self.cursor.execute(f'ALTER TABLE {table} ADD COLUMN state TEXT')
                print(f"✓ Added 'state' field to {table} table")
            except sqlite3.OperationalError:
                pass
        
        self.conn.commit()
        
        # Show database version
        stats = self.get_stats()
        print(f"✓ Database v3.3 ready: {self.db_path}")
        print(f"  - deals table (M&A): with broker and property_name fields")
        print(f"  - development_projects table: created")
    
    def _calculate_units_per_property(self, total_units, property_count):
        """
        Calculate units_per_property with proper logic
        If property_count is 1 or N/A, units_per_property = total_units / 1
        """
        # Handle N/A, None, 0
        if total_units in ['N/A', None, 0, '0']:
            return 'N/A'
        
        if property_count in ['N/A', None, 0, '0', 1, '1']:
            # Single property or unknown - units_per_property = total_units
            try:
                return float(total_units)
            except:
                return 'N/A'
        
        # Multiple properties - calculate average
        try:
            units = float(total_units)
            props = float(property_count)
            return round(units / props, 1)
        except:
            return 'N/A'
    
    def insert_deal(self, deal_data):
        """Insert M&A deal with broker and property_name fields"""
        
        # Calculate units_per_property with fixed logic
        total_units = deal_data.get('total_units', 'N/A')
        property_count = deal_data.get('property_count', 'N/A')
        units_per_property = self._calculate_units_per_property(total_units, property_count)
        
        try:
            self.cursor.execute('''
                INSERT INTO deals (
                    deal_type, property_name, region, metro, state, seller, buyer, broker,
                    transaction_date, announcement_date, article_date,
                    seller_rationale, buyer_rationale, post_deal_plan,
                    price, deal_terms, total_units, units_per_property, property_count,
                    property_type, year_built, property_age,
                    financing_method, financing_details,
                    borrower, lender, financing_purpose, loan_amount, loan_terms,
                    source_url, article_title, raw_article_text,
                    extraction_confidence, operator, operator_change
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                deal_data.get('deal_type', 'N/A'),
                deal_data.get('property_name', 'N/A'),
                deal_data.get('region', 'N/A'),
                deal_data.get('metro', 'N/A'),
                deal_data.get('state', 'N/A'),
                deal_data.get('seller', 'N/A'),
                deal_data.get('buyer', 'N/A'),
                deal_data.get('broker', 'N/A'),
                deal_data.get('transaction_date', 'N/A'),
                deal_data.get('announcement_date', 'N/A'),
                deal_data.get('article_date', 'N/A'),
                deal_data.get('seller_rationale', 'N/A'),
                deal_data.get('buyer_rationale', 'N/A'),
                deal_data.get('post_deal_plan', 'N/A'),
                deal_data.get('price', 'N/A'),
                deal_data.get('deal_terms', 'N/A'),
                total_units,
                units_per_property,
                property_count,
                deal_data.get('property_type', 'N/A'),
                deal_data.get('year_built', 'N/A'),
                deal_data.get('property_age', 'N/A'),
                deal_data.get('financing_method', 'N/A'),
                deal_data.get('financing_details', 'N/A'),
                deal_data.get('borrower', 'N/A'),
                deal_data.get('lender', 'N/A'),
                deal_data.get('financing_purpose', 'N/A'),
                deal_data.get('loan_amount', 'N/A'),
                deal_data.get('loan_terms', 'N/A'),
                deal_data.get('source_url', ''),
                deal_data.get('article_title', 'N/A'),
                deal_data.get('raw_article_text', 'N/A'),
                deal_data.get('extraction_confidence', 3),
                deal_data.get('operator', 'N/A'),
                deal_data.get('operator_change', 0)
            ))
            
            self.conn.commit()
            return True
            
        except sqlite3.IntegrityError:
            # URL already exists
            return False
    
    def insert_development_project(self, project_data):
        """Insert development project with property_name"""
        try:
            self.cursor.execute('''
                INSERT INTO development_projects (
                    project_name, property_name, developer, general_contractor, architect,
                    civil_engineer, landscape_architect, interior_designer,
                    operator, operator_type, region, metro, state, building_type,
                    unit_count, building_size_sqft, land_size_acres,
                    total_project_cost, funding_method, funding_details,
                    income_target, age_target, amenities, services_provided,
                    announcement_date, expected_completion_date, project_status,
                    article_date, source_url, article_title, raw_article_text,
                    extraction_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_data.get('project_name', 'N/A'),
                project_data.get('property_name', project_data.get('project_name', 'N/A')),  # Default to project_name
                project_data.get('developer', 'N/A'),
                project_data.get('general_contractor', 'N/A'),
                project_data.get('architect', 'N/A'),
                project_data.get('civil_engineer', 'N/A'),
                project_data.get('landscape_architect', 'N/A'),
                project_data.get('interior_designer', 'N/A'),
                project_data.get('operator', 'N/A'),
                project_data.get('operator_type', 'N/A'),
                project_data.get('region', 'N/A'),
                project_data.get('metro', 'N/A'),
                project_data.get('state', 'N/A'),
                project_data.get('building_type', 'N/A'),
                project_data.get('unit_count', 'N/A'),
                project_data.get('building_size_sqft', 'N/A'),
                project_data.get('land_size_acres', 'N/A'),
                project_data.get('total_project_cost', 'N/A'),
                project_data.get('funding_method', 'N/A'),
                project_data.get('funding_details', 'N/A'),
                project_data.get('income_target', 'N/A'),
                project_data.get('age_target', 'N/A'),
                project_data.get('amenities', 'N/A'),
                project_data.get('services_provided', 'N/A'),
                project_data.get('announcement_date', 'N/A'),
                project_data.get('expected_completion_date', 'N/A'),
                project_data.get('project_status', 'N/A'),
                project_data.get('article_date', 'N/A'),
                project_data.get('source_url', ''),
                project_data.get('article_title', 'N/A'),
                project_data.get('raw_article_text', 'N/A'),
                project_data.get('extraction_confidence', 3)
            ))
            
            self.conn.commit()
            return True
            
        except sqlite3.IntegrityError:
            return False
    
    def url_exists(self, url):
        """Check if URL exists in either table"""
        self.cursor.execute('SELECT 1 FROM deals WHERE source_url = ?', (url,))
        if self.cursor.fetchone():
            return True
        
        self.cursor.execute('SELECT 1 FROM development_projects WHERE source_url = ?', (url,))
        return self.cursor.fetchone() is not None
    
    def get_stats(self):
        """Get comprehensive statistics"""
        # M&A stats
        self.cursor.execute('''
            SELECT 
                COUNT(*) as total_deals,
                COUNT(CASE WHEN deal_type = 'Acquisition' THEN 1 END) as acquisitions,
                COUNT(CASE WHEN deal_type = 'Financing' THEN 1 END) as financings,
                COUNT(CASE WHEN price != 'N/A' AND price > 0 THEN 1 END) as deals_with_price,
                SUM(CASE WHEN price != 'N/A' AND price > 0 THEN price ELSE 0 END) / 1000000.0 as total_value_millions,
                SUM(CASE WHEN total_units != 'N/A' AND total_units > 0 THEN total_units ELSE 0 END) as total_units,
                SUM(CASE WHEN property_count != 'N/A' AND property_count > 0 THEN property_count ELSE 0 END) as total_properties
            FROM deals
        ''')
        
        ma_stats = self.cursor.fetchone()
        
        # Development stats
        self.cursor.execute('''
            SELECT
                COUNT(*) as total_projects,
                SUM(CASE WHEN total_project_cost != 'N/A' AND total_project_cost > 0 THEN total_project_cost ELSE 0 END) / 1000000.0 as total_value_millions,
                SUM(CASE WHEN unit_count != 'N/A' AND unit_count > 0 THEN unit_count ELSE 0 END) as total_units
            FROM development_projects
        ''')
        
        dev_stats = self.cursor.fetchone()
        
        return {
            'ma_deals': ma_stats[0] or 0,
            'acquisitions': ma_stats[1] or 0,
            'financings': ma_stats[2] or 0,
            'deals_with_price': ma_stats[3] or 0,
            'ma_value_millions': round(ma_stats[4] or 0, 1),
            'ma_units': int(ma_stats[5] or 0),
            'ma_properties': int(ma_stats[6] or 0),
            'dev_projects': dev_stats[0] or 0,
            'dev_value_millions': round(dev_stats[1] or 0, 1),
            'dev_units': int(dev_stats[2] or 0),
            'total_records': (ma_stats[0] or 0) + (dev_stats[0] or 0),
            'combined_value_millions': round((ma_stats[4] or 0) + (dev_stats[1] or 0), 1),
            'combined_units': int((ma_stats[5] or 0) + (dev_stats[2] or 0))
        }
    
    def get_all_deals(self):
        """Get all M&A deals"""
        self.cursor.execute('SELECT * FROM deals ORDER BY deal_id DESC')
        return self.cursor.fetchall()
    
    def get_all_development_projects(self):
        """Get all development projects"""
        self.cursor.execute('SELECT * FROM development_projects ORDER BY project_id DESC')
        return self.cursor.fetchall()
    
    def export_to_csv(self, table='both'):
        """Export data to CSV files"""
        if table in ['deals', 'both']:
            deals = self.get_all_deals()
            if deals:
                # Get column names
                self.cursor.execute('PRAGMA table_info(deals)')
                columns = [col[1] for col in self.cursor.fetchall()]
                
                with open('ma_deals_export.csv', 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(deals)
                print(f"✓ Exported {len(deals)} M&A deals to ma_deals_export.csv")
        
        if table in ['development', 'both']:
            projects = self.get_all_development_projects()
            if projects:
                self.cursor.execute('PRAGMA table_info(development_projects)')
                columns = [col[1] for col in self.cursor.fetchall()]
                
                with open('development_projects_export.csv', 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(projects)
                print(f"✓ Exported {len(projects)} development projects to development_projects_export.csv")
    
    def __del__(self):
        """Close database connection"""
        try:
            self.conn.close()
        except:
            pass

if __name__ == "__main__":
    # Test database
    db = DealDatabase()
    stats = db.get_stats()
    print("\nDatabase Statistics:")
    print(f"  M&A Deals: {stats['ma_deals']}")
    print(f"  Development Projects: {stats['dev_projects']}")
    print(f"  Total Records: {stats['total_records']}")
