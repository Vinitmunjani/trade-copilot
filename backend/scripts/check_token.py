import os
import sys
# Ensure backend root is on sys.path so `import app` works when running from scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import get_settings

s = get_settings()
print('METAAPI_TOKEN present:', bool(s.METAAPI_TOKEN))
print('METAAPI_TOKEN preview:', (s.METAAPI_TOKEN[:40] + '...') if s.METAAPI_TOKEN else '')
