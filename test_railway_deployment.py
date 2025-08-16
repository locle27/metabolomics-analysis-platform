#!/usr/bin/env python3
"""
Railway Deployment Test Script
Tests your Railway deployment with custom domain
"""

import os
import sys
import socket
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_dns_propagation():
    """Check DNS propagation for custom domain"""
    print(f"🔍 Checking DNS Propagation")
    print("-" * 35)
    
    domain = "phenikaa-lipidomics-analysis.edu.vn"
    
    try:
        ip_address = socket.gethostbyname(domain)
        print(f"✅ DNS resolved successfully!")
        print(f"📍 IP Address: {ip_address}")
        return True
        
    except socket.gaierror:
        print(f"❌ DNS resolution failed")
        print(f"💡 Domain not found - DNS may not be propagated yet")
        print(f"🕒 Wait time: Up to 72 hours for full propagation")
        return False
    except Exception as e:
        print(f"❌ DNS check error: {e}")
        return False

def test_domain_accessibility():
    """Test if the custom domain is accessible"""
    domain = "https://phenikaa-lipidomics-analysis.edu.vn"
    
    print(f"\n🌐 Testing Domain Accessibility")
    print("-" * 35)
    print(f"Testing: {domain}")
    
    try:
        response = requests.get(domain, timeout=15)
        if response.status_code == 200:
            print(f"✅ Domain is accessible! (Status: {response.status_code})")
            return True
        else:
            print(f"⚠️ Domain returned status: {response.status_code}")
            return False
    except requests.exceptions.SSLError as e:
        print(f"🔒 SSL certificate issue")
        print(f"💡 Railway might still be generating SSL certificate (wait 10-15 minutes)")
        return False
    except requests.exceptions.ConnectTimeout:
        print(f"⏰ Connection timeout - domain might be slow to respond")
        return False
    except requests.exceptions.ConnectionError as e:
        if "NameResolutionError" in str(e) or "getaddrinfo failed" in str(e):
            print(f"🌐 DNS not propagated yet")
            print(f"💡 DNS propagation can take up to 72 hours")
        else:
            print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_oauth_endpoint():
    """Test OAuth debug endpoint"""
    domain = "https://phenikaa-lipidomics-analysis.edu.vn"
    
    print(f"\n🔐 Testing OAuth Debug Endpoint")
    print("-" * 35)
    
    try:
        response = requests.get(f"{domain}/oauth-debug", timeout=10)
        if response.status_code == 200:
            print(f"✅ OAuth debug endpoint accessible")
            return True
        else:
            print(f"⚠️ OAuth debug returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OAuth endpoint test failed: {e}")
        return False

def test_email_endpoint():
    """Test email system endpoint"""
    domain = "https://phenikaa-lipidomics-analysis.edu.vn"
    
    print(f"\n📧 Testing Email System Endpoint")
    print("-" * 35)
    
    try:
        response = requests.get(f"{domain}/test-email-system", timeout=10)
        if response.status_code == 200:
            print(f"✅ Email system endpoint accessible")
            return True
        else:
            print(f"⚠️ Email system returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Email endpoint test failed: {e}")
        return False

def check_environment_variables():
    """Check if environment variables are set locally"""
    print(f"🔧 Checking Local Environment Variables")
    print("-" * 40)
    
    required_vars = [
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET', 
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'DATABASE_URL'
    ]
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 20}")
        else:
            print(f"❌ {var}: NOT SET")
            all_good = False
    
    return all_good

def display_next_steps():
    """Show next steps based on test results"""
    print(f"\n📋 Next Steps")
    print("-" * 15)
    print(f"""
🔧 If DNS not propagated:
   1. Wait for Railway DNS to update (up to 72 hours)
   2. Check Railway dashboard for domain status
   3. Verify CNAME record at your domain registrar

📧 If domain accessible but endpoints fail:
   1. Check Railway environment variables are set
   2. Verify Railway deployment completed successfully
   3. Check Railway logs for any errors

🔐 If OAuth issues:
   1. Verify Google Console redirect URIs include:
      - https://phenikaa-lipidomics-analysis.edu.vn/auth
      - https://phenikaa-lipidomics-analysis.edu.vn/callback
   2. Wait 5-10 minutes for Google changes to propagate

🎯 Once everything works:
   - Visit: https://phenikaa-lipidomics-analysis.edu.vn
   - Test OAuth login
   - Test schedule form with email notifications
   - Test lipid data analysis and charts
    """)

def main():
    """Run Railway deployment tests"""
    print("🚄 RAILWAY DEPLOYMENT TEST")
    print("=" * 30)
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Domain: phenikaa-lipidomics-analysis.edu.vn")
    print("=" * 60)
    
    # Test results tracking
    tests = []
    
    # Check local environment
    env_check = check_environment_variables()
    tests.append(("Local Environment", env_check))
    
    # Check DNS propagation
    dns_check = check_dns_propagation()
    tests.append(("DNS Propagation", dns_check))
    
    # Test domain accessibility
    domain_test = test_domain_accessibility()
    tests.append(("Domain Accessibility", domain_test))
    
    # If domain works, test endpoints
    if domain_test:
        oauth_test = test_oauth_endpoint()
        tests.append(("OAuth Endpoint", oauth_test))
        
        email_test = test_email_endpoint()
        tests.append(("Email Endpoint", email_test))
    
    # Display results
    print(f"\n📊 Test Results Summary")
    print("=" * 25)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"🚀 Your Railway deployment is working perfectly!")
        print(f"🌐 Visit: https://phenikaa-lipidomics-analysis.edu.vn")
    else:
        print(f"\n⚠️ Some tests failed - this is normal during DNS propagation")
        display_next_steps()
        
        if not dns_check:
            print(f"\n💡 Most likely cause: DNS not propagated yet")
            print(f"   ⏰ Wait 15-60 minutes and run this test again")
            print(f"   📋 Check Railway dashboard for domain status")

if __name__ == "__main__":
    main()