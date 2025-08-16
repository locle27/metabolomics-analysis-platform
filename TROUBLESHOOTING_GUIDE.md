# 🔧 Troubleshooting Guide

## 🚨 **Common Issues & Solutions**

### **LOGIN PROBLEMS**

#### ❌ **Google OAuth Not Working**
**Symptoms**: "OAuth error" or redirect fails
**Causes**: Incorrect Google Client ID/Secret, wrong redirect URLs
**Solutions**:
1. Check Google Cloud Console → Credentials
2. Verify CLIENT_ID and CLIENT_SECRET in Railway environment
3. Ensure redirect URLs include your domain
4. Clear browser cache and cookies

#### ❌ **Email Login Fails**
**Symptoms**: "Invalid credentials" message
**Causes**: Wrong password, account not activated, email not verified
**Solutions**:
1. Use "Forgot Password" to reset
2. Check email spam folder for verification
3. Contact admin to check account status
4. Try different browser/incognito mode

#### ❌ **Account Locked/Inactive**
**Symptoms**: "Account inactive" message
**Causes**: Admin deactivated account, suspicious activity
**Solutions**:
1. Contact platform administrator
2. Admin: Check user status in admin panel
3. Admin: Reactivate via Management → Dashboard

---

### **CHART PROBLEMS**

#### ❌ **Charts Not Loading**
**Symptoms**: Blank chart area, loading spinner forever
**Causes**: JavaScript disabled, database connection issues, too many lipids selected
**Solutions**:
1. Enable JavaScript in browser
2. Check `/health` endpoint for database status
3. Reduce number of selected lipids (max 5)
4. Clear browser cache
5. Try different browser

#### ❌ **Zoom Not Working**
**Symptoms**: Mouse wheel doesn't zoom, can't pan
**Causes**: Chart not activated, JavaScript errors
**Solutions**:
1. **Click the chart first** to activate (blue border should appear)
2. Check browser console for JavaScript errors
3. Refresh page and try again
4. Use double-click to reset zoom

#### ❌ **Hover Tooltips Missing**
**Symptoms**: No information when hovering over colored areas
**Causes**: Area detection off, CSS conflicts
**Solutions**:
1. Hover specifically over **colored integration areas**
2. Don't hover on chart background or axes
3. Check if external information panel updates
4. Refresh page if tooltips stop working

#### ❌ **Charts Show No Data**
**Symptoms**: Empty charts, no colored areas
**Causes**: No lipids selected, database issues, wrong lipid ID
**Solutions**:
1. Verify lipids are selected in dashboard
2. Check lipid ID in URL parameter
3. Test with known working lipid (e.g., ID: 1)
4. Check database connection status

---

### **DATABASE ISSUES**

#### ❌ **Database Connection Failed**
**Symptoms**: "Database unavailable", connection errors
**Causes**: Railway database down, wrong connection string, network issues
**Solutions**:
1. Check Railway dashboard for database status
2. Verify DATABASE_URL environment variable
3. Test connection with simple query
4. Contact Railway support if persistent

#### ❌ **Slow Database Queries**
**Symptoms**: Long loading times, timeouts
**Causes**: Complex queries, database overload, missing indexes
**Solutions**:
1. Reduce complexity of lipid selections
2. Check database performance in Railway
3. Admin: Run database optimization
4. Limit concurrent users if needed

#### ❌ **Search Results Empty**
**Symptoms**: No results for valid search terms
**Causes**: Database import issues, search syntax, case sensitivity
**Solutions**:
1. Try exact lipid names (e.g., "AC(24:1)")
2. Use partial searches ("AC")
3. Check lipid class filters
4. Admin: Verify data import completed

---

### **EMAIL PROBLEMS**

#### ❌ **Password Reset Email Not Received**
**Symptoms**: Reset email doesn't arrive
**Causes**: Email in spam, wrong email address, SMTP issues
**Solutions**:
1. **Check spam/junk folder** thoroughly
2. Verify email address spelling
3. Wait 10-15 minutes for delivery
4. Admin: Test email configuration
5. Try different email provider

#### ❌ **Email Configuration Errors**
**Symptoms**: SMTP errors in logs, emails not sending
**Causes**: Wrong Gmail app password, SMTP settings incorrect
**Solutions**:
1. Admin: Verify Gmail app password (nxvg dhug ccdg mdaj)
2. Check MAIL_USERNAME and MAIL_PASSWORD in Railway
3. Test with Gmail 2-factor authentication enabled
4. Review SMTP server settings (smtp.gmail.com:587)

