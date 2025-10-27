# test_config.py
from config import settings

print("🔧 Config Check:")
print(f"Frontend URL: {settings.frontend_url}")
print(f"Type: {type(settings.frontend_url)}")
print(f"Length: {len(settings.frontend_url)}")

# Test if it's a valid URL
if "http://localhost:3000" in settings.frontend_url:
    print("✅ Frontend URL looks correct")
else:
    print("❌ Frontend URL issue detected")