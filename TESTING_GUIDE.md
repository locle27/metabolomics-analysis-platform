# 🧪 Testing Guide for New Features

## ✅ Features Implemented

### 1. **Railway HTTPS Fix (ProxyFix)**
- **What**: Added `ProxyFix` middleware to handle HTTPS behind Railway proxy
- **File**: `app.py` - Lines 9, 53-54
- **Test**: Login with Appwrite should work on Railway without "Invalid URI" errors

### 2. **Detailed Lipid Information Display**
- **What**: Replaced chart legend with comprehensive lipid data when "Show Details" is clicked
- **File**: `templates/dual_chart_view.html` - Lines 365-380, 818-906  
- **Test**: Click "Show Details" button → Should show detailed lipid info instead of simple legend

### 3. **Admin Zoom Settings Feature**
- **What**: Admin can set default zoom range for all users' charts
- **Files**: 
  - Database model: `models_postgresql_optimized.py` - Lines 475-562
  - Routes: `app.py` - Lines 879-939
  - Template: `templates/admin_zoom_settings.html` (new file)
  - Navigation: `templates/base.html` - Line 626
- **Test**: 
  1. Login as admin
  2. Go to Management → Chart Zoom Settings
  3. Set custom range (e.g., 5.0 - 12.0 minutes)
  4. Save settings
  5. View any chart → Chart 2 should auto-zoom to that range with orange border

### 4. **Auto-Apply Admin Zoom**
- **What**: All Chart 2 instances automatically zoom to admin-configured range
- **File**: `templates/dual_chart_view.html` - Lines 472-500, 1044-1135
- **Test**: After admin sets zoom range, all new chart views should automatically zoom
- **Visual Indicators**:
  - Orange top and left borders on Chart 2
  - Orange badge showing zoom range
  - Zoom persists after any reset operations

### 5. **Schedule Form Fix**
- **What**: Added missing `schedule_form.html` template to fix Railway deployment
- **File**: `templates/schedule_form.html` (new file)
- **Test**: Schedule navigation should work without errors

## 🧪 Step-by-Step Testing

### Local Testing:
```bash
# 1. Install any missing dependencies
pip install appwrite werkzeug

# 2. Run the app
python app.py

# 3. Open browser to http://localhost:5000
```

### Test Sequence:

1. **Homepage** → Should load without errors
2. **Login** → Test demo login works
3. **Analysis** → Select a lipid and view charts
4. **Admin Settings** → Management → Chart Zoom Settings
5. **Set Zoom** → Try 8.0 - 12.0 minutes, save
6. **Test Auto-Zoom** → Go back to charts, Chart 2 should auto-zoom with orange borders
7. **Test Reset** → Reset zoom (R key or double-click) → Should reapply admin zoom
8. **Detailed Info** → Click "Show Details" → Should show comprehensive lipid data
9. **Schedule** → Schedule menu should work without errors

## 🎯 Expected Results

### Admin Zoom Working:
- Chart 2 has orange borders (top and left)
- Orange badge shows "Admin Zoom: X.X-X.Xmin"
- Chart automatically zooms to configured range
- Zoom persists through all reset operations
- Console shows: "🎯 Applying admin zoom to [lipid]: X.XX - X.XX minutes"

### Detailed Info Working:
- Click "Show Details" shows comprehensive lipid data in grid format
- Data includes: Code, Name, Class, Precursor/Product ions, Retention time, etc.
- No more simple chart legend

### Railway Deployment Working:
- Appwrite login works without "Invalid URI" errors
- All templates load correctly
- HTTPS redirect URLs work properly

## 🚨 Troubleshooting

### If Admin Zoom Not Working:
1. Check browser console for errors
2. Verify admin settings saved: `/api/zoom-settings`
3. Check Chart.js zoom plugin loaded
4. Ensure admin set non-default values (not 0.0-16.0)

### If ProxyFix Not Working:
1. Check Railway logs for errors
2. Verify `werkzeug` version supports `ProxyFix`
3. Test locally first to isolate Railway issues

### If Templates Missing:
1. Check all templates committed to git
2. Run `git status` to see untracked files
3. Push all changes before Railway deployment

## 📝 Changes Summary

**Files Modified:**
- `app.py` - Added ProxyFix, AdminSettings routes, imports
- `models_postgresql_optimized.py` - Added AdminSettings model
- `templates/dual_chart_view.html` - Detailed info display, auto-zoom functionality
- `templates/base.html` - Added zoom settings to admin menu

**Files Created:**
- `templates/admin_zoom_settings.html` - Admin interface for zoom configuration
- `test_setup.py` - Quick validation script
- `TESTING_GUIDE.md` - This testing guide

**Ready for Deployment!** 🚀