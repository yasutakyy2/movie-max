#!/usr/bin/env python3
"""
映画最適化API - 最適化アルゴリズムの統合インターフェース
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from database_manager import DatabaseManager
from enhanced_optimizer import EnhancedOptimizer, ViewingPlan, MovieShowtime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MovieOptimizationAPI:
    def __init__(self, db_path: str = "movie_optimization.db"):
        self.db_path = db_path
        self.optimizer = EnhancedOptimizer(db_path)
    
    def get_available_movies(self, date: str = "2025-07-14", 
                           time_from: str = "19:00", 
                           time_to: str = "20:00") -> List[Dict]:
        """利用可能な映画を検索（入力時間範囲内に厳密に制限）"""
        with DatabaseManager(self.db_path) as db:
            showtimes = db.get_showtimes(date=date)
            
            # 時間でフィルタリング（開始時間が範囲内で、終了時間も範囲内の映画のみ）
            filtered_showtimes = []
            for showtime in showtimes:
                # 開始時間が範囲内かつ終了時間も範囲内の映画のみ
                if (time_from <= showtime['start_time'] and 
                    showtime['end_time'] <= time_to):
                    filtered_showtimes.append(showtime)
            
            # 映画情報を付加
            movies = []
            for showtime in filtered_showtimes:
                movie_info = {
                    "showtime_id": showtime['showtime_id'],
                    "movie_title": showtime['movie_title'],
                    "theater_name": showtime['theater_name'],
                    "start_time": showtime['start_time'],
                    "end_time": showtime['end_time'],
                    "price": showtime['price'],
                    "screen_number": showtime['screen_number'],
                    "show_date": showtime['show_date'],
                    "image_url": showtime.get('image_url', ''),
                    "duration": showtime.get('duration', 120)
                }
                movies.append(movie_info)
            
            return movies
    
    def optimize_plan(self, showtime_id: int, 
                     max_travel_time: int = 30,
                     buffer_time: int = 15,
                     plan_type: str = "all",
                     max_total_duration: int = 480,
                     time_from: str = "19:00",
                     time_to: str = "22:00") -> Dict:
        """プランを最適化（時間制約を厳密に適用）"""
        try:
            # 最適化を実行
            plans = self.optimizer.optimize_movie_plan(showtime_id, plan_type, time_from, time_to)
            
            # 時間制約に基づいてプランをフィルタリング
            from datetime import datetime
            time_from_minutes = self._time_to_minutes(time_from)
            time_to_minutes = self._time_to_minutes(time_to)
            available_duration = time_to_minutes - time_from_minutes
            
            # 結果を辞書形式に変換
            result_plans = []
            for plan in plans:
                # プランの実際の開始時間と終了時間を計算
                earliest_start = plan.primary_showtime.start_time
                latest_end = plan.primary_showtime.end_time
                
                if plan.before_showtime:
                    earliest_start = plan.before_showtime.start_time
                if plan.after_showtime:
                    latest_end = plan.after_showtime.end_time
                
                # 時間制約チェック
                plan_start_minutes = self._time_to_minutes(earliest_start)
                plan_end_minutes = self._time_to_minutes(latest_end)
                
                # プランが時間範囲内に収まるかチェック（厳密）
                if (plan_start_minutes >= time_from_minutes and 
                    plan_end_minutes <= time_to_minutes):
                    
                    # 総所要時間もチェック
                    if plan.total_duration_minutes <= available_duration:
                        
                        # 個別の映画も時間制約チェック
                        valid_plan = True
                        
                        # プライマリ映画チェック
                        if not (time_from <= plan.primary_showtime.start_time and 
                                plan.primary_showtime.end_time <= time_to):
                            valid_plan = False
                        
                        # 前映画チェック
                        if plan.before_showtime and not (time_from <= plan.before_showtime.start_time and 
                                                        plan.before_showtime.end_time <= time_to):
                            valid_plan = False
                        
                        # 後映画チェック
                        if plan.after_showtime and not (time_from <= plan.after_showtime.start_time and 
                                                       plan.after_showtime.end_time <= time_to):
                            valid_plan = False
                        
                        if not valid_plan:
                            continue
                        plan_dict = {
                            "plan_id": plan.plan_id,
                            "plan_type": plan.plan_type,
                            "optimization_score": plan.optimization_score,
                            "total_duration_minutes": plan.total_duration_minutes,
                            "total_travel_minutes": plan.total_travel_minutes,
                            "total_movie_minutes": plan.total_movie_minutes,
                            "primary_showtime": {
                                "showtime_id": plan.primary_showtime.showtime_id,
                                "movie_title": plan.primary_showtime.movie_title,
                                "theater_name": plan.primary_showtime.theater_name,
                                "start_time": plan.primary_showtime.start_time,
                                "end_time": plan.primary_showtime.end_time,
                                "price": plan.primary_showtime.price,
                                "duration": plan.primary_showtime.duration
                            },
                            "before_showtime": None,
                            "after_showtime": None,
                            "travel_details": plan.travel_details
                        }
                        
                        if plan.before_showtime:
                            plan_dict["before_showtime"] = {
                                "showtime_id": plan.before_showtime.showtime_id,
                                "movie_title": plan.before_showtime.movie_title,
                                "theater_name": plan.before_showtime.theater_name,
                                "start_time": plan.before_showtime.start_time,
                                "end_time": plan.before_showtime.end_time,
                                "price": plan.before_showtime.price,
                                "duration": plan.before_showtime.duration
                            }
                        
                        if plan.after_showtime:
                            plan_dict["after_showtime"] = {
                                "showtime_id": plan.after_showtime.showtime_id,
                                "movie_title": plan.after_showtime.movie_title,
                                "theater_name": plan.after_showtime.theater_name,
                                "start_time": plan.after_showtime.start_time,
                                "end_time": plan.after_showtime.end_time,
                                "price": plan.after_showtime.price,
                                "duration": plan.after_showtime.duration
                            }
                        
                        result_plans.append(plan_dict)
            
            # 最高スコアのプランを保存
            if result_plans:
                best_plan = plans[0]
                plan_id = self.optimizer.save_plan_to_database(best_plan)
                logger.info(f"Best plan saved with ID: {plan_id}")
            
            return {
                "success": True,
                "plans": result_plans,
                "total_plans": len(result_plans),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "plans": [],
                "total_plans": 0,
                "generated_at": datetime.now().isoformat()
            }
    
    def _time_to_minutes(self, time_str: str) -> int:
        """時刻文字列を分に変換"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def get_crawling_status(self) -> Dict:
        """クローリング状況を取得"""
        with DatabaseManager(self.db_path) as db:
            cursor = db.connection.cursor()
            
            # 映画館別のクローリング状況
            cursor.execute('''
                SELECT theater_name, last_crawled, total_movies, success_count, failure_count
                FROM crawling_status
                ORDER BY theater_id
            ''')
            theaters = cursor.fetchall()
            
            # 全体統計
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_theaters,
                    SUM(total_movies) as total_movies,
                    SUM(success_count) as total_success,
                    SUM(failure_count) as total_failures,
                    MIN(last_crawled) as oldest_crawl,
                    MAX(last_crawled) as newest_crawl
                FROM crawling_status
            ''')
            stats = cursor.fetchone()
            
            # 成功率計算
            total_attempts = stats[2] + stats[3] if stats[2] and stats[3] else 1
            success_rate = (stats[2] / total_attempts * 100) if total_attempts > 0 else 0
            
            theater_status = []
            for theater_name, last_crawled, total_movies, success_count, failure_count in theaters:
                theater_attempts = success_count + failure_count if success_count and failure_count else 1
                theater_success_rate = (success_count / theater_attempts * 100) if theater_attempts > 0 else 0
                
                theater_status.append({
                    "theater_name": theater_name,
                    "last_crawled": last_crawled,
                    "total_movies": total_movies or 0,
                    "success_rate": round(theater_success_rate, 1),
                    "status": "active" if total_movies > 0 else "inactive"
                })
            
            return {
                "success": True,
                "overall_stats": {
                    "total_theaters": stats[0],
                    "total_movies": stats[1] or 0,
                    "success_rate": round(success_rate, 1),
                    "oldest_crawl": stats[4],
                    "newest_crawl": stats[5]
                },
                "theater_status": theater_status,
                "data_freshness": "recent" if success_rate > 80 else "outdated"
            }
    
    def get_plan_details(self, plan_id: int) -> Dict:
        """プランの詳細を取得"""
        with DatabaseManager(self.db_path) as db:
            cursor = db.connection.cursor()
            cursor.execute("""
                SELECT * FROM viewing_plans WHERE plan_id = ?
            """, (plan_id,))
            
            result = cursor.fetchone()
            if not result:
                return {
                    "success": False,
                    "error": "Plan not found",
                    "plan": None
                }
            
            plan_data = json.loads(result['plan_data'])
            
            return {
                "success": True,
                "plan": {
                    "plan_id": result['plan_id'],
                    "plan_type": result['plan_type'],
                    "optimization_score": result['optimization_score'],
                    "total_duration_minutes": result['total_duration_minutes'],
                    "total_travel_minutes": result['total_travel_minutes'],
                    "plan_data": plan_data,
                    "created_at": result['created_at']
                }
            }
    
    def get_theater_distances(self) -> List[Dict]:
        """映画館間距離を取得"""
        with DatabaseManager(self.db_path) as db:
            distances = db.get_theater_distances()
            return distances
    
    def get_database_stats(self) -> Dict:
        """データベース統計情報を取得"""
        with DatabaseManager(self.db_path) as db:
            stats = db.get_database_stats()
            return stats
    
    def calculate_optimization_metrics(self, plans: List[Dict]) -> Dict:
        """最適化メトリクスを計算"""
        if not plans:
            return {
                "average_score": 0,
                "best_score": 0,
                "worst_score": 0,
                "total_plans": 0,
                "plan_types": {}
            }
        
        scores = [plan['optimization_score'] for plan in plans]
        plan_types = {}
        
        for plan in plans:
            plan_type = plan['plan_type']
            if plan_type not in plan_types:
                plan_types[plan_type] = 0
            plan_types[plan_type] += 1
        
        return {
            "average_score": sum(scores) / len(scores),
            "best_score": max(scores),
            "worst_score": min(scores),
            "total_plans": len(plans),
            "plan_types": plan_types
        }

def main():
    """APIのテスト実行"""
    api = MovieOptimizationAPI()
    
    print("=== 映画最適化API テスト ===")
    
    # 1. 利用可能な映画を取得
    print("\n1. 利用可能な映画を取得")
    movies = api.get_available_movies()
    print(f"利用可能な映画: {len(movies)}件")
    
    for i, movie in enumerate(movies[:5], 1):
        print(f"  {i}. {movie['start_time']} | {movie['movie_title']} | {movie['theater_name']}")
    
    if not movies:
        print("利用可能な映画がありません")
        return
    
    # 2. 最適化を実行
    print("\n2. 最適化を実行")
    target_movie = movies[0]
    result = api.optimize_plan(target_movie['showtime_id'])
    
    if result['success']:
        print(f"最適化成功: {result['total_plans']}件のプラン生成")
        
        for i, plan in enumerate(result['plans'], 1):
            print(f"\n  プラン {i}:")
            print(f"    タイプ: {plan['plan_type']}")
            print(f"    スコア: {plan['optimization_score']:.2f}")
            print(f"    総時間: {plan['total_duration_minutes']}分")
            print(f"    移動時間: {plan['total_travel_minutes']}分")
            print(f"    メイン映画: {plan['primary_showtime']['movie_title']} ({plan['primary_showtime']['start_time']})")
            
            if plan['before_showtime']:
                print(f"    前映画: {plan['before_showtime']['movie_title']} ({plan['before_showtime']['start_time']})")
            
            if plan['after_showtime']:
                print(f"    後映画: {plan['after_showtime']['movie_title']} ({plan['after_showtime']['start_time']})")
        
        # 3. メトリクスを計算
        print("\n3. 最適化メトリクス")
        metrics = api.calculate_optimization_metrics(result['plans'])
        print(f"  平均スコア: {metrics['average_score']:.2f}")
        print(f"  最高スコア: {metrics['best_score']:.2f}")
        print(f"  最低スコア: {metrics['worst_score']:.2f}")
        print(f"  プランタイプ: {metrics['plan_types']}")
        
    else:
        print(f"最適化失敗: {result['error']}")
    
    # 4. データベース統計
    print("\n4. データベース統計")
    stats = api.get_database_stats()
    for key, value in stats.items():
        if key != 'showtimes_by_date':
            print(f"  {key}: {value}")
    
    # 5. 映画館間距離
    print("\n5. 映画館間距離（上位5件）")
    distances = api.get_theater_distances()
    for i, distance in enumerate(distances[:5], 1):
        print(f"  {i}. {distance['from_theater_name']} → {distance['to_theater_name']}: {distance['walking_minutes']}分")

if __name__ == "__main__":
    main()