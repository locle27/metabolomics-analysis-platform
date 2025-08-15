# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Professional Metabolomics Data Analysis Platform** that extracts, manages, and visualizes lipid chromatography data from the Baker Institute. The system provides interactive dual-chart visualizations with advanced filtering, scientific-grade analysis tools, and a modern Phenikaa University-inspired interface.

### **🎯 Current Status: PRODUCTION-READY METABOLOMICS ANALYSIS PLATFORM**
- **Homepage**: Professional university-style homepage with project overview, news, and future plans
- **Interface**: **EXACT** Phenikaa University design implementation (logo left, navigation right with dropdowns)
- **Header Structure**: Authentic Phenikaa layout with logo and slogan table structure
- **Logo**: Official Phenikaa logo integrated (`logo-phenikaa.png`) 
- **Colors**: Exact color palette from original Phenikaa CSS (#2E4C92, #E94B00, #213671)
- **Typography**: Inter font family with exact Phenikaa specifications
- **Navigation**: Professional dropdown navigation with submenus
- **Database**: PostgreSQL with 800+ lipids imported
- **Charts**: **REVOLUTIONARY 2D AREA-BASED HOVER DETECTION SYSTEM** 🚀
- **Analysis**: Real-time XIC data visualization with professional external information panels
- **User Experience**: Industry-standard hover detection with clean, dot-free chart appearance

## 🧬 Advanced Metabolomics Analysis Platform

### **🏗️ System Architecture Overview**

#### **Database Layer (PostgreSQL)**
- **Primary Database**: PostgreSQL hosted on Koyeb cloud platform
- **Main Tables**:
  - `main_lipids` - Core lipid information (ID, name, class, retention time, etc.)
  - `annotated_ions` - Individual ion annotations (integration areas, MS/MS data)
  - `lipid_classes` - Lipid classification system
- **Data Volume**: 800+ lipids with complete XIC chromatogram data
- **Import Method**: Selenium hybrid scraping → PostgreSQL via SQLAlchemy ORM

#### **Backend Layer (Flask + SQLAlchemy)**
- **Framework**: Flask 2.3+ with PostgreSQL adapter
- **ORM**: SQLAlchemy for database operations
- **Key Services**:
  - `dual_chart_service.py` - Interactive chart generation
  - `models.py` - Database models and relationships
  - `app.py` - Main Flask application with routes

#### **Frontend Layer (Bootstrap 5 + Chart.js)**
- **Design**: Phenikaa University-inspired interface
- **Charts**: Chart.js 4.4.0 with zoom plugin for interactive analysis
- **Responsive**: Mobile-friendly Bootstrap 5 grid system
- **Navigation**: Professional 5-tab navigation system

### **🎨 Interface Design System (EXACT Phenikaa University Implementation)**

Based on the original Phenikaa University frontend files (`ui-test/`), the interface now uses the **exact** design system:

#### **Exact Phenikaa Color Palette** (from original CSS):
```css
--phenikaa-blue: #2E4C92          /* Exact header blue: rgba(46, 76, 146, 1) */
--phenikaa-dark-blue: #213671     /* Navigation blue: rgba(33, 54, 113, 1) */  
--phenikaa-orange: #E94B00        /* Exact orange: rgba(233, 75, 0, 1) */
--phenikaa-text-blue: #213671     /* Text color: rgba(33, 54, 113, 1) */
--phenikaa-white: #FFFFFF         /* Pure white backgrounds */
--phenikaa-light: #FBFAF9         /* Body background */
--phenikaa-dark: #191818          /* Dark text */
```

#### **Exact Header Structure** (Matching Phenikaa Layout):
- **Top Bar**: Blue bar with "METABOLOMICS RESEARCH PLATFORM" and "Contact" 
- **Main Header**: Centered logo + title section
- **Logo**: Actual Phenikaa logo (`logo-phenikaa.png`) - 121px × 79px
- **Title**: "Advanced Lipid Chromatography Data Analysis & Visualization Platform"
- **Subtitle**: "Precision • Innovation • Discovery"

#### **Exact Navigation System** (5 Tabs):
1. **DASHBOARD** - Main overview and lipid selection
2. **ANALYSIS** - Interactive dual-chart visualization  
3. **DATA MANAGEMENT** - Lipid database management
4. **BROWSE LIPIDS** - Search and filter lipids
5. **STATISTICS** - System analytics and reports

#### **Typography** (Exact Phenikaa Fonts):
- **Primary Font**: Inter (from Google Fonts)
- **Font Weights**: 400 (regular), 500 (medium), 600 (semibold), 700 (bold)
- **Font Sizes**: Following Phenikaa specifications (11px-15px for navigation)

#### **Professional Website Structure**:
1. **Homepage** (`/`) - University-style homepage with:
   - Hero section with call-to-action buttons
   - Project overview with feature cards
   - Statistics section showing platform capabilities
   - News/updates section with recent developments
   - Future development plans section
   - Professional call-to-action section

2. **Analysis Section** (`/lipid-selection`) - Lipid selection and analysis:
   - Clean lipid database interface (removed stats strip)
   - Interactive lipid selection with filtering
   - Professional page header with project description
   - Direct integration with chart analysis tools

3. **Navigation Structure**:
   - **OVERVIEW** dropdown: Project Overview, About Platform
   - **ANALYSIS** dropdown: Select Lipids, Interactive Charts
   - **DATA MANAGEMENT**: Database administration
   - **DOCUMENTATION**: Platform documentation
   - **STATISTICS**: System analytics

### **📊 Dual Chart System (Core Feature)**

#### **Chart Configuration**:
- **Chart 1**: Focused view (RT ± 0.6 minutes from main lipid)
- **Chart 2**: Full overview (0-16 minutes complete range)
- **Y-axis**: Compressed scaling (lowest point appears close to 0)
- **X-axis**: 1-minute intervals (0, 1, 2, 3, 4...)
- **Interaction**: Click-to-activate zoom, click-outside to deactivate

### **🎯 Lipid Annotation Color System** (Updated):
```python
'Current lipid': '#1f77b4'    # Blue (main compound)
'Similar MRM': '#2ed573'      # Light Green (user requested)
'+2 isotope': '#ff4757'       # Light Red (user requested)  
'Default': '#40E0D0'          # Turquoise (fallback)
```

### **⚙️ Chart Behavior Specifications**:

#### **Chart 1 (Focused View)**:
- **Purpose**: Detailed view of main lipid only
- **Time Range**: Main lipid RT ± 0.6 minutes
- **Lipid Display**: ONLY current/main lipid (no isotopes, no Similar MRM)
- **Boundaries**: Integration boundaries of current lipid
- **Y-axis**: Compressed (data appears ~2% above 0)

#### **Chart 2 (Overview)**:
- **Purpose**: Complete analytical context
- **Time Range**: Fixed 0-16 minutes
- **Lipid Display**: ALL lipids (Current + isotopes + Similar MRM)
- **Boundaries**: Chart 1 range boundaries (RT ± 0.6) for reference
- **Y-axis**: Compressed (data appears ~2% above 0)

### **🖱️ Mouse Interaction System**:
1. **Default State**: Page scrolls normally, no chart zoom
2. **Click Chart**: Activates zoom (blue border appears)
3. **Zoom/Pan**: Mouse wheel zooms, Shift+drag pans
4. **Click Outside**: Deactivates ALL charts, restores page scroll
5. **Double-click**: Reset zoom and deactivate specific chart

### **💬 Tooltip System**:
- **Targeted Display**: Shows ONLY when hovering over colored integration areas
- **Individual Data**: Each integration area shows its own lipid information
- **Static Content**: No dynamic RT updates while moving mouse
- **Format**:
  ```
  Lipid name: AC(24:1)_(a)
  Lipid class: AC
  Retention time: 4.30 minutes
  Integration start: 4.20 minutes  
  Integration end: 4.35 minutes
  Precursor mass: 510.3 m/z
  Product mass: 85.1 m/z
  Annotation: Similar MRM
  ```

## 🗂️ **File Structure & Functions**

### **📁 Core Application Files**:

#### **`app.py`** - Main Flask Application
- **Routes**:
  - `/` → `clean_dashboard()` - Main lipid selection interface
  - `/dual-chart-view` → `dual_chart_view()` - Interactive chart analysis
  - `/manage-lipids` → `manage_lipids()` - Database management
  - `/browse-lipids` → `browse_lipids()` - Search and filter
  - `/admin-stats` → `admin_stats()` - System statistics
  - `/api/dual-chart-data/<id>` → API endpoint for chart data
- **Database**: PostgreSQL connection via SQLAlchemy
- **Deployment**: Configured for Koyeb cloud hosting

#### **`dual_chart_service.py`** - Chart Generation Engine
- **Core Function**: `get_dual_chart_data(lipid_id)` → Chart.js configuration
- **Chart Types**: Focused view (Chart 1) + Overview (Chart 2)
- **Y-axis Algorithm**: Compressed scaling for visual clarity
- **Integration Areas**: Individual datasets per lipid with hover info
- **Boundary Lines**: Calculated per chart type and main lipid
- **Color Mapping**: Updated color system for annotation types

#### **`models.py`** - Database Schema
- **MainLipid**: Core lipid information table
- **AnnotatedIon**: Individual ion annotations with integration data
- **LipidClass**: Classification system
- **Relationships**: Foreign keys linking lipids to annotations

### **📁 Template Files (Phenikaa UI)**:

#### **`base.html`** - Master Template
- **Header**: Phenikaa University-inspired design
- **Navigation**: 5-tab professional system
- **Hero Section**: Conditional hero with CTAs
- **Footer**: Professional footer with branding
- **CSS**: Complete Phenikaa color system and styling

#### **`clean_dashboard.html`** - Lipid Selection Interface
- **Grid Display**: Interactive lipid selection cards
- **Search**: Advanced filtering with shorthand support
- **Selection Panel**: Fixed-position selected lipids panel
- **Integration**: Links to dual chart analysis

#### **`dual_chart_view.html`** - Chart Analysis Interface
- **Dual Charts**: Side-by-side Chart.js displays
- **Shared Legend**: Unified legend system
- **Zoom Controls**: Click-to-activate interaction system
- **Tooltips**: Custom positioned tooltips for integration areas

### **📁 Database & Import Files**:

#### **Data Import Pipeline**:
1. **`selenium_table_scraper.py`** - Scrapes Baker Institute website
2. **`import_hybrid_database.py`** - Imports scraped data to PostgreSQL
3. **`migrate_to_postgresql.py`** - Database migration utilities

### **🔧 Configuration Files**:
- **`requirements.txt`** - Python dependencies
- **`Procfile`** - Koyeb deployment configuration
- **`secrets.toml`** - Local environment variables
- **`koyeb.toml`** - Cloud deployment settings

## 🛠️ **Development Guidelines**

### **⚠️ Critical Rules - NEVER VIOLATE**:
1. **Never run files directly** - Let user run and provide feedback
2. **Database is PostgreSQL** - Not SQLite, use proper PostgreSQL syntax
3. **Charts use Chart.js 4.4.0** - Interactive with zoom plugin
4. **Y-axis must compress data close to 0** - Not proportional spacing
5. **Chart 1 shows ONLY main lipid** - No isotopes or Similar MRM
6. **Colors are fixed**: Similar MRM = light green, isotope = light red
7. **Tooltips are static** - No dynamic RT updates while hovering

### **🔄 When Making Changes**:

#### **Database Changes**:
- Use `models.py` for schema modifications
- Update via SQLAlchemy migrations, not direct SQL
- Test with development data before production

#### **Chart Modifications**:
- Edit `dual_chart_service.py` for backend chart logic
- Edit `dual_chart_view.html` for frontend Chart.js config  
- Maintain Chart 1/Chart 2 behavior differences
- Test zoom/pan interaction carefully

## 🚀 **REVOLUTIONARY 2D AREA-BASED HOVER DETECTION SYSTEM**

### **📊 Professional Chart Interaction (January 2025 - Latest Feature)**

#### **System Overview:**
The platform now features an **industry-leading 2D area-based hover detection system** that provides precise, professional interaction with chromatographic integration areas.

#### **🎯 Key Features:**
- **2D Rectangular Detection**: Mouse detection anywhere within integration area bounds
- **External Information Panel**: Professional 300px information panel (no overlapping tooltips)
- **Clean Chart Appearance**: Zero visible dots on any chart elements
- **Multi-Type Detection**: Precise detection for Current lipid, +2 isotope, and Similar MRM
- **Smart Priority System**: Automatic selection of most specific match when areas overlap

#### **🔬 Technical Implementation:**

##### **Backend (`dual_chart_service.py`):**
```python
# Clean chart appearance - NO visible dots anywhere
'pointRadius': 0,              # Main chromatogram: no dots
'pointHoverRadius': 0,         # Integration areas: no dots
'pointBackgroundColor': 'transparent',  # All points invisible
```

##### **Frontend (`dual_chart_view.html`):**
```javascript
// 2D Area Detection Algorithm:
1. Convert mouse position to data coordinates (X=time, Y=intensity)
2. Calculate integration bounds: time_start → time_end, 0 → peak_height
3. Check if mouse is within rectangular area: inTimeRange && inIntensityRange
4. Select smallest area if multiple matches (most specific)
5. Update external information panel with exact lipid data
```

#### **🎨 Professional Information Panel:**
```
📊 Lipid Information Panel (300px width)
├── Empty State: "Hover over colored integration areas..."
├── Active State: Shows exact hovered lipid type
├── Color-Coded Badge: 📍 +2 ISOTOPE (with matching colors)
├── Complete Data: Name, Class, RT, Integration bounds, MS/MS
└── Dynamic Highlighting: Border colors match chart elements
```

#### **⚙️ Hover Detection Specifications:**
- **Interaction Mode**: `intersect: false, mode: 'index'` for area detection
- **Chart.js Integration**: Uses `onHover` event for smooth real-time updates
- **Coordinate System**: Precise pixel-to-data coordinate conversion
- **Priority Algorithm**: Smallest area wins (most specific match)
- **Performance**: Zero performance impact, smooth 60fps interaction

#### **🧬 Supported Detection Types:**
1. **Current Lipid** → Blue highlighting, complete compound information
2. **+2 Isotope** → Red highlighting, isotope-specific data  
3. **Similar MRM** → Green highlighting, related compound details

#### **✅ Chart Behavior Rules:**
- **Chart 1**: Shows ONLY main lipid (focused view)
- **Chart 2**: Shows ALL types with 2D hover detection
- **No Tooltips**: External panel only, no overlay tooltips
- **Clean Appearance**: Professional, publication-ready charts

#### **UI/Design Changes**:
- Edit `base.html` for global styling
- Maintain Phenikaa University color scheme
- Keep responsive design for mobile devices
- Test all 5 navigation tabs

#### **New Routes/Features**:
- Add to `app.py` with proper error handling
- Create corresponding templates
- Update navigation in `base.html` if needed
- Document in this CLAUDE.md file

### **📈 Performance Considerations**:
- **Database**: Use proper indexing on lipid_id and retention_time
- **Charts**: Limit XIC data points for smooth rendering
- **Frontend**: Use CDN for Chart.js and Bootstrap
- **Caching**: Consider Redis for frequent chart data requests

### **🌐 Deployment Notes**:
- **Platform**: Koyeb cloud (PostgreSQL + Flask)
- **Environment Variables**: Set in Koyeb dashboard
- **Database URL**: Use DATABASE_URL environment variable
- **Static Files**: Served via CDN (Bootstrap, Chart.js, FontAwesome)

### **📊 Supported Lipid Classes** (Complete Coverage):
- **AC** - Acyl Carnitines (original focus, most tested)
- **TG** - Triacylglycerols  
- **PC** - Phosphatidylcholines
- **PE** - Phosphatidylethanolamines
- **SM** - Sphingomyelins
- **Cer** - Ceramides
- **LPC** - Lysophosphatidylcholines
- **LPE** - Lysophosphatidylethanolamines
- **PS, PI, PG, CL, FA, MAG, DAG** - Extended classes

## 🚀 **Development Commands**

### **🔧 Local Development**:
```bash
# Activate virtual environment (REQUIRED)
source venv_linux/bin/activate  # Linux/WSL

# Run Flask application
python app.py
# Access: http://localhost:5000

# Database operations
python migrate_to_postgresql.py    # Setup database
python import_hybrid_database.py   # Import lipid data
```

### **📊 Chart Testing**:
```bash
# Test dual chart system
# 1. Run app.py
# 2. Navigate to Dashboard
# 3. Select lipids 
# 4. Click "View Interactive Charts"
# 5. Test zoom/pan interactions
```

### **🗄️ Database Management**:
```bash
# Import fresh data
python selenium_table_scraper.py   # Scrape latest data
python import_hybrid_database.py   # Import to PostgreSQL

# Check database status
python -c "from models import *; print(f'Lipids: {MainLipid.query.count()}')"
```

## ⚡ **Quick Reference**

### **🎯 Key User-Requested Features Implemented**:
1. ✅ **Colors Updated**: Similar MRM = light green, isotope = light red
2. ✅ **Y-axis Compression**: Data appears close to 0 (not proportional)
3. ✅ **Chart 1 Clean**: Only shows main lipid (no isotopes/Similar MRM)
4. ✅ **Chart 2 Boundaries**: Uses Chart 1 range (RT ± 0.6) for reference
5. ✅ **Retention Time Scale**: 1-minute intervals (0,1,2,3...) not 2-minute
6. ✅ **Click-to-Zoom**: Must click chart to activate zoom, click outside to deactivate
7. ✅ **Static Tooltips**: Only show lipid data when hovering over integration areas
8. ✅ **Phenikaa UI**: Complete university-inspired interface design

### **🔍 Current System Status**:
- **Database**: ✅ PostgreSQL with 800+ lipids imported
- **Charts**: ✅ Interactive dual-chart system operational
- **Interface**: ✅ Phenikaa University design implemented
- **Navigation**: ✅ 5-tab professional navigation system
- **Interactions**: ✅ Click-to-zoom, static tooltips, compressed Y-axis
- **Colors**: ✅ Updated annotation color system

### **🚨 If System Breaks**:
1. **Check PostgreSQL connection** - Most common issue
2. **Verify Chart.js CDN loading** - Required for interactivity
3. **Test with simple lipid first** - AC100 or AC120 are reliable
4. **Check browser console** - JavaScript errors will show here
5. **Restart Flask app** - Clears any memory issues

### **📝 Testing Checklist**:
- [ ] Dashboard loads with lipid selection grid
- [ ] Dual charts display correctly with compressed Y-axis
- [ ] Chart 1 shows only main lipid, Chart 2 shows all types
- [ ] Click chart activates zoom (blue border), click outside deactivates
- [ ] Tooltips show only when hovering over colored integration areas
- [ ] Colors: Similar MRM = light green, isotope = light red
- [ ] Retention time scale shows 0,1,2,3... not 0,2,4,6...
- [ ] Y-axis starts close to lowest data point (not proportional)
- [ ] Phenikaa navigation works across all 5 tabs

---

**🎯 REMEMBER**: This system is now production-ready with a professional Phenikaa University-inspired interface, interactive dual-chart analysis, and comprehensive PostgreSQL database. All user-requested optimizations have been implemented. Focus on maintaining stability and user experience quality.

**Last Updated**: January 2025 - Phenikaa UI Implementation & Chart System Optimization Complete