import sqlite3
from datetime import datetime, timedelta

class FocusDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('focus_sessions.db')
        self._create_table()

    def _create_table(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS sessions
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             start_time DATETIME NOT NULL,
             end_time DATETIME NOT NULL,
             session_type TEXT NOT NULL)''')

    def add_session(self, start, end, session_type):
        self.conn.execute('INSERT INTO sessions (start_time, end_time, session_type) VALUES (?,?,?)',
                         (start.isoformat(), end.isoformat(), session_type))
        self.conn.commit()

    def get_daily_stats(self):
        today = datetime.today().date()
        five_days_ago = today - timedelta(days=5)
        
        cur = self.conn.cursor()
        cur.execute('''SELECT DATE(start_time) as date, 
                      SUM(strftime('%s', end_time) - strftime('%s', start_time))/3600
                      FROM sessions
                      WHERE date BETWEEN ? AND ?
                      GROUP BY date''',
                   (five_days_ago.isoformat(), today.isoformat()))
        return {row[0]: row[1] for row in cur.fetchall()}

    def close(self):
        self.conn.close()