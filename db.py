from datetime import timedelta
import pandas as pd
import sqlite3
from typing import List, Tuple, Optional
from datetime import datetime

class DB:
    def __init__(self, db_path: str = "forex_data.db"):
        self.db_path = db_path
        self.setup_database()

    def setup_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS forex_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_currency TEXT,
            to_currency TEXT,
            date DATE,
            open_rate REAL,
            high_rate REAL,
            low_rate REAL,
            close_rate REAL,
            volume INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(from_currency, to_currency, date)
        )
        ''')
        conn.commit()
        conn.close()

    def save_to_db(self, df: pd.DataFrame, from_currency: str, to_currency: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute('''
            INSERT INTO forex_rates 
            (from_currency, to_currency, date, open_rate, high_rate, low_rate, close_rate, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(from_currency, to_currency, date) 
            DO UPDATE SET
                open_rate = ?,
                high_rate = ?,
                low_rate = ?,
                close_rate = ?,
                volume = ?
            ''', (
                from_currency,
                to_currency,
                row['Date'].strftime('%Y-%m-%d'),
                row['Open'],
                row['High'],
                row['Low'],
                row['Close'],
                row.get('Volume', 0),
                row['Open'],
                row['High'],
                row['Low'],
                row['Close'],
                row.get('Volume', 0)
            ))
        conn.commit()
        conn.close()

    def fetch_from_db(self, from_currency: str, to_currency: str, start_date: datetime, end_date: datetime) -> List[dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute('''
        SELECT * FROM forex_rates 
        WHERE from_currency = ? 
        AND to_currency = ? 
        AND date BETWEEN ? AND ?
        ORDER BY date ASC
        ''', (from_currency, to_currency, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def fetch_missing_dates(self, from_currency: str, to_currency: str, start_date: datetime, end_date: datetime) -> Optional[List[Tuple[datetime, datetime]]]:
        data = self.fetch_from_db(from_currency, to_currency, start_date, end_date)
        if data:
            available_dates = {datetime.strptime(row['date'], '%Y-%m-%d') for row in data}
            requested_dates = sorted(pd.date_range(start=start_date, end=end_date).to_pydatetime())
            
            # Find contiguous missing date ranges
            missing_ranges = []
            current_range = []
            for date in requested_dates:
                if date not in available_dates:
                    current_range.append(date)
                elif current_range:
                    missing_ranges.append((current_range[0], current_range[-1]))
                    current_range = []
            
            # Add the last range if it exists
            if current_range:
                missing_ranges.append((current_range[0], current_range[-1]))

            return missing_ranges if missing_ranges else None
        return [(start_date, end_date)]

    def get_period_dates(self, period: str) -> Tuple[datetime, datetime]:
        end_date = datetime.now()
        period_map = {
            "1W": timedelta(weeks=1),
            "1M": timedelta(days=30),
            "3M": timedelta(days=90),
            "6M": timedelta(days=180),
            "1Y": timedelta(days=365)
        }
        start_date = end_date - period_map.get(period, timedelta(days=0))
        return start_date, end_date
