# 🧬 Complete Metabolomics Platform User Guide

## 🚀 **Platform Overview**

Your **Professional Metabolomics Data Analysis Platform** is now live on Railway with full functionality. This guide covers everything you need to know to use and manage the platform effectively.

## 🌐 **Platform Access**

### **Your Live Platform URLs:**
- **Main Platform**: `https://your-railway-domain.railway.app`
- **Health Check**: `https://your-railway-domain.railway.app/health`
- **Custom Domain**: `https://httpsphenikaa-lipidomics-analysis.xyz` (if configured)

### **Platform Status:**
- ✅ **Status**: Fully operational
- ✅ **Database**: 800+ lipids imported
- ✅ **Authentication**: Google OAuth + Email system
- ✅ **Charts**: Interactive dual-chart analysis
- ✅ **Email**: Gmail SMTP configured

---

## 🔐 **1. AUTHENTICATION SYSTEM**

### **Login Options:**
1. **Google OAuth** (Recommended)
   - Click "Login with Google" 
   - Uses your existing Google account
   - Instant access, secure

2. **Email Registration**
   - Register with email/password
   - Email verification required
   - Password reset available

### **User Roles:**
- **Admin**: Full platform access, user management
- **Manager**: Database management, scheduling
- **User**: Analysis tools and visualization

### **First User Setup:**
- **First person to register automatically becomes Admin**
- Subsequent users get 'User' role by default
- Admins can promote other users

---

## 🏠 **2. HOMEPAGE & NAVIGATION**

### **Main Navigation:**
- **HOME**: Platform overview and news
- **ANALYSIS**: Lipid selection and interactive charts
- **SCHEDULE**: Consultation booking (public access)
- **MANAGEMENT**: Admin tools (admin only)
- **DOCUMENTATION**: Platform documentation

### **Homepage Features:**
- Platform statistics and overview
- Recent news and updates
- Quick access to main features
- System status indicators

---

## 📊 **3. LIPID ANALYSIS SYSTEM**

### **Dashboard (`/dashboard` or `/lipid-selection`):**

#### **Lipid Selection:**
- **Grid View**: Visual cards showing lipid information
- **Search**: Real-time search by lipid name
- **Filters**: 
  - Lipid class filter
  - Retention time range
  - Multi-ion lipids only
- **Selection Panel**: Fixed panel showing selected lipids

#### **Lipid Information Displayed:**
- Lipid name and class
- Retention time
- Precursor/product masses
- Number of annotations
- Integration areas

#### **How to Select Lipids:**
1. Use search box for specific lipids
2. Apply class filters (AC, TG, PC, etc.)
3. Set retention time ranges
4. Click lipid cards to select
5. Selected lipids appear in right panel
6. Click "View Interactive Charts" when ready

---

## 📈 **4. INTERACTIVE CHART SYSTEM**

### **Dual Chart Analysis (`/dual-chart-view`):**

#### **Chart Layout:**
- **Chart 1**: Focused view (main lipid ± 0.6 minutes)
- **Chart 2**: Overview (full 0-16 minute range)
- **Shared Legend**: Color-coded lipid types
- **Information Panel**: Detailed lipid data on hover

#### **Chart Features:**
- **2D Area Hover Detection**: Hover over colored integration areas
- **Click-to-Zoom**: Click chart to activate zoom mode
- **Pan & Zoom**: Mouse wheel zoom, Shift+drag pan
- **Reset**: Double-click to reset zoom
- **Deactivate**: Click outside chart to deactivate

#### **Color System:**
- **Blue**: Current/main lipid
- **Light Green**: Similar MRM transitions
- **Light Red**: +2 isotope peaks
- **Turquoise**: Default/other annotations

#### **Chart Interaction:**
1. Click on chart to activate zoom mode (blue border appears)
2. Use mouse wheel to zoom in/out
3. Hold Shift and drag to pan around
4. Hover over colored areas to see lipid details
5. Click outside chart to deactivate and restore page scroll

---

## 🛠️ **5. ADMINISTRATION**

### **Admin Dashboard (`/admin` - Admin only):**

#### **User Management:**
- View all registered users
- Change user roles (Admin/Manager/User)
- Activate/deactivate accounts
- View user activity

#### **Database Management:**
- Import new lipid data
- View database statistics
- Backup and restore data
- Optimize database performance

#### **System Settings:**
- Configure email settings
- Update platform settings
- View system logs
- Monitor performance

#### **Analytics:**
- User activity reports
- Platform usage statistics
- Popular lipids and searches
- System performance metrics

---

## 📧 **6. EMAIL SYSTEM**

### **Configured Email Features:**
- **SMTP Server**: Gmail (smtp.gmail.com)
- **Email Address**: loc22100302@gmail.com
- **Features**: Password reset, notifications, admin alerts

### **Email Functions:**
1. **Password Reset**: Automatic reset emails
2. **Account Verification**: New user verification
3. **Admin Notifications**: System alerts
4. **Consultation Booking**: Schedule confirmations

---

## 🔧 **7. PLATFORM MANAGEMENT**

