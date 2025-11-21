import os
import sys
try:
    with open('env_check.txt', 'w', encoding='utf-8') as f:
        f.write(f"CWD: {os.getcwd()}\n")
        f.write(f"Python: {sys.executable}\n")
        f.write("Success!\n")
except Exception as e:
    # Try to write to a safe location if CWD fails
    with open('c:/Users/Public/env_check_fallback.txt', 'w') as f:
        f.write(f"Error: {e}")
