# Check if all required packages are available
import sys

required_packages = [
    'flask',
    'psycopg2',
    'sqlalchemy', 
    'flask_sqlalchemy',
    'flask_login',
    'authlib',
    'requests_oauthlib',
    'flask_mail',
    'flask_wtf',
    'email_validator',
    'pandas',
    'python_dotenv',
    'boto3',
    'python_dateutil',
    'openpyxl',
    'requests'
]

missing_packages = []
available_packages = []

for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
        available_packages.append(package)
    except ImportError:
        missing_packages.append(package)

print("=== PACKAGE CHECK RESULTS ===")
print(f"✅ Available packages ({len(available_packages)}):")
for pkg in available_packages:
    print(f"  - {pkg}")

print(f"\n❌ Missing packages ({len(missing_packages)}):")
for pkg in missing_packages:
    print(f"  - {pkg}")

if missing_packages:
    print(f"\n🔧 Install missing packages:")
    print(f"pip install {' '.join(missing_packages)}")
    sys.exit(1)
else:
    print(f"\n🎉 All packages are available!")
    sys.exit(0)