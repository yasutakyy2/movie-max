#!/usr/bin/env python3
"""
映画.comから新宿エリア映画館の完全なクローリングシステム
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time
import sqlite3
from database_manager import DatabaseManager
from typing import Dict, List, Optional

class CompleteEigaCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://eiga.com"
        
        # 正しいURL構造で映画館情報を更新
        self.theaters = {
            '新宿ピカデリー': {
                'url': 'https://eiga.com/theater/13/130201/3017/',
                'id': '3017',
                'area_id': '13/130201/3017'
            },
            'テアトル新宿': {
                'url': 'https://eiga.com/theater/13/130201/3022/',
                'id': '3022',
                'area_id': '13/130201/3022'
            },
            '新宿武蔵野館': {
                'url': 'https://eiga.com/theater/13/130201/3026/',
                'id': '3026',
                'area_id': '13/130201/3026'
            },
            'シネマート新宿': {
                'url': 'https://eiga.com/theater/13/130201/3020/',
                'id': '3020',
                'area_id': '13/130201/3020'
            },
            'kino cinema新宿': {
                'url': 'https://eiga.com/theater/13/130201/3322/',
                'id': '3322',
                'area_id': '13/130201/3322'
            },
            'Ks cinema': {
                'url': 'https://eiga.com/theater/13/130201/3018/',
                'id': '3018',
                'area_id': '13/130201/3018'
            },
            '新宿シネマカリテ': {
                'url': 'https://eiga.com/theater/13/130201/3096/',
                'id': '3096',
                'area_id': '13/130201/3096'
            },
            '新宿バルト9': {
                'url': 'https://eiga.com/theater/13/130201/3016/',
                'id': '3016',
                'area_id': '13/130201/3016'
            },
            'TOHOシネマズ新宿': {
                'url': 'https://eiga.com/theater/13/130201/3263/',
                'id': '3263',
                'area_id': '13/130201/3263'
            },
            '109シネマズプレミアム新宿': {
                'url': 'https://eiga.com/theater/13/130201/3318/',
                'id': '3318',
                'area_id': '13/130201/3318'
            }
        }
    
    def get_theater_movies(self, theater_name: str) -> List[Dict]:
        """映画館の上映中映画一覧を取得"""
        if theater_name not in self.theaters:
            return []
        
        theater_url = self.theaters[theater_name]['url']
        
        try:
            response = self.session.get(theater_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            movies = []
            
            # 映画リンクを探す
            movie_links = soup.find_all('a', href=re.compile(r'/movie/[^/]+/'))
            
            for link in movie_links:
                href = link.get('href')
                if href:
                    # 映画IDを抽出
                    movie_id_match = re.search(r'/movie/([^/]+)/', href)
                    if movie_id_match:
                        movie_id = movie_id_match.group(1)
                        
                        # 映画タイトルを取得
                        img_elem = link.find('img')
                        if img_elem and img_elem.get('alt'):
                            title = img_elem.get('alt').strip()
                        else:
                            title = link.get_text(strip=True)
                        
                        if title and len(title) > 1:
                            movies.append({
                                'movie_id': movie_id,
                                'title': title,
                                'theater_name': theater_name,
                                'theater_id': self.theaters[theater_name]['id'],
                                'image_url': img_elem.get('src', '') if img_elem else ''
                            })
            
            # 重複を除去
            unique_movies = {}
            for movie in movies:
                if movie['movie_id'] not in unique_movies:
                    unique_movies[movie['movie_id']] = movie
            
            return list(unique_movies.values())
            
        except Exception as e:
            print(f"Error getting movies for {theater_name}: {e}")
            return []
    
    def get_movie_schedule(self, movie_id: str, theater_name: str) -> List[Dict]:
        """特定の映画の上映スケジュールを取得"""
        if theater_name not in self.theaters:
            return []
        
        movie_url = f"https://eiga.com/movie-theater/{movie_id}/{self.theaters[theater_name]['area_id']}/"
        
        try:
            response = self.session.get(movie_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 映画の基本情報を取得
            title_elem = soup.find('h1') or soup.find('h2')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # 上映時間を取得
            duration = 120  # デフォルト値
            duration_patterns = [
                r'(\\d+)分',
                r'上映時間[：:]\\s*(\\d+)分'
            ]
            
            for pattern in duration_patterns:
                duration_match = re.search(pattern, response.text)
                if duration_match:
                    duration = int(duration_match.group(1))
                    break
            
            # 上映スケジュールを取得
            showtimes = []
            
            # .weekly-schedule テーブルを探す
            weekly_schedule = soup.find('table', class_='weekly-schedule')
            if weekly_schedule:
                # 日付とタイムスロットを解析
                for row in weekly_schedule.find_all('tr'):
                    for cell in row.find_all('td'):
                        # 日付を探す
                        date_elem = cell.find('p', class_='date')
                        if date_elem:
                            date_text = date_elem.get_text(strip=True)
                            date_match = re.search(r'(\\d{1,2})/(\\d{1,2})', date_text)
                            if date_match:
                                month, day = date_match.groups()
                                year = datetime.now().year
                                show_date = f"{year}-{int(month):02d}-{int(day):02d}"
                                
                                # 時間スロットを探す
                                time_elements = cell.find_all(['a', 'span'])
                                for time_elem in time_elements:
                                    time_text = time_elem.get_text(strip=True)
                                    time_match = re.search(r'(\\d{1,2}:\\d{2})', time_text)
                                    if time_match:
                                        start_time = time_match.group(1)
                                        
                                        # 終了時間を計算
                                        start_hour, start_min = map(int, start_time.split(':'))
                                        end_minutes = start_hour * 60 + start_min + duration
                                        end_hour = end_minutes // 60
                                        end_min = end_minutes % 60
                                        end_time = f"{end_hour:02d}:{end_min:02d}"
                                        
                                        showtimes.append({
                                            'date': show_date,
                                            'start_time': start_time,
                                            'end_time': end_time,
                                            'screen': 1,  # デフォルト値
                                            'price': 2000.0  # デフォルト値
                                        })
            
            return {
                'title': title,
                'duration': duration,
                'showtimes': showtimes
            }
            
        except Exception as e:
            print(f"Error getting schedule for movie {movie_id}: {e}")
            return {
                'title': 'Unknown',
                'duration': 120,
                'showtimes': []
            }
    
    def crawl_all_theaters(self) -> Dict:
        """全ての新宿エリア映画館をクローリング"""
        print("=== 映画.com 新宿エリア完全クローリング開始 ===")
        
        all_data = {
            'theaters': [],
            'movies': [],
            'showtimes': []
        }
        
        theater_id_counter = 1
        movie_id_counter = 1
        showtime_id_counter = 1
        movie_title_to_id = {}
        
        for theater_name in self.theaters.keys():
            print(f"\\n--- {theater_name} ---")
            
            # 映画館情報
            theater_info = {
                'theater_id': theater_id_counter,
                'name': theater_name,
                'area': 'shinjuku',
                'address': f'東京都新宿区（{theater_name}）',
                'eiga_com_id': self.theaters[theater_name]['id']
            }
            all_data['theaters'].append(theater_info)
            
            try:
                # 映画館の映画一覧を取得
                movies = self.get_theater_movies(theater_name)
                print(f"  映画数: {len(movies)}")
                
                for movie in movies:
                    # 映画の詳細スケジュールを取得
                    schedule_info = self.get_movie_schedule(movie['movie_id'], theater_name)
                    
                    # 映画情報を追加
                    if movie['title'] not in movie_title_to_id:
                        movie_info = {
                            'movie_id': movie_id_counter,
                            'title': movie['title'],
                            'duration': schedule_info['duration'],
                            'image_url': movie['image_url'],
                            'eiga_com_id': movie['movie_id']
                        }
                        all_data['movies'].append(movie_info)
                        movie_title_to_id[movie['title']] = movie_id_counter
                        movie_id_counter += 1
                    
                    # 上映時間を追加
                    current_movie_id = movie_title_to_id[movie['title']]
                    for showtime in schedule_info['showtimes']:
                        showtime_info = {
                            'showtime_id': showtime_id_counter,
                            'movie_id': current_movie_id,
                            'theater_id': theater_id_counter,
                            'showtime_date': showtime['date'],
                            'start_time': showtime['start_time'],
                            'end_time': showtime['end_time'],
                            'screen_number': showtime['screen'],
                            'price': showtime['price']
                        }
                        all_data['showtimes'].append(showtime_info)
                        showtime_id_counter += 1
                    
                    print(f"    {movie['title']}: {len(schedule_info['showtimes'])}回上映")
                    time.sleep(1)  # リクエスト間隔
                
            except Exception as e:
                print(f"  Error processing {theater_name}: {e}")
            
            theater_id_counter += 1
            time.sleep(2)  # 映画館間の間隔
        
        return all_data
    
    def update_database(self, crawled_data: Dict):
        """データベースを更新"""
        print("\\n=== データベース更新開始 ===")
        
        with DatabaseManager() as db:
            cursor = db.connection.cursor()
            
            # 既存の新宿エリアデータを削除
            cursor.execute('DELETE FROM theaters WHERE area = "shinjuku"')
            cursor.execute('DELETE FROM theater_distances')
            
            # 映画館データを挿入
            for theater in crawled_data['theaters']:
                cursor.execute('''
                    INSERT OR REPLACE INTO theaters (theater_id, name, address, area, screen_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (theater['theater_id'], theater['name'], theater['address'], theater['area'], 10))
            
            print(f"映画館データ: {len(crawled_data['theaters'])}件")
            
            # 映画データを挿入
            for movie in crawled_data['movies']:
                cursor.execute('''
                    INSERT OR REPLACE INTO movies (movie_id, title, duration, image_url)
                    VALUES (?, ?, ?, ?)
                ''', (movie['movie_id'], movie['title'], movie['duration'], movie['image_url']))
            
            print(f"映画データ: {len(crawled_data['movies'])}件")
            
            # 上映時間データを挿入
            for showtime in crawled_data['showtimes']:
                cursor.execute('''
                    INSERT OR REPLACE INTO showtimes (showtime_id, movie_id, theater_id, showtime_date, start_time, end_time, screen_number, price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (showtime['showtime_id'], showtime['movie_id'], showtime['theater_id'], 
                      showtime['showtime_date'], showtime['start_time'], showtime['end_time'], 
                      showtime['screen_number'], showtime['price']))
            
            print(f"上映時間データ: {len(crawled_data['showtimes'])}件")
            
            db.connection.commit()
            print("✅ データベース更新完了")
    
    def find_nakayama_kyoto(self) -> Optional[Dict]:
        """「中山教頭の人生テスト」の正確な情報を検索"""
        print("\\n=== 「中山教頭の人生テスト」検索 ===")
        
        for theater_name in self.theaters.keys():
            print(f"  {theater_name}で検索中...")
            movies = self.get_theater_movies(theater_name)
            
            for movie in movies:
                if "中山教頭" in movie['title'] or "人生テスト" in movie['title']:
                    print(f"✅ 発見: {movie['title']} @ {theater_name}")
                    
                    # 詳細スケジュールを取得
                    schedule = self.get_movie_schedule(movie['movie_id'], theater_name)
                    
                    result = {
                        'movie_id': movie['movie_id'],
                        'title': movie['title'],
                        'theater_name': theater_name,
                        'theater_id': self.theaters[theater_name]['id'],
                        'duration': schedule['duration'],
                        'showtimes': schedule['showtimes'],
                        'image_url': movie['image_url']
                    }
                    
                    print(f"  上映時間: {schedule['duration']}分")
                    print(f"  上映スケジュール: {len(schedule['showtimes'])}件")
                    for showtime in schedule['showtimes']:
                        print(f"    {showtime['date']} {showtime['start_time']}-{showtime['end_time']}")
                    
                    return result
            
            time.sleep(1)
        
        print("❌ 「中山教頭の人生テスト」が見つかりませんでした")
        return None

def main():
    crawler = CompleteEigaCrawler()
    
    # 1. 「中山教頭の人生テスト」の正確な情報を検索
    nakayama_info = crawler.find_nakayama_kyoto()
    
    if nakayama_info:
        print(f"\\n=== 「中山教頭の人生テスト」詳細 ===")
        print(f"映画館: {nakayama_info['theater_name']}")
        print(f"上映時間: {nakayama_info['duration']}分")
        print(f"上映回数: {len(nakayama_info['showtimes'])}")
        
        # 結果を保存
        with open('nakayama_final_info.json', 'w', encoding='utf-8') as f:
            json.dump(nakayama_info, f, ensure_ascii=False, indent=2)
        
        print("✅ 「中山教頭の人生テスト」の情報を保存しました")
    
    # 2. 全映画館の完全クローリング
    print("\\n=== 全映画館クローリング開始 ===")
    crawled_data = crawler.crawl_all_theaters()
    
    # 3. データベースを更新
    crawler.update_database(crawled_data)
    
    # 4. 結果を保存
    with open('complete_theater_data.json', 'w', encoding='utf-8') as f:
        json.dump(crawled_data, f, ensure_ascii=False, indent=2)
    
    print("\\n=== クローリング完了 ===")
    print(f"映画館数: {len(crawled_data['theaters'])}")
    print(f"映画数: {len(crawled_data['movies'])}")
    print(f"上映時間数: {len(crawled_data['showtimes'])}")
    print("✅ 全データをcomplete_theater_data.jsonに保存しました")

if __name__ == "__main__":
    main()