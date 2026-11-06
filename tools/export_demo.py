"""Export only synthetic fixture data, without sessions, secrets or real records."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.seed import generate_profiles
print(json.dumps({'schema_version':1,'demo_only':True,'profiles':generate_profiles()},ensure_ascii=False,indent=2))
