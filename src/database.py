import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path


class Database:
    def __init__(self, config: Dict[str, Any]):
        db_path = config.get('path', 'data/publications.db')
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Create a new connection with WAL mode and timeout."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Initialize database schema"""
        with self._get_conn() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS publications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT,
                    date TEXT,
                    vigente TEXT DEFAULT 'Si',
                    norma TEXT DEFAULT '',
                    summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notified INTEGER DEFAULT 0
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_source ON publications(source)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_category ON publications(category)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_date ON publications(date)')
    
    def save_publication(self, publication: Dict[str, Any]) -> int:
        """Save a new publication to database"""
        with self._get_conn() as conn:
            cursor = conn.execute('''
                INSERT OR IGNORE INTO publications 
                (source, url, title, category, date, vigente, norma, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                publication.get('source'),
                publication.get('url'),
                publication.get('title'),
                publication.get('category'),
                publication.get('date'),
                publication.get('vigente', 'Si'),
                publication.get('norma', ''),
                publication.get('summary')
            ))
            return cursor.lastrowid or 0
    
    def publication_exists(self, url: str) -> bool:
        """Check if publication already exists by URL"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                'SELECT 1 FROM publications WHERE url = ?', (url,)
            )
            return cursor.fetchone() is not None
    
    def get_publications(self, source: Optional[str] = None, 
                        category: Optional[str] = None,
                        days: int = 30) -> List[Dict[str, Any]]:
        """Get recent publications with optional filters"""
        with self._get_conn() as conn:
            query = 'SELECT * FROM publications WHERE 1=1'
            params: list = []
            
            if source:
                query += ' AND source = ?'
                params.append(source)
            
            if category:
                query += ' AND category = ?'
                params.append(category)
            
            if days:
                date_limit = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                query += ' AND date >= ?'
                params.append(date_limit)
            
            query += ' ORDER BY date DESC, created_at DESC'
            
            rows = conn.execute(query, params).fetchall()
            
            return [{
                'id': row['id'],
                'source': row['source'],
                'url': row['url'],
                'title': row['title'],
                'category': row['category'],
                'date': row['date'],
                'vigente': row['vigente'],
                'norma': row['norma'],
                'summary': row['summary'],
                'created_at': row['created_at'],
                'notified': bool(row['notified'])
            } for row in rows]
    
    def get_all_publications(self) -> List[Dict[str, Any]]:
        """Get all publications without date filter."""
        with self._get_conn() as conn:
            rows = conn.execute(
                'SELECT * FROM publications ORDER BY category, source, title'
            ).fetchall()
            return [dict(row) for row in rows]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        with self._get_conn() as conn:
            total = conn.execute('SELECT COUNT(*) as c FROM publications').fetchone()['c']
            
            categories = conn.execute('''
                SELECT category, COUNT(*) as count 
                FROM publications GROUP BY category ORDER BY count DESC
            ''').fetchall()
            
            sources = conn.execute('''
                SELECT source, COUNT(*) as count 
                FROM publications GROUP BY source ORDER BY count DESC
            ''').fetchall()
            
            vigentes = conn.execute(
                "SELECT COUNT(*) as c FROM publications WHERE vigente = 'Si'"
            ).fetchone()['c']
            
            tramitacion = conn.execute(
                "SELECT COUNT(*) as c FROM publications WHERE vigente LIKE '%tramit%'"
            ).fetchone()['c']
            
            recent = conn.execute('''
                SELECT * FROM publications ORDER BY created_at DESC LIMIT 5
            ''').fetchall()
            
            return {
                'total': total,
                'categories': [dict(r) for r in categories],
                'sources': [dict(r) for r in sources],
                'vigentes': vigentes,
                'tramitacion': tramitacion,
                'recent': [dict(r) for r in recent],
            }
    
    def get_publications_by_category(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get publications optionally filtered by category."""
        with self._get_conn() as conn:
            if category:
                rows = conn.execute(
                    'SELECT * FROM publications WHERE category = ? ORDER BY source, title',
                    (category,)
                ).fetchall()
            else:
                rows = conn.execute(
                    'SELECT * FROM publications ORDER BY category, source, title'
                ).fetchall()
            return [dict(row) for row in rows]
    
    def mark_as_notified(self, publication_ids: List[int]):
        """Mark publications as notified"""
        if not publication_ids:
            return
        with self._get_conn() as conn:
            placeholders = ','.join('?' * len(publication_ids))
            conn.execute(
                f'UPDATE publications SET notified = 1 WHERE id IN ({placeholders})',
                publication_ids
            )
