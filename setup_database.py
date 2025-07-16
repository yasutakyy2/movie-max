#!/usr/bin/env python3
"""
映画最適化システム データベースセットアップ
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    def __init__(self, db_path: str = "movie_optimization.db"):
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        """データベース接続"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
            logger.info(f"Database connected: {self.db_path}")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """データベース切断"""
        if self.connection:
            self.connection.close()
            logger.info("Database disconnected")
    
    def create_tables(self):
        """テーブル作成"""
        try:
            # スキーマファイルを読み込み
            with open('database_schema.sql', 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # SQLを実行
            cursor = self.connection.cursor()
            cursor.executescript(schema_sql)
            self.connection.commit()
            
            logger.info("Tables created successfully")
            
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            raise
    
    def insert_initial_theaters(self):
        """初期映画館データ挿入"""
        theaters = [
            {
                'name': '新宿ピカデリー',
                'address': '東京都新宿区新宿3-15-15',
                'latitude': 35.6895,
                'longitude': 139.7065,
                'area': 'shinjuku',
                'screens': 11,
                'facilities': json.dumps(['IMAX', 'Dolby Atmos', 'プラチナシート']),
                'url': 'https://eiga.com/theater/13/130201/3017/'
            },
            {
                'name': '新宿バルト9',
                'address': '東京都新宿区新宿3-1-26',
                'latitude': 35.6900,
                'longitude': 139.7050,
                'area': 'shinjuku',
                'screens': 9,
                'facilities': json.dumps(['4DX', 'MX4D']),
                'url': 'https://eiga.com/theater/13/130201/3016/'
            },
            {
                'name': 'TOHOシネマズ新宿',
                'address': '東京都新宿区歌舞伎町1-19-1',
                'latitude': 35.6942,
                'longitude': 139.7033,
                'area': 'shinjuku',
                'screens': 12,
                'facilities': json.dumps(['IMAX', 'TCX', 'Dolby Atmos']),
                'url': 'https://eiga.com/theater/13/130201/3263/'
            },
            {
                'name': 'シネマート新宿',
                'address': '東京都新宿区新宿3-13-3',
                'latitude': 35.6898,
                'longitude': 139.7068,
                'area': 'shinjuku',
                'screens': 7,
                'facilities': json.dumps(['プレミアムシート']),
                'url': 'https://eiga.com/theater/13/130201/3020/'
            },
            {
                'name': '新宿シネマカリテ',
                'address': '東京都新宿区新宿3-37-12',
                'latitude': 35.6885,
                'longitude': 139.7058,
                'area': 'shinjuku',
                'screens': 2,
                'facilities': json.dumps(['アート作品専門']),
                'url': 'https://eiga.com/theater/13/130201/3096/'
            },
            {
                'name': '新宿武蔵野館',
                'address': '東京都新宿区新宿3-27-10',
                'latitude': 35.6888,
                'longitude': 139.7062,
                'area': 'shinjuku',
                'screens': 4,
                'facilities': json.dumps(['クラシック映画館']),
                'url': 'https://eiga.com/theater/13/130201/3026/'
            },
            {
                'name': 'テアトル新宿',
                'address': '東京都新宿区新宿3-14-20',
                'latitude': 35.6892,
                'longitude': 139.7063,
                'area': 'shinjuku',
                'screens': 3,
                'facilities': json.dumps(['単館系']),
                'url': 'https://eiga.com/theater/13/130201/3022/'
            },
            {
                'name': '109シネマズプレミアム新宿',
                'address': '東京都新宿区歌舞伎町1-2-3',
                'latitude': 35.6945,
                'longitude': 139.7028,
                'area': 'shinjuku',
                'screens': 8,
                'facilities': json.dumps(['プレミアムシート', 'グランドシネマサンシャイン']),
                'url': 'https://eiga.com/theater/13/130201/3318/'
            },
            {
                'name': 'kino cinema新宿',
                'address': '東京都新宿区新宿3-35-13',
                'latitude': 35.6882,
                'longitude': 139.7055,
                'area': 'shinjuku',
                'screens': 4,
                'facilities': json.dumps(['独立系', 'アート作品']),
                'url': 'https://eiga.com/theater/13/130201/3322/'
            }
        ]
        
        cursor = self.connection.cursor()
        
        for theater in theaters:
            cursor.execute('''
                INSERT OR REPLACE INTO theaters 
                (name, address, latitude, longitude, area, screens, facilities, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                theater['name'], theater['address'], theater['latitude'],
                theater['longitude'], theater['area'], theater['screens'],
                theater['facilities'], theater['url']
            ))
        
        self.connection.commit()
        logger.info(f"Inserted {len(theaters)} theaters")
    
    def insert_initial_distances(self):
        """初期映画館間距離データ挿入"""
        distances = [
            # 新宿ピカデリー (ID: 1) からの距離
            {'from_id': 1, 'to_id': 2, 'walking': 5, 'train': 0, 'taxi': 3, 'distance': 0.3},
            {'from_id': 1, 'to_id': 3, 'walking': 10, 'train': 0, 'taxi': 5, 'distance': 0.7},
            {'from_id': 1, 'to_id': 4, 'walking': 3, 'train': 0, 'taxi': 2, 'distance': 0.2},
            {'from_id': 1, 'to_id': 5, 'walking': 7, 'train': 0, 'taxi': 4, 'distance': 0.5},
            {'from_id': 1, 'to_id': 6, 'walking': 8, 'train': 0, 'taxi': 4, 'distance': 0.6},
            {'from_id': 1, 'to_id': 7, 'walking': 4, 'train': 0, 'taxi': 3, 'distance': 0.3},
            {'from_id': 1, 'to_id': 8, 'walking': 12, 'train': 0, 'taxi': 6, 'distance': 0.8},
            {'from_id': 1, 'to_id': 9, 'walking': 6, 'train': 0, 'taxi': 3, 'distance': 0.4},
            
            # 新宿バルト9 (ID: 2) からの距離
            {'from_id': 2, 'to_id': 1, 'walking': 5, 'train': 0, 'taxi': 3, 'distance': 0.3},
            {'from_id': 2, 'to_id': 3, 'walking': 8, 'train': 0, 'taxi': 4, 'distance': 0.5},
            {'from_id': 2, 'to_id': 4, 'walking': 6, 'train': 0, 'taxi': 3, 'distance': 0.4},
            {'from_id': 2, 'to_id': 5, 'walking': 9, 'train': 0, 'taxi': 5, 'distance': 0.6},
            {'from_id': 2, 'to_id': 6, 'walking': 10, 'train': 0, 'taxi': 5, 'distance': 0.7},
            {'from_id': 2, 'to_id': 7, 'walking': 7, 'train': 0, 'taxi': 4, 'distance': 0.5},
            {'from_id': 2, 'to_id': 8, 'walking': 10, 'train': 0, 'taxi': 5, 'distance': 0.6},
            {'from_id': 2, 'to_id': 9, 'walking': 8, 'train': 0, 'taxi': 4, 'distance': 0.5},
            
            # TOHOシネマズ新宿 (ID: 3) からの距離
            {'from_id': 3, 'to_id': 1, 'walking': 10, 'train': 0, 'taxi': 5, 'distance': 0.7},
            {'from_id': 3, 'to_id': 2, 'walking': 8, 'train': 0, 'taxi': 4, 'distance': 0.5},
            {'from_id': 3, 'to_id': 4, 'walking': 12, 'train': 0, 'taxi': 6, 'distance': 0.8},
            {'from_id': 3, 'to_id': 5, 'walking': 15, 'train': 0, 'taxi': 7, 'distance': 1.0},
            {'from_id': 3, 'to_id': 6, 'walking': 13, 'train': 0, 'taxi': 6, 'distance': 0.9},
            {'from_id': 3, 'to_id': 7, 'walking': 11, 'train': 0, 'taxi': 5, 'distance': 0.7},
            {'from_id': 3, 'to_id': 8, 'walking': 5, 'train': 0, 'taxi': 3, 'distance': 0.3},
            {'from_id': 3, 'to_id': 9, 'walking': 14, 'train': 0, 'taxi': 7, 'distance': 0.9},
        ]
        
        cursor = self.connection.cursor()
        
        for dist in distances:
            route_info = json.dumps({
                'method': 'walking',
                'description': f"徒歩約{dist['walking']}分"
            })
            
            cursor.execute('''
                INSERT OR REPLACE INTO theater_distances 
                (from_theater_id, to_theater_id, walking_minutes, train_minutes, taxi_minutes, distance_km, route_info)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                dist['from_id'], dist['to_id'], dist['walking'], dist['train'],
                dist['taxi'], dist['distance'], route_info
            ))
        
        self.connection.commit()
        logger.info(f"Inserted {len(distances)} distance records")
    
    def setup_complete_database(self):
        """データベース完全セットアップ"""
        logger.info("Starting database setup...")
        
        # 既存のDBファイルがある場合は削除
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            logger.info("Removed existing database file")
        
        # データベース接続
        self.connect()
        
        try:
            # テーブル作成
            self.create_tables()
            
            # 初期データ挿入
            self.insert_initial_theaters()
            self.insert_initial_distances()
            
            logger.info("Database setup completed successfully!")
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise
        finally:
            self.disconnect()
    
    def show_database_info(self):
        """データベース情報表示"""
        self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            # テーブル一覧
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            print("=" * 60)
            print("データベース情報")
            print("=" * 60)
            print(f"データベースファイル: {self.db_path}")
            print(f"テーブル数: {len(tables)}")
            print()
            
            # 各テーブルのレコード数
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} レコード")
            
            print()
            
            # 映画館一覧
            cursor.execute("SELECT theater_id, name, screens FROM theaters ORDER BY theater_id")
            theaters = cursor.fetchall()
            
            print("=== 映画館一覧 ===")
            for theater in theaters:
                print(f"ID: {theater[0]}, 名前: {theater[1]}, スクリーン数: {theater[2]}")
            
        except Exception as e:
            logger.error(f"Failed to show database info: {e}")
        finally:
            self.disconnect()

def main():
    """メイン実行"""
    setup = DatabaseSetup()
    
    try:
        # データベースセットアップ
        setup.setup_complete_database()
        
        # データベース情報表示
        setup.show_database_info()
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise

if __name__ == "__main__":
    main()