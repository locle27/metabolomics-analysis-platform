# 🛡️ Admin Quick Reference Guide

## 🔐 **Admin Access**

### **Getting Admin Rights:**
- **First User**: Automatically becomes admin
- **Promotion**: Visit `/promote-to-admin` (only works if no admins exist)
- **Admin Panel**: Access via Management dropdown menu

### **Admin URLs:**
- **Main Admin**: `/admin`
- **User Management**: `/admin/users`
- **Database Stats**: `/admin/stats`
- **System Info**: `/user-debug`

---

## 👥 **User Management**

### **User Roles:**
- **Admin**: Full access, user management
- **Manager**: Database management, scheduling
- **User**: Basic analysis tools only

### **Managing Users:**
1. Go to Management → Dashboard
2. View all registered users
3. Change roles via dropdown
4. Activate/deactivate accounts
5. Monitor user activity

### **Common Admin Tasks:**
```bash
# Promote user to manager
Role: User → Manager

# Deactivate inactive user
Status: Active → Inactive

# Grant admin access (careful!)
Role: User → Admin
```

---

## 🗄️ **Database Management**

### **Database Status:**
- **Tables**: main_lipids, annotated_ions, users
- **Records**: 800+ lipids imported
- **Connection**: PostgreSQL on Railway

### **Database Operations:**
1. **View Stats**: `/admin/stats`
2. **Import Data**: Management → Database Management
3. **Backup**: Automatic via Railway
4. **Optimize**: Run via admin panel

### **Database Health Check:**
```sql
-- Connection test
SELECT 1;

-- Table counts
SELECT COUNT(*) FROM main_lipids;
SELECT COUNT(*) FROM users;
```

---

## 📧 **Email System Management**

### **Current Configuration:**
- **SMTP**: Gmail (smtp.gmail.com)
- **Email**: loc22100302@gmail.com
- **Password**: nxvg dhug ccdg mdaj (App Password)

### **Email Functions:**
- **Password Reset**: Automatic
- **User Verification**: Automatic
- **Admin Notifications**: Manual/Automatic
- **Consultation Bookings**: Automatic

### **Email Troubleshooting:**
1. **Test Email Config**: `/admin/email-test`
2. **Check Logs**: Admin panel → System Logs
3. **Verify SMTP**: Gmail settings
4. **Update App Password**: If needed

---

## 🔧 **System Monitoring**

### **Health Checks:**
- **Main Health**: `/health`
- **Detailed Status**: `/user-debug`
- **Database Status**: Admin dashboard

### **Key Metrics to Monitor:**
- **Response Time**: < 2 seconds
- **Database Connections**: Active
- **Email System**: Functional
- **User Activity**: Regular logins

### **Warning Signs:**
- **Slow Response**: > 5 seconds
- **Database Errors**: Connection failures
- **Email Failures**: SMTP errors
- **No User Activity**: Platform issues

---

## 🚨 **Emergency Procedures**

### **Platform Down:**
1. Check Railway dashboard
2. Review deployment logs
3. Check health endpoint
4. Restart if necessary

### **Database Issues:**
1. Check connection string
2. Verify Railway database status
3. Review error logs
4. Contact Railway support if needed

### **Authentication Problems:**
1. Check Google OAuth settings
2. Verify email configuration
3. Test with different browser
4. Check user account status

---

## 📊 **Performance Optimization**

### **Chart Performance:**
- **Limit**: 5 lipids max per analysis
- **Timeout**: 30 seconds for complex queries
- **Memory**: Monitor RAM usage

### **Database Optimization:**
- **Indexing**: Ensure proper indexes
- **Cleanup**: Remove old logs
- **Backup**: Regular automated backups

### **User Experience:**
- **Response Times**: Monitor regularly
- **Error Rates**: Keep < 1%
- **Uptime**: Target 99.9%

---

## 🔄 **Regular Maintenance**

### **Daily:**
- Check platform health (`/health`)
- Review user registrations
- Monitor error logs

### **Weekly:**
- User activity review
- Performance metrics check
- Email system test

### **Monthly:**
- Database optimization
- Security review
- Backup verification

---

## 📞 **Emergency Contacts**

### **Technical Issues:**
- **Railway**: Platform hosting
- **Google Cloud**: OAuth issues
- **Gmail**: Email problems

### **Platform Support:**
- **Admin Email**: loc22100302@gmail.com
- **Health Check**: `/health`
- **System Status**: Railway dashboard

---

## 🛠️ **Common Admin Commands**

### **User Management:**
```python
# Promote user to admin
user.role = 'admin'
db.session.commit()

# Deactivate user
user.is_active = False
db.session.commit()

# Reset user password (trigger email)
# Via admin panel
```

### **Database Operations:**
```python
# Get user count
User.query.count()

# Get lipid count
MainLipid.query.count()

# Check active users
User.query.filter_by(is_active=True).count()
```

### **System Information:**
```python
# Check features loaded
/health endpoint

# Database status
/user-debug endpoint

# Platform statistics
/admin/stats
```

---

## ⚡ **Quick Fixes**

### **User Can't Login:**
1. Check user account is active
2. Verify email/password
3. Test Google OAuth
4. Clear browser cache

### **Charts Not Loading:**
1. Check JavaScript enabled
2. Verify lipid selection
3. Database connection test
4. Reduce selected lipids

### **Email Not Sending:**
1. Check Gmail app password
2. Verify SMTP settings
3. Test email configuration
4. Review error logs

### **Slow Performance:**
1. Check database queries
2. Monitor server load
3. Optimize selected lipids
4. Review user activity

---

## 📋 **Admin Checklist**

### **New User Registration:**
- [ ] Verify email address
- [ ] Assign appropriate role
- [ ] Send welcome information
- [ ] Monitor first login

### **System Health:**
- [ ] Check `/health` endpoint
- [ ] Review error logs
- [ ] Monitor response times
- [ ] Verify database connection

### **Security Review:**
- [ ] Audit user accounts
- [ ] Check admin access
- [ ] Review authentication logs
- [ ] Update passwords if needed

### **Performance Check:**
- [ ] Test chart loading
- [ ] Verify email system
- [ ] Check database queries
- [ ] Monitor memory usage

---

*Admin Quick Reference - Always Keep This Handy!*