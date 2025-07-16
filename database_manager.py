#!/usr/bin/env python3
"""
映画最適化システム データベースマネージャー
"""

import sqlite3
import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "movie_optimization.db"):
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        """データベース接続"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Database connected: {self.db_path}")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """データベース切断"""
        if self.connection:
            self.connection.close()
            logger.info("Database disconnected")
    
    def __enter__(self):
        """コンテキストマネージャー開始"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        self.disconnect()
    
    def get_theaters(self) -> List[Dict]:
        """映画館一覧を取得"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM theaters ORDER BY theater_id")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_theater_by_name(self, name: str) -> Optional[Dict]:
        """映画館名で映画館を取得"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM theaters WHERE name = ?", (name,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    def get_movies(self, limit: int = None) -> List[Dict]:
        """映画一覧を取得"""
        cursor = self.connection.cursor()
        query = "SELECT * FROM movies ORDER BY movie_id"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_movie_by_title(self, title: str) -> Optional[Dict]:
        """映画タイトルで映画を取得"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM movies WHERE title = ?", (title,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    def get_showtimes(self, date: str = None, theater_id: int = None, movie_id: int = None) -> List[Dict]:
        """上映スケジュールを取得"""
        cursor = self.connection.cursor()
        query = """
            SELECT s.*, t.name as theater_name, m.title as movie_title, m.image_url
            FROM showtimes s
            JOIN theaters t ON s.theater_id = t.theater_id
            JOIN movies m ON s.movie_id = m.movie_id
            WHERE 1=1
        """
        params = []
        
        if date:
            query += " AND s.show_date = ?"
            params.append(date)
        
        if theater_id:
            query += " AND s.theater_id = ?"
            params.append(theater_id)
        
        if movie_id:
            query += " AND s.movie_id = ?"
            params.append(movie_id)
        
        query += " ORDER BY s.show_date, s.start_time"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_19h_showtimes(self, date: str = "2025-07-14") -> List[Dict]:
        """19時台の上映スケジュールを取得"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT s.*, t.name as theater_name, m.title as movie_title
            FROM showtimes s
            JOIN theaters t ON s.theater_id = t.theater_id
            JOIN movies m ON s.movie_id = m.movie_id
            WHERE s.show_date = ? AND s.start_time >= '19:00' AND s.start_time < '20:00'
            ORDER BY s.start_time
        """, (date,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_theater_distances(self, from_theater_id: int = None, to_theater_id: int = None) -> List[Dict]:
        """映画館間距離を取得"""
        cursor = self.connection.cursor()
        query = """
            SELECT d.*, t1.name as from_theater_name, t2.name as to_theater_name
            FROM theater_distances d
            JOIN theaters t1 ON d.from_theater_id = t1.theater_id
            JOIN theaters t2 ON d.to_theater_id = t2.theater_id
            WHERE 1=1
        """
        params = []
        
        if from_theater_id:
            query += " AND d.from_theater_id = ?"
            params.append(from_theater_id)
        
        if to_theater_id:
            query += " AND d.to_theater_id = ?"
            params.append(to_theater_id)
        
        query += " ORDER BY d.from_theater_id, d.to_theater_id"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_travel_time(self, from_theater_id: int, to_theater_id: int) -> Optional[int]:
        """2つの映画館間の移動時間を取得（徒歩）"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT walking_minutes FROM theater_distances
            WHERE from_theater_id = ? AND to_theater_id = ?
        """, (from_theater_id, to_theater_id))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def insert_or_update_movie(self, title: str, duration: int = 120, rating: str = "G", 
                             genre: List[str] = None, description: str = "") -> int:
        """映画を挿入または更新"""
        cursor = self.connection.cursor()
        
        # 既存チェック
        cursor.execute("SELECT movie_id FROM movies WHERE title = ?", (title,))
        result = cursor.fetchone()
        
        if result:
            # 既存の映画を更新
            movie_id = result[0]
            cursor.execute("""
                UPDATE movies SET duration = ?, rating = ?, genre = ?, description = ?, updated_at = ?
                WHERE movie_id = ?
            """, (duration, rating, json.dumps(genre or []), description, datetime.now().isoformat(), movie_id))
        else:
            # 新しい映画を挿入
            cursor.execute("""
                INSERT INTO movies (title, duration, rating, genre, description, release_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, duration, rating, json.dumps(genre or []), description, "2025-07-14"))
            movie_id = cursor.lastrowid
        
        return movie_id
    
    def insert_or_update_showtime(self, theater_id: int, movie_id: int, show_date: str, 
                                start_time: str, screen_number: int = 1, price: float = 2000.0) -> int:
        """上映スケジュールを挿入または更新"""
        cursor = self.connection.cursor()
        
        # 映画の長さを取得
        cursor.execute("SELECT duration FROM movies WHERE movie_id = ?", (movie_id,))
        duration = cursor.fetchone()[0]
        
        # 終了時間を計算
        start_datetime = datetime.strptime(f"{show_date} {start_time}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + timedelta(minutes=duration)
        end_time = end_datetime.strftime("%H:%M")
        
        # 重複チェック
        cursor.execute("""
            SELECT showtime_id FROM showtimes 
            WHERE theater_id = ? AND show_date = ? AND start_time = ? AND screen_number = ?
        """, (theater_id, show_date, start_time, screen_number))
        
        result = cursor.fetchone()
        
        if result:
            # 既存の上映時間を更新
            showtime_id = result[0]
            cursor.execute("""
                UPDATE showtimes SET movie_id = ?, end_time = ?, price = ?, updated_at = ?
                WHERE showtime_id = ?
            """, (movie_id, end_time, price, datetime.now().isoformat(), showtime_id))
        else:
            # 新しい上映時間を挿入
            cursor.execute("""
                INSERT INTO showtimes (theater_id, movie_id, show_date, start_time, end_time, screen_number, price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (theater_id, movie_id, show_date, start_time, end_time, screen_number, price))
            showtime_id = cursor.lastrowid
        
        return showtime_id
    
    def clear_showtimes(self, date: str = None):
        """上映スケジュールをクリア"""
        cursor = self.connection.cursor()
        if date:
            cursor.execute("DELETE FROM showtimes WHERE show_date = ?", (date,))
        else:
            cursor.execute("DELETE FROM showtimes")
        self.connection.commit()
        logger.info(f"Cleared showtimes for date: {date if date else 'all'}")
    
    def import_schedule_data(self, json_file_path: str) -> Dict:
        """スケジュールデータをインポート"""
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        try:
            # 既存のデータをクリア
            self.clear_showtimes(data['metadata']['target_date'])
            
            imported_movies = set()
            imported_showtimes = 0
            
            for schedule_item in data['schedule']:
                # 映画タイトルをクリーニング
                title = self.clean_movie_title(schedule_item['title'])
                if title == "不明" or len(title) < 2:
                    continue
                
                # 映画館を取得
                theater = self.get_theater_by_name(schedule_item['theater_name'])
                if not theater:
                    logger.warning(f"Theater not found: {schedule_item['theater_name']}")
                    continue
                
                # 映画を挿入/更新
                movie_id = self.insert_or_update_movie(title)
                imported_movies.add(title)
                
                # スクリーン番号をランダムに割り当て
                screen_number = random.randint(1, theater['screens'])
                
                # 上映時間を挿入/更新
                showtime_id = self.insert_or_update_showtime(
                    theater['theater_id'], movie_id, schedule_item['date'], 
                    schedule_item['start_time'], screen_number
                )
                
                if showtime_id:
                    imported_showtimes += 1
            
            self.connection.commit()
            
            result = {
                'imported_movies': len(imported_movies),
                'imported_showtimes': imported_showtimes,
                'source_file': json_file_path,
                'target_date': data['metadata']['target_date']
            }
            
            logger.info(f"Import completed: {result}")
            return result
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Import failed: {e}")
            raise
    
    def clean_movie_title(self, title: str) -> str:
        """映画タイトルをクリーニング"""
        import re
        
        # 不要な文字列を除去
        title = re.sub(r'コピー\s*印刷\s*すべてのスケジュールを見る', '', title)
        title = re.sub(r'\d+:\d+.*$', '', title)
        title = re.sub(r'^\d+:\d+\s*', '', title)
        title = title.strip()
        
        # 空の場合や短すぎる場合は「不明」
        if not title or len(title) < 2:
            return "不明"
        
        return title
    
    def get_database_stats(self) -> Dict:
        """データベース統計情報を取得"""
        cursor = self.connection.cursor()
        
        stats = {}
        
        # 各テーブルのレコード数
        tables = ['theaters', 'movies', 'showtimes', 'theater_distances', 'viewing_plans', 'plan_recommendations']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        # 19時台の上映数
        cursor.execute("SELECT COUNT(*) FROM showtimes WHERE start_time >= '19:00' AND start_time < '20:00'")
        stats['showtimes_19h'] = cursor.fetchone()[0]
        
        # 日付別上映数
        cursor.execute("SELECT show_date, COUNT(*) FROM showtimes GROUP BY show_date")
        stats['showtimes_by_date'] = dict(cursor.fetchall())
        
        return stats
    
    def get_or_create_theater(self, theater_name: str, location: str = "", prefecture: str = "") -> int:
        """映画館を取得または新規作成して、IDを返す"""
        cursor = self.connection.cursor()
        
        # 既存の映画館を検索（正しいカラム名を使用）
        cursor.execute("SELECT theater_id FROM theaters WHERE name = ?", (theater_name,))
        existing = cursor.fetchone()
        
        if existing:
            return existing[0]
        
        # 新規作成（正しいカラム名を使用）
        cursor.execute("""
            INSERT INTO theaters (name, address, area) 
            VALUES (?, ?, ?)
        """, (theater_name, location or "新宿区", prefecture or "東京都"))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def get_or_create_movie(self, movie_title: str, duration: int = 120, genre: str = "") -> int:
        """映画を取得または新規作成して、IDを返す"""
        cursor = self.connection.cursor()
        
        # 既存の映画を検索
        cursor.execute("SELECT movie_id FROM movies WHERE title = ?", (movie_title,))
        existing = cursor.fetchone()
        
        if existing:
            return existing[0]
        
        # 新規作成
        cursor.execute("""
            INSERT INTO movies (title, duration, genre) 
            VALUES (?, ?, ?)
        """, (movie_title, duration, genre))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def add_showtime(self, movie_id: int, theater_id: int, date: str, 
                    start_time: str, end_time: str, screen_number: int = 1, 
                    price: int = 1500) -> Optional[int]:
        """上映情報を追加"""
        cursor = self.connection.cursor()
        
        try:
            # 重複チェック（同じ映画館、同じ日時、同じ映画）
            cursor.execute("""
                SELECT showtime_id FROM showtimes 
                WHERE movie_id = ? AND theater_id = ? AND show_date = ? AND start_time = ?
            """, (movie_id, theater_id, date, start_time))
            
            existing = cursor.fetchone()
            if existing:
                logger.debug(f"Showtime already exists: {existing[0]}")
                return existing[0]
            
            # 新規追加
            cursor.execute("""
                INSERT INTO showtimes (movie_id, theater_id, show_date, start_time, end_time, 
                                     screen_number, price) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (movie_id, theater_id, date, start_time, end_time, screen_number, price))
            
            self.connection.commit()
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Failed to add showtime: {e}")
            return None

def main():
    """メイン実行とテスト"""
    db_manager = DatabaseManager()
    
    try:
        with db_manager:
            # 最新のクローリングデータを検索
            json_files = [f for f in os.listdir('.') if f.startswith('final_schedule_') and f.endswith('.json')]
            if not json_files:
                logger.error("No crawling data files found")
                return
            
            latest_file = sorted(json_files)[-1]
            logger.info(f"Importing from: {latest_file}")
            
            # データをインポート
            result = db_manager.import_schedule_data(latest_file)
            
            print("=" * 60)
            print("データインポート結果")
            print("=" * 60)
            print(f"インポート映画数: {result['imported_movies']}")
            print(f"インポート上映回数: {result['imported_showtimes']}")
            print(f"対象日: {result['target_date']}")
            print(f"ソースファイル: {result['source_file']}")
            
            # 統計情報を表示
            stats = db_manager.get_database_stats()
            print("\n=== データベース統計 ===")
            for key, value in stats.items():
                if key != 'showtimes_by_date':
                    print(f"{key}: {value}")
            
            # 19時台の上映を表示
            showtimes_19h = db_manager.get_19h_showtimes()
            print(f"\n=== 19時台の上映 ({len(showtimes_19h)} 件) ===")
            for showtime in showtimes_19h:
                print(f"{showtime['start_time']} | {showtime['movie_title']} | {showtime['theater_name']}")
            
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        raise

if __name__ == "__main__":
    main()