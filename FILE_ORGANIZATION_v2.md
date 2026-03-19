# FILE ORGANIZATION GUIDE - v2.0

## 📁 ACTIVE FILES (Keep in main folder)

Copy these exact files to your ma_tracker folder:

### **Core System Files:**
```
config.py                          ← Your existing config (no version)
database_v2.py                     ← New database with property_type & age
entity_mapping_v1.py               ← Entity normalization mappings
scraper_v2.py                      ← Main scraper (enhanced)
check_duplicates_v1.py             ← Check for entity duplicates
view_stats_v2.py                   ← View enhanced statistics
export_data_v1.py                  ← Export to CSV/Excel
```

### **Data Files:**
```
urls.txt                           ← Your article URLs
cookies.pkl                        ← Login cookies (auto-generated)
senior_housing_deals.db            ← Active database
```

### **Documentation:**
```
README.md                          ← Project documentation
PROPERTY_TYPE_GUIDE.md             ← Reference for property types
```

**Total: 12 files**

---

## 📦 ARCHIVE FILES (Move to backup folder)

**Move these to:** `C:\Users\kimja\Documents\ma_tracker\backup\`

### **Old Versions (v1.0):**
```
database.py                        ← Old database (no property_type)
database_improved.py               ← Intermediate version
cookie_auto_login.py               ← Old name for scraper
cookie_auto_login_improved.py      ← Intermediate version
week1_scraper.py                   ← Old name (basic)
week1_scraper_enhanced.py          ← Old name (enhanced)
view_stats.py                      ← Old stats (basic)
view_stats_enhanced.py             ← Old name
simple_scraper.py                  ← Very old single URL scraper
browser_scraper.py                 ← Old Selenium version
```

### **Old Planning Docs:**
```
ACTION_PLAN.md                     ← Superseded by SETUP_GUIDE_v2.md
4_WEEK_ROADMAP.md                  ← Keep if you want reference
UPDATED_ACTION_PLAN.md             ← Old version
```

### **Old Backups:**
```
senior_housing_deals_backup.db     ← Old database backups
backup_before_enhancement.db       ← Old database backups
*.db (any other .db files)         ← Old database backups
```

---

## 🔄 FILE RENAMING MAP

**If you have these files, rename them:**

| Old Name | New Name (v2.0) |
|----------|-----------------|
| `week1_scraper_enhanced.py` | `scraper_v2.py` |
| `view_stats_enhanced.py` | `view_stats_v2.py` |
| `check_duplicates.py` | `check_duplicates_v1.py` |
| `export_data.py` | `export_data_v1.py` |
| `entity_mapping.py` | `entity_mapping_v1.py` |

---

## ⚙️ STEP-BY-STEP CLEANUP

### **Step 1: Create backup folder**

```bash
cd C:\Users\kimja\Documents\ma_tracker
mkdir backup_v1
```

### **Step 2: Move old files to backup**

```bash
# Move old database versions
move database.py backup_v1\
move database_improved.py backup_v1\

# Move old scraper versions
move cookie_auto_login.py backup_v1\
move cookie_auto_login_improved.py backup_v1\
move week1_scraper.py backup_v1\
move simple_scraper.py backup_v1\
move browser_scraper.py backup_v1\

# Move old stats versions
move view_stats.py backup_v1\

# Move old planning docs (optional - keep if you want)
move ACTION_PLAN.md backup_v1\
move UPDATED_ACTION_PLAN.md backup_v1\

# Move old database backups
move *.db backup_v1\
# But keep the main one:
move backup_v1\senior_housing_deals.db .\
```

### **Step 3: Rename new files to v2 naming**

```bash
# Rename to standard naming
ren week1_scraper_enhanced.py scraper_v2.py
ren view_stats_enhanced.py view_stats_v2.py
ren check_duplicates.py check_duplicates_v1.py
ren export_data.py export_data_v1.py
ren entity_mapping.py entity_mapping_v1.py
```

### **Step 4: Verify your folder**

```bash
dir *.py
```

**You should see:**
```
config.py
database_v2.py
entity_mapping_v1.py
scraper_v2.py
check_duplicates_v1.py
view_stats_v2.py
export_data_v1.py
```

---

## 📋 FINAL FOLDER STRUCTURE

```
C:\Users\kimja\Documents\ma_tracker\
│
├── backup_v1\                     ← All old files here
│   ├── database.py
│   ├── cookie_auto_login.py
│   ├── view_stats.py
│   └── ... (all old versions)
│
├── config.py                      ← Active files below
├── database_v2.py
├── entity_mapping_v1.py
├── scraper_v2.py
├── check_duplicates_v1.py
├── view_stats_v2.py
├── export_data_v1.py
│
├── urls.txt
├── cookies.pkl
├── senior_housing_deals.db
│
├── README.md
├── PROPERTY_TYPE_GUIDE.md
└── SETUP_GUIDE_v2.md
```

---

## 🚀 UPDATED WORKFLOW (v2.0)

### **Daily Workflow:**

```bash
# 1. Add URLs
notepad urls.txt

# 2. Run scraper (v2 - with property type & age)
python scraper_v2.py

# 3. View stats (v2 - enhanced display)
python view_stats_v2.py

# 4. Check duplicates
python check_duplicates_v1.py

# 5. Export
python export_data_v1.py
```

### **Commands Reference:**

| Task | Command |
|------|---------|
| Process URLs | `python scraper_v2.py` |
| View stats | `python view_stats_v2.py` |
| Check duplicates | `python check_duplicates_v1.py` |
| Export to Excel | `python export_data_v1.py` |
| Reset database | `del senior_housing_deals.db` then `python database_v2.py` |

---

## 📝 VERSION NOTES

### **v2.0 (Current) - Enhanced Extraction**

**New Features:**
- ✅ Property type extraction (AL, MC, IL, CCRC, AA, SNF, Mixed)
- ✅ Year built extraction
- ✅ Property age calculation (announcement_year - year_built)
- ✅ Fallback: announcement_date > article_date > current_year
- ✅ Enhanced stats display
- ✅ Property type breakdown
- ✅ Age distribution analysis

**Database Schema:**
- Added: `property_type` (TEXT)
- Added: `year_built` (INTEGER)
- Added: `property_age` (INTEGER)

### **v1.0 (Archived) - Basic Version**

**Features:**
- Basic scraping
- GPT extraction
- Simple database
- No property type
- No age tracking

---

## ✅ CHECKLIST

After cleanup, verify:

- [ ] 7 .py files in main folder (all with version numbers)
- [ ] All old files in backup_v1 folder
- [ ] urls.txt in main folder
- [ ] senior_housing_deals.db in main folder
- [ ] cookies.pkl in main folder (or will be created on first run)
- [ ] Commands work: `python scraper_v2.py`, `python view_stats_v2.py`

---

## 🔮 FUTURE VERSIONS

**v3.0 (Week 2) - Multi-Source:**
- Add Seniors Housing Business scraper
- Source tracking
- Enhanced entity resolution

**v4.0 (Week 3) - Analytics:**
- Google Sheets integration
- Visualizations
- Automated insights

**v5.0 (Week 4) - Production:**
- Web dashboard
- API endpoints
- Scheduled automation

---

**Clean folder = Clean mind = Better development!** 🧹✨
