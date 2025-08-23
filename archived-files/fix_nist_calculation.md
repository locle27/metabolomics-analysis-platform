# NIST Calculation Issue Analysis

## 🔍 Most Likely Problems:

### 1. **Wrong Input Data Processing**
- The original system uses **pre-calculated ratios** from the "Ratio" sheet
- The new system is trying to calculate ratios from raw areas
- **Solution**: Use the uploaded data directly as ratios, don't calculate them

### 2. **Incorrect NIST Reference Usage**
- Original system uses specific NIST reference values from NIST_1-100 row
- New system might be using wrong NIST mapping
- **Solution**: Use exact NIST reference values from the reference row

### 3. **Sample-to-NIST Mapping Issue**
- Original uses complex mapping: PH-HC_1-25 → NIST (1), PH-HC_26-50 → NIST (2), etc.
- Database mapping might not match this logic
- **Solution**: Verify database sample mapping matches original logic

## 🔧 Quick Fix Steps:

1. **Verify uploaded data format**: Check if Book1.xlsx contains the same data as PH-HC_5601-5700 sheet
2. **Use ratios directly**: Don't calculate ratios from areas, use the values directly
3. **Fix NIST reference**: Use the correct NIST reference values for each sample group
4. **Test with known values**: Compare first compound calculation step by step

## 🎯 Expected Calculation:
```
NIST = Ratio / NIST_reference_value

Where:
- Ratio = Pre-calculated ratio from data (not area/ISTD)
- NIST_reference_value = Value from NIST_1-100 row for the correct NIST column
```