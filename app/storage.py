"""Small local demo store; access is isolated behind this repository class.

The public catalog is a cached immutable snapshot, so reads do not need one SQL
query per visitor. The cache has a TTL as well as explicit local invalidation.
Do not share this SQLite file across machines. Use one Uvicorn worker for MVP.
"""
import json
import sqlite3
import time
import threading
from contextlib import contextmanager
from pathlib import Path
from .seed import generate_profiles

class Repository:
    def __init__(self,path:str):
        self.path=path
        self._cache=None
        self._cached_at=0.0
        self._lock=threading.RLock()
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.executescript("""
              PRAGMA journal_mode=WAL;
              CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,is_demo INTEGER NOT NULL CHECK(is_demo=1),
                login_type TEXT NOT NULL DEFAULT 'demo_only',created_at INTEGER NOT NULL);
              CREATE TABLE IF NOT EXISTS profiles (
                user_id TEXT PRIMARY KEY REFERENCES users(id),profession TEXT NOT NULL,
                city TEXT NOT NULL,state TEXT NOT NULL,payload TEXT NOT NULL,updated_at INTEGER NOT NULL);
              CREATE INDEX IF NOT EXISTS ix_profiles_location ON profiles(state,city,profession);
              CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),
                csrf TEXT NOT NULL,expires_at INTEGER NOT NULL,created_at INTEGER NOT NULL);
              CREATE INDEX IF NOT EXISTS ix_session_expiry ON sessions(expires_at);
            """)
            for p in generate_profiles():
                db.execute('INSERT OR IGNORE INTO users(id,email,is_demo,created_at) VALUES(?,?,1,?)',(p['id'],p['email'],int(time.time())))
                db.execute('INSERT OR IGNORE INTO profiles VALUES(?,?,?,?,?,?)',(p['id'],p['profession'],p['city'],p['state'],json.dumps(p,ensure_ascii=False),int(time.time())))

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=3)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=3000')
        try:
            with db: yield db
        finally: db.close()

    def catalog(self):
        with self._lock:
            if self._cache is None or time.monotonic()-self._cached_at>30:
                with self.connect() as db:
                    self._cache=tuple(json.loads(r['payload']) for r in db.execute('SELECT payload FROM profiles ORDER BY user_id'))
                self._cached_at=time.monotonic()
            # Internal caller only: do not mutate returned dicts.
            return self._cache

    def get(self,user_id):
        return next((p for p in self.catalog() if p['id']==user_id),None)

    def update(self,user_id,changes):
        with self._lock:
            with self.connect() as db:
                row=db.execute('SELECT payload FROM profiles WHERE user_id=?',(user_id,)).fetchone()
                if not row: return None
                profile=json.loads(row['payload'])
                profile.update(changes)
                db.execute('UPDATE profiles SET payload=?,updated_at=? WHERE user_id=?',(json.dumps(profile,ensure_ascii=False),int(time.time()),user_id))
            self._cache=None
            return profile

    def session_create(self,token_hash,user_id,csrf):
        now=int(time.time())
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE expires_at<=?',(now,))
            db.execute('INSERT INTO sessions VALUES(?,?,?,?,?)',(token_hash,user_id,csrf,now+3600,now))
            db.execute('DELETE FROM sessions WHERE user_id=? AND token_hash NOT IN (SELECT token_hash FROM sessions WHERE user_id=? ORDER BY created_at DESC,rowid DESC LIMIT 5)',(user_id,user_id))

    def session_get(self,token_hash):
        with self.connect() as db:
            row=db.execute('SELECT user_id,csrf FROM sessions WHERE token_hash=? AND expires_at>?',(token_hash,int(time.time()))).fetchone()
            return dict(row) if row else None

    def session_delete(self,token_hash):
        with self.connect() as db: db.execute('DELETE FROM sessions WHERE token_hash=?',(token_hash,))
