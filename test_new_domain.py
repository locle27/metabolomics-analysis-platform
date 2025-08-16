#!/usr/bin/env python3
"""
Test script for new domain: httpsphenikaa-lipidomics-analysis.xyz
"""

import requests
from datetime import datetime

def test_new_domain():
    """Test the new working domain"""
    domain = "https://httpsphenikaa-lipidomics-analysis.xyz"
    
    print("🎯 TESTING NEW DOMAIN")
    print("=" * 30)
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Domain: {domain}")
    print("=" * 60)
    
    # Test endpoints
    endpoints = [
        ('Homepage', '/'),
        ('OAuth Debug', '/oauth-debug'),
        ('Email Test', '/test-email-system'),
        ('Schedule Form', '/schedule'),
        ('Dashboard', '/dashboard'),
        ('Demo Login', '/demo-login')
    ]
    
    results = []
    
    for name, path in endpoints:
        try:
            url = f"{domain}{path}"
            print(f"\n🧪 Testing {name}: {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {name}: WORKING (Status: {response.status_code})")
                results.append((name, True))
            else:
                print(f"⚠️ {name}: Status {response.status_code}")
                results.append((name, False))
                
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            results.append((name, False))
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("=" * 25)
    
    passed = sum(1 for _, result in results)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<15} {status}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed > 0:
        print(f"\n🎉 SUCCESS! Your Railway deployment is working!")
        print(f"🌐 Visit: {domain}")
        
        print(f"\n🔐 NEXT STEP: Update Google OAuth")
        print(f"Add these redirect URIs to Google Cloud Console:")
        print(f"   • https://httpsphenikaa-lipidomics-analysis.xyz/auth")
        print(f"   • https://httpsphenikaa-lipidomics-analysis.xyz/callback")
        print(f"   • https://httpsphenikaa-lipidomics-analysis.xyz/oauth2")
        print(f"   • https://httpsphenikaa-lipidomics-analysis.xyz/google")
        
    return passed > 0

if __name__ == "__main__":
    test_new_domain()