#!/usr/bin/env python3
"""
「中山教頭の人生テスト」の正確な情報を迅速に検索
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time
from typing import Dict, Optional

class QuickNakayamaSearch:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://eiga.com"
        
        # 新宿エリアの主要映画館
        self.theaters = {
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
            'テアトル新宿': {
                'url': 'https://eiga.com/theater/13/130201/3022/',
                'id': '3022',
                'area_id': '13/130201/3022'
            },
            '新宿シネマカリテ': {
                'url': 'https://eiga.com/theater/13/130201/3096/',
                'id': '3096',
                'area_id': '13/130201/3096'
            },
            'kino cinema新宿': {
                'url': 'https://eiga.com/theater/13/130201/3322/',
                'id': '3322',
                'area_id': '13/130201/3322'
            }
        }
    
    def search_movie_in_theater(self, theater_name: str) -> Optional[Dict]:
        """特定の映画館で「中山教頭の人生テスト」を検索"""
        if theater_name not in self.theaters:
            return None
            
        theater_url = self.theaters[theater_name]['url']
        print(f"  {theater_name}で検索中...")
        
        try:
            response = self.session.get(theater_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 映画リンクを探す
            movie_links = soup.find_all('a', href=re.compile(r'/movie/[^/]+/'))
            
            for link in movie_links:
                href = link.get('href')
                if href:
                    # 映画タイトルを取得
                    img_elem = link.find('img')
                    if img_elem and img_elem.get('alt'):
                        title = img_elem.get('alt').strip()
                    else:
                        title = link.get_text(strip=True)
                    
                    # 「中山教頭の人生テスト」を検索
                    if title and ("中山教頭" in title or "人生テスト" in title):
                        print(f"    ✅ 発見: {title}")
                        
                        # 映画IDを抽出
                        movie_id_match = re.search(r'/movie/([^/]+)/', href)
                        if movie_id_match:
                            movie_id = movie_id_match.group(1)
                            
                            # 詳細情報を取得
                            movie_detail_url = f"https://eiga.com/movie-theater/{movie_id}/{self.theaters[theater_name]['area_id']}/"
                            schedule_info = self.get_movie_schedule(movie_detail_url)
                            
                            return {
                                'movie_id': movie_id,
                                'title': title,
                                'theater_name': theater_name,
                                'theater_id': self.theaters[theater_name]['id'],
                                'movie_detail_url': movie_detail_url,
                                'duration': schedule_info['duration'],
                                'showtimes': schedule_info['showtimes'],
                                'image_url': img_elem.get('src', '') if img_elem else ''
                            }
            
            print(f"    映画が見つかりませんでした")
            return None
            
        except Exception as e:
            print(f"    エラー: {e}")
            return None
    
    def get_movie_schedule(self, movie_url: str) -> Dict:
        """映画の上映スケジュールを取得"""
        try:
            response = self.session.get(movie_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 上映時間を取得
            duration = 125  # 既知の情報
            duration_match = re.search(r'(\d+)分', response.text)
            if duration_match:
                duration = int(duration_match.group(1))
            
            # 上映スケジュールを取得
            showtimes = []
            
            # .weekly-schedule テーブルを探す
            weekly_schedule = soup.find('table', class_='weekly-schedule')
            if weekly_schedule:
                for row in weekly_schedule.find_all('tr'):
                    for cell in row.find_all('td'):
                        # 日付を探す
                        date_elem = cell.find('p', class_='date')
                        if date_elem:
                            date_text = date_elem.get_text(strip=True)
                            date_match = re.search(r'(\d{1,2})/(\d{1,2})', date_text)
                            if date_match:
                                month, day = date_match.groups()
                                year = datetime.now().year
                                show_date = f"{year}-{int(month):02d}-{int(day):02d}"
                                
                                # 時間スロットを探す
                                time_elements = cell.find_all(['a', 'span'])
                                for time_elem in time_elements:
                                    time_text = time_elem.get_text(strip=True)
                                    time_match = re.search(r'(\d{1,2}:\d{2})', time_text)
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
                                            'screen': 1,
                                            'price': 2000.0
                                        })
            
            return {
                'duration': duration,
                'showtimes': showtimes
            }
            
        except Exception as e:
            print(f"    スケジュール取得エラー: {e}")
            return {
                'duration': 125,
                'showtimes': []
            }
    
    def find_nakayama_kyoto(self) -> Optional[Dict]:
        """「中山教頭の人生テスト」を検索"""
        print("=== 「中山教頭の人生テスト」検索開始 ===")
        
        for theater_name in self.theaters.keys():
            result = self.search_movie_in_theater(theater_name)
            if result:
                return result
            time.sleep(1)
        
        print("❌ 「中山教頭の人生テスト」が見つかりませんでした")
        return None

def main():
    searcher = QuickNakayamaSearch()
    
    # 「中山教頭の人生テスト」を検索
    nakayama_info = searcher.find_nakayama_kyoto()
    
    if nakayama_info:
        print(f"\n=== 「中山教頭の人生テスト」詳細 ===")
        print(f"映画館: {nakayama_info['theater_name']}")
        print(f"映画ID: {nakayama_info['movie_id']}")
        print(f"上映時間: {nakayama_info['duration']}分")
        print(f"上映回数: {len(nakayama_info['showtimes'])}")
        
        if nakayama_info['showtimes']:
            print(f"上映スケジュール:")
            for i, showtime in enumerate(nakayama_info['showtimes'], 1):
                print(f"  {i}. {showtime['date']} {showtime['start_time']}-{showtime['end_time']}")
        
        # 結果を保存
        with open('nakayama_quick_search.json', 'w', encoding='utf-8') as f:
            json.dump(nakayama_info, f, ensure_ascii=False, indent=2)
        
        print("\n✅ 「中山教頭の人生テスト」の情報を nakayama_quick_search.json に保存しました")
        
        # データベースを更新
        from database_manager import DatabaseManager
        
        with DatabaseManager() as db:
            cursor = db.connection.cursor()
            
            # 映画館IDを取得
            cursor.execute('SELECT theater_id FROM theaters WHERE name = ?', (nakayama_info['theater_name'],))
            theater_result = cursor.fetchone()
            
            if theater_result:
                theater_id = theater_result[0]
                
                # 映画IDを取得
                cursor.execute('SELECT movie_id FROM movies WHERE title = ?', ("中山教頭の人生テスト",))
                movie_result = cursor.fetchone()
                
                if movie_result:
                    movie_id = movie_result[0]
                    
                    # 映画情報を更新
                    cursor.execute('UPDATE movies SET duration = ? WHERE movie_id = ?', 
                                 (nakayama_info['duration'], movie_id))
                    
                    # 既存の上映時間を削除
                    cursor.execute('DELETE FROM showtimes WHERE movie_id = ?', (movie_id,))
                    
                    # 正しい上映時間を追加
                    for showtime in nakayama_info['showtimes']:
                        cursor.execute('''
                            INSERT INTO showtimes (movie_id, theater_id, showtime_date, start_time, end_time, screen_number, price)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (movie_id, theater_id, showtime['date'], showtime['start_time'], 
                              showtime['end_time'], showtime['screen'], showtime['price']))
                    
                    db.connection.commit()
                    print("✅ データベースを更新しました")
                else:
                    print("❌ 映画がデータベースに見つかりません")
            else:
                print("❌ 映画館がデータベースに見つかりません")
    
    else:
        print("\n❌ 「中山教頭の人生テスト」の情報を取得できませんでした")

if __name__ == "__main__":
    main()