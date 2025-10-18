# Format Selection Debugging Guide

## 🔍 How to Debug Format Selection Issues

### Step 1: Open Browser Developer Tools
1. Visit: https://www.httpsphenikaa-lipidomics-analysis.xyz/streamlined-calculator
2. Press `F12` or `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac)
3. Click on the **Console** tab

### Step 2: Check Console Messages

You should see these messages in order:

```
✅ EXPECTED SEQUENCE:
1. 🔵 Streamlined Calculator Script Loading...
2. 🎯 DOM LOADED: Initializing format selection cards...
3. Found 2 format cards: NodeList(2) [div.format-card.format-1, div.format-card.format-2]
4.   Card 0: data-format="1", classes="format-card format-1"
5.   Card 1: data-format="2", classes="format-card format-2"
6. ✅ Format cards initialized successfully
```

### Step 3: Test Format Selection

1. Click on **FORMAT 1** card
2. You should see in console:
   ```
   🖱️ CLICK EVENT: Format card 1 clicked
   📋 Selected format: 1
   ✅ Format 1 upload section displayed
   ```

3. Click on **FORMAT 2** card
4. You should see in console:
   ```
   🖱️ CLICK EVENT: Format card 2 clicked
   📋 Selected format: 2
   ✅ Format 2 upload section displayed
   ```

### Step 4: Visual Confirmation

After clicking a format card:
- ✅ The card should have a colored border (blue for Format 1, green for Format 2)
- ✅ The card should have a gradient background
- ✅ The upload section below should appear
- ✅ Page should smoothly scroll to the upload section

## ❌ Common Issues and Solutions

### Issue 1: "No .format-card elements found!"

**Error Message:**
```
❌ ERROR: No .format-card elements found!
```

**Cause:** CSS or HTML rendering issue
**Solution:**
1. Check if format cards are visible on page
2. Inspect HTML: Right-click on page → Inspect
3. Search for `format-card` in Elements tab
4. If not found → template rendering issue

### Issue 2: Cards visible but no click events

**Symptoms:**
- Format cards appear on page
- Clicking does nothing
- No "🖱️ CLICK EVENT" in console

**Cause:** Event listeners not attached
**Solution:**
1. Check if "✅ Format cards initialized successfully" appears
2. If not → DOM loaded before script
3. Hard refresh page: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
4. Clear browser cache

### Issue 3: HTTP/2 Protocol Error

**Error in Network tab:**
```
Failed to load resource: net::ERR_HTTP2_PROTOCOL_ERROR
```

**Possible Causes:**
1. Production server issue (Railway/Koyeb)
2. Large file upload attempt
3. Connection timeout
4. SSL/TLS handshake failure

**Solutions:**
1. **Clear Browser Cache:**
   - Chrome: Settings → Privacy → Clear browsing data
   - Select "Cached images and files"
   - Click "Clear data"

2. **Hard Refresh:**
   - `Ctrl+Shift+R` (Windows/Linux)
   - `Cmd+Shift+R` (Mac)

3. **Try Incognito/Private Mode:**
   - Chrome: `Ctrl+Shift+N`
   - Firefox: `Ctrl+Shift+P`

4. **Check Production Logs:**
   - Railway: Dashboard → Logs tab
   - Look for server errors

5. **Verify Server Status:**
   - Check if server is running
   - Ping the URL: `curl https://www.httpsphenikaa-lipidomics-analysis.xyz/health`

### Issue 4: Script loads but selectFormat not defined

**Error:**
```
Uncaught ReferenceError: selectFormat is not defined
```

**Cause:** Inline `onclick` attributes instead of event listeners
**Solution:**
- This should be fixed in latest commit
- Verify HTML has `data-format="1"` NOT `onclick="selectFormat(1)"`
- Check git commit: `8f2236c`

## 🔧 Manual Testing Checklist

- [ ] Page loads without JavaScript errors
- [ ] Console shows "🔵 Streamlined Calculator Script Loading..."
- [ ] Console shows "Found 2 format cards"
- [ ] Both format cards are visible
- [ ] Clicking Format 1 shows click event in console
- [ ] Clicking Format 1 displays upload section
- [ ] Clicking Format 2 shows click event in console
- [ ] Clicking Format 2 displays upload section
- [ ] Upload sections toggle correctly (only one visible at a time)
- [ ] Page scrolls smoothly to upload section
- [ ] Format cards have hover effects
- [ ] Selected card has highlighted border

## 📊 Performance Testing

### Check Page Load Time
1. Open DevTools → Network tab
2. Refresh page (`F5`)
3. Look at total load time (bottom of Network tab)
4. **Expected:** < 2 seconds

### Check Script Execution Time
1. Open DevTools → Performance tab
2. Click "Record" button
3. Refresh page
4. Stop recording after page loads
5. Look for `selectFormat` function calls
6. **Expected:** < 100ms total

## 🚀 Production Deployment Verification

After deploying to production:

1. **Wait 2-3 minutes** for Railway/Koyeb to deploy
2. **Clear browser cache** completely
3. **Hard refresh** the page
4. **Open DevTools Console** BEFORE loading page
5. **Navigate** to /streamlined-calculator
6. **Verify** all console messages appear
7. **Test** format selection
8. **Upload** a test file

## 📝 Reporting Issues

If format selection still doesn't work, collect this information:

1. **Browser Info:**
   - Browser name and version
   - Operating system

2. **Console Output:**
   - Copy ALL messages from Console tab
   - Include error messages (in red)

3. **Network Tab:**
   - Screenshot of failed requests
   - Check for HTTP status codes (404, 500, etc.)

4. **Screenshot:**
   - Full page screenshot showing the issue

5. **Steps to Reproduce:**
   - Exact steps you took
   - What you expected vs what happened

## 🔍 Advanced Debugging

### Check if DOMContentLoaded fired
```javascript
// Paste in Console:
console.log('DOM ready state:', document.readyState);
```
**Expected:** `complete` or `interactive`

### Manually trigger format selection
```javascript
// Paste in Console:
selectFormat(1);
```
**Expected:** Upload section appears

### Check event listeners
```javascript
// Paste in Console:
const cards = document.querySelectorAll('.format-card');
cards.forEach(card => {
    console.log('Card:', card);
    console.log('Has click listener:', getEventListeners(card).click?.length > 0);
});
```

### Force initialize format cards
```javascript
// Paste in Console - ONLY if automatic initialization failed:
document.querySelectorAll('.format-card').forEach(card => {
    card.addEventListener('click', function() {
        const formatNumber = parseInt(this.getAttribute('data-format'));
        selectFormat(formatNumber);
    });
});
console.log('✅ Manually initialized format cards');
```

## 📞 Support

If none of these solutions work, the issue may be:
- Server-side configuration problem
- Network/firewall blocking scripts
- Browser extension interference
- CDN (Bootstrap/FontAwesome) loading failure

Try accessing from a different network or device to isolate the issue.