### **Railway Deployment:**

#### **Environment Variables (Already Configured):**
```bash
DATABASE_URL=postgresql://postgres:...
FLASK_ENV=production
SECRET_KEY=production-metabolomics-secret-key-2025
GOOGLE_CLIENT_ID=164274105715-...
GOOGLE_CLIENT_SECRET=GOCSPX-...
MAIL_USERNAME=loc22100302@gmail.com
MAIL_PASSWORD=nxvg dhug ccdg mdaj
CUSTOM_DOMAIN=httpsphenikaa-lipidomics-analysis.xyz
```

#### **Deployment Info:**
- **Platform**: Railway (cloud hosting)
- **Database**: PostgreSQL (hosted on Railway)
- **SSL**: Automatic HTTPS
- **Monitoring**: Built-in health checks

### **Database Information:**
- **Type**: PostgreSQL 
- **Location**: Railway cloud
- **Size**: 800+ lipids imported
- **Tables**: main_lipids, annotated_ions, lipid_classes, users
- **Backup**: Automatic Railway backups

---

## 🚨 **8. TROUBLESHOOTING**

### **Common Issues & Solutions:**

#### **Login Problems:**
- **Google OAuth fails**: Check GOOGLE_CLIENT_ID configuration
- **Email login fails**: Verify email/password, check spam folder
- **Account locked**: Contact admin for account activation

#### **Chart Issues:**
- **Charts not loading**: Check browser JavaScript enabled
- **Zoom not working**: Click chart first to activate
- **Data missing**: Verify lipid selection, check database connection

#### **Performance Issues:**
- **Slow loading**: Check internet connection
- **Database timeout**: May indicate high server load
- **Charts laggy**: Reduce number of selected lipids

#### **Email Issues:**
- **Reset email not received**: Check spam folder
- **Email configuration**: Verify MAIL_USERNAME and MAIL_PASSWORD

### **Getting Help:**
1. Check platform status at `/health`
2. Review system logs (admin only)
3. Contact system administrator
4. Check Railway deployment status

---

## 📈 **9. BEST PRACTICES**

### **For Users:**
- **Start with specific searches** rather than browsing all lipids
- **Select 3-5 lipids max** for optimal chart performance
- **Use class filters** to narrow down results
- **Save interesting lipid combinations** for future reference

### **For Admins:**
- **Regular backups**: Monitor automatic Railway backups
- **User management**: Review and approve new user registrations
- **Performance monitoring**: Check `/health` endpoint regularly
- **Email testing**: Verify email system periodically

### **Security:**
- **Strong passwords**: Encourage users to use strong passwords
- **Role management**: Assign appropriate roles to users
- **Regular updates**: Keep platform dependencies updated
- **Monitor access**: Review user activity logs

---

## 🔄 **10. MAINTENANCE & UPDATES**

### **Regular Maintenance:**
- **Database optimization**: Monthly performance checks
- **User cleanup**: Remove inactive accounts
- **Log rotation**: Clear old system logs
- **Security updates**: Update dependencies

### **Platform Updates:**
1. **Test in development** before deploying
2. **Backup database** before major changes
3. **Update Railway environment** variables if needed
4. **Monitor deployment** for issues
5. **Verify functionality** after updates

### **Monitoring:**
- **Health checks**: Automated via Railway
- **Performance metrics**: Available in admin dashboard
- **Error tracking**: System logs capture issues
- **User feedback**: Monitor for reported problems

---

## 📞 **11. SUPPORT & CONTACT**

### **System Administrator:**
- **Email**: loc22100302@gmail.com
- **Platform Admin**: First registered user (auto-admin)

### **Technical Support:**
- **Railway Dashboard**: For hosting issues
- **GitHub Repository**: For code-related issues
- **Platform Health**: `/health` endpoint for status

### **Documentation:**
- **This Guide**: Complete platform documentation
- **Railway Docs**: For deployment questions
- **Flask Documentation**: For technical details

---

## 🎯 **12. QUICK START GUIDE**

### **For New Users:**
1. **Visit platform URL**
2. **Register/Login** (Google OAuth recommended)
3. **Explore Dashboard** - familiarize with interface
4. **Select lipids** - use search and filters
5. **View charts** - interactive analysis
6. **Experiment** - try different lipid combinations

### **For Admins:**
1. **Access admin panel** (`/admin`)
2. **Review user accounts** - approve/manage users
3. **Check system status** - monitor performance
4. **Configure settings** - customize platform
5. **Setup monitoring** - regular health checks

---

## 🎉 **CONGRATULATIONS!**

Your **Professional Metabolomics Data Analysis Platform** is now fully operational with:

- ✅ **Complete Authentication System**
- ✅ **Advanced Interactive Charts** 
- ✅ **Professional Database Management**
- ✅ **Email Integration**
- ✅ **Production-Grade Hosting**
- ✅ **Comprehensive Admin Tools**

**The platform is ready for scientific research and analysis!** 🧬✨

---

*Last Updated: August 17, 2025*
*Platform Version: Production 1.0*
*Status: Fully Operational*