---

### **PERFORMANCE ISSUES**

#### ❌ **Platform Loading Slowly**
**Symptoms**: Pages take > 5 seconds to load
**Causes**: Server overload, database issues, network problems
**Solutions**:
1. Check internet connection speed
2. Monitor `/health` endpoint response time
3. Admin: Check Railway performance metrics
4. Try accessing during off-peak hours

#### ❌ **Charts Laggy or Unresponsive**
**Symptoms**: Slow zoom/pan, delayed hover response
**Causes**: Too much data, browser performance, JavaScript issues
**Solutions**:
1. **Reduce selected lipids** to 3-5 maximum
2. Close other browser tabs
3. Use Chrome or Firefox (recommended)
4. Clear browser cache and cookies

#### ❌ **Memory Issues**
**Symptoms**: Browser crashes, "out of memory" errors
**Causes**: Large datasets, memory leaks, multiple chart views
**Solutions**:
1. Refresh page periodically
2. Limit lipid selections
3. Close unused browser tabs
4. Use 64-bit browser if available

---

### **AUTHENTICATION ERRORS**

#### ❌ **Session Expired**
**Symptoms**: Suddenly logged out, "Please login" messages
**Causes**: Session timeout, server restart, security policy
**Solutions**:
1. Login again (sessions may timeout for security)
2. Check "Remember me" option
3. Admin: Review session timeout settings
4. Clear cookies if persistent

#### ❌ **Permission Denied**
**Symptoms**: "Access denied", "Insufficient permissions"
**Causes**: Wrong user role, account restrictions
**Solutions**:
1. Check user role (User/Manager/Admin)
2. Contact admin for role upgrade
3. Admin: Review user permissions in admin panel
4. Logout and login again

---

### **ADMIN-SPECIFIC ISSUES**

#### ❌ **Admin Panel Not Accessible**
**Symptoms**: 404 error on `/admin`, permission denied
**Causes**: Not admin role, authentication issues
**Solutions**:
1. Verify admin role in database
2. Use `/promote-to-admin` if first user
3. Check login status
4. Contact other admin for role assignment

#### ❌ **User Management Errors**
**Symptoms**: Can't change user roles, database errors
**Causes**: Database connection issues, permission problems
**Solutions**:
1. Check database connection status
2. Refresh admin panel
3. Try one user at a time
4. Review error logs for details

---

## 🔍 **Diagnostic Tools**

### **Health Checks:**
- **Platform Status**: `/health`
- **Detailed Info**: `/user-debug` 
- **Database Test**: Admin dashboard

### **Browser Console:**
```javascript
// Check for JavaScript errors
console.log("Chart status:", window.chart);

// Test API endpoint
fetch('/health').then(r => r.json()).then(console.log);
```

### **Network Testing:**
```bash
# Test platform connectivity
curl https://your-domain.com/health

# Test database endpoint
curl https://your-domain.com/api/database-view
```

---

## 🛠️ **Emergency Recovery**

### **Platform Completely Down:**
1. Check Railway deployment status
2. Review recent changes/deployments
3. Check environment variables
4. Restart deployment if needed
5. Contact Railway support

### **Database Corrupted:**
1. Check Railway database dashboard
2. Restore from latest backup
3. Re-import lipid data if needed
4. Notify users of temporary downtime

### **Authentication System Broken:**
1. Use direct database access if possible
2. Reset admin accounts manually
3. Check Google OAuth configuration
4. Test with fresh browser session

---

## 📞 **Getting Help**

### **Self-Service:**
1. Check this troubleshooting guide
2. Review platform health (`/health`)
3. Clear browser cache/cookies
4. Try different browser

### **Admin Support:**
- **Platform Admin**: loc22100302@gmail.com
- **User Debug**: `/user-debug` endpoint
- **System Status**: Railway dashboard

### **Technical Support:**
- **Railway**: Platform hosting issues
- **Google Cloud**: OAuth problems  
- **GitHub**: Code-related issues

---

## ✅ **Prevention Tips**

### **For Users:**
- Use modern browsers (Chrome, Firefox, Safari)
- Keep JavaScript enabled
- Don't select too many lipids at once
- Logout properly when finished

### **For Admins:**
- Monitor platform health regularly
- Keep backups current
- Test email system monthly
- Review user activity for issues

### **Best Practices:**
- Regular browser cache clearing
- Monitor performance metrics
- Keep user accounts organized
- Document any custom changes

---

*When in doubt, start with `/health` and work from there!*