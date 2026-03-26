#!/usr/bin/env python3
"""
Test script to verify Streamlit secrets.toml is configured correctly
"""
import os
import sys
from pathlib import Path

# Try to load secrets like Streamlit does
secrets_path = Path(__file__).parent / '.streamlit' / 'secrets.toml'

print("=" * 60)
print("Streamlit Secrets Configuration Check")
print("=" * 60)
print(f"Secrets file path: {secrets_path}")
print(f"Secrets file exists: {secrets_path.exists()}")
print()

if not secrets_path.exists():
    print("❌ secrets.toml not found!")
    print()
    print("Please create .streamlit/secrets.toml with your API keys.")
    print("You can copy .streamlit/secrets.toml.example as a template.")
    sys.exit(1)

# Parse TOML file manually (simple parsing for API keys)
api_keys = {}
try:
    with open(secrets_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key in ['TAVILY_API_KEY', 'GOOGLE_MAPS_API_KEY', 'GROQ_API_KEY']:
                    api_keys[key] = value
except Exception as e:
    print(f"❌ Error reading secrets.toml: {e}")
    sys.exit(1)

# Check each API key
required_keys = ['TAVILY_API_KEY', 'GOOGLE_MAPS_API_KEY', 'GROQ_API_KEY']
all_found = True

for key_name in required_keys:
    key_value = api_keys.get(key_name)
    if key_value and key_value != f"your_{key_name.lower().replace('_', '_')}":
        # Show only first 10 and last 4 characters for security
        masked_value = f"{key_value[:10]}...{key_value[-4:]}" if len(key_value) > 14 else "***"
        print(f"✅ {key_name}: {masked_value}")
    else:
        print(f"❌ {key_name}: NOT FOUND or using placeholder value")
        all_found = False

print()
print("=" * 60)
if all_found:
    print("✅ All API keys found! Your secrets.toml is configured correctly.")
    print()
    print("You can now run the app with:")
    print("  ./run_app.sh")
    print("  or")
    print("  env/bin/python -m streamlit run streamlit_app.py")
else:
    print("❌ Some API keys are missing or using placeholder values.")
    print()
    print("Make sure your .streamlit/secrets.toml contains:")
    print('  TAVILY_API_KEY = "your_actual_key_here"')
    print('  GOOGLE_MAPS_API_KEY = "your_actual_key_here"')
    print('  GROQ_API_KEY = "your_actual_key_here"')
print("=" * 60)
