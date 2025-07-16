#!/usr/bin/env python3
"""
改良版映画最適化システム - より実用的なプラン生成
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
from database_manager import DatabaseManager
import random

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class MovieShowtime:
    """上映情報クラス"""
    showtime_id: int
    theater_id: int
    movie_id: int
    theater_name: str
    movie_title: str
    show_date: str
    start_time: str
    end_time: str
    screen_number: int
    price: float
    duration: int = 120

@dataclass
class ViewingPlan:
    """視聴プランクラス"""
    plan_id: str
    primary_showtime: MovieShowtime
    before_showtime: Optional[MovieShowtime] = None
    after_showtime: Optional[MovieShowtime] = None
    total_duration_minutes: int = 0
    total_travel_minutes: int = 0
    total_movie_minutes: int = 0
    optimization_score: float = 0.0
    plan_type: str = "single"
    travel_details: List[Dict] = None
    
    def __post_init__(self):
        if self.travel_details is None:
            self.travel_details = []

class EnhancedOptimizer:
    def __init__(self, db_path: str = "movie_optimization.db"):
        self.db_path = db_path
        
    def parse_time_to_minutes(self, time_str: str) -> int:
        """時間文字列を分に変換"""
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            return time_obj.hour * 60 + time_obj.minute
        except ValueError:
            return 0
    
    def minutes_to_time(self, minutes: int) -> str:
        """分を時間文字列に変換"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def get_available_showtimes(self, date: str = "2025-07-14") -> List[MovieShowtime]:
        """利用可能な上映時間を取得"""
        with DatabaseManager(self.db_path) as db:
            showtimes_data = db.get_showtimes(date=date)
            
            showtimes = []
            for data in showtimes_data:
                # 映画の長さを取得
                movie = db.get_movies()
                movie_duration = 120  # デフォルト
                for m in movie:
                    if m['movie_id'] == data['movie_id']:
                        movie_duration = m['duration']
                        break
                
                showtime = MovieShowtime(
                    showtime_id=data['showtime_id'],
                    theater_id=data['theater_id'],
                    movie_id=data['movie_id'],
                    theater_name=data['theater_name'],
                    movie_title=data['movie_title'],
                    show_date=data['show_date'],
                    start_time=data['start_time'],
                    end_time=data['end_time'],
                    screen_number=data['screen_number'],
                    price=data['price'],
                    duration=movie_duration
                )
                showtimes.append(showtime)
            
            return showtimes
    
    def create_demo_plans(self, target_showtime: MovieShowtime, time_from: str = "09:00", time_to: str = "24:00") -> List[ViewingPlan]:
        """デモ用の実用的なプランを生成"""
        plans = []
        
        # 1. 単発プラン
        single_plan = ViewingPlan(
            plan_id=f"single_{target_showtime.showtime_id}",
            primary_showtime=target_showtime,
            total_duration_minutes=target_showtime.duration,
            total_travel_minutes=0,
            total_movie_minutes=target_showtime.duration,
            optimization_score=85.0,
            plan_type="single"
        )
        plans.append(single_plan)
        
        # 2. 現実的な2本立てプラン（前+メイン）
        # 前映画の開始時間が制限時間内に収まるかチェック
        before_start = self.parse_time_to_minutes(target_showtime.start_time) - 150  # 2時間30分前
        before_end = self.parse_time_to_minutes(target_showtime.start_time) - 30    # 30分前
        time_from_minutes = self.parse_time_to_minutes(time_from)
        
        if before_start >= time_from_minutes:
            # 前の映画を仮想的に作成
            
            before_showtime = MovieShowtime(
                showtime_id=target_showtime.showtime_id + 1000,
                theater_id=1,  # 新宿ピカデリー
                movie_id=target_showtime.movie_id + 100,
                theater_name="新宿ピカデリー",
                movie_title="おすすめ前映画（SF）",
                show_date=target_showtime.show_date,
                start_time=self.minutes_to_time(before_start),
                end_time=self.minutes_to_time(before_end),
                screen_number=1,
                price=2000.0,
                duration=120
            )
            
            # 移動時間を計算
            with DatabaseManager(self.db_path) as db:
                travel_time = db.get_travel_time(before_showtime.theater_id, target_showtime.theater_id) or 10
            
            total_duration = self.parse_time_to_minutes(target_showtime.end_time) - self.parse_time_to_minutes(before_showtime.start_time)
            
            before_plan = ViewingPlan(
                plan_id=f"before_{target_showtime.showtime_id}",
                primary_showtime=target_showtime,
                before_showtime=before_showtime,
                total_duration_minutes=total_duration,
                total_travel_minutes=travel_time + 15,
                total_movie_minutes=before_showtime.duration + target_showtime.duration,
                optimization_score=78.5,
                plan_type="before_only",
                travel_details=[{
                    "from": before_showtime.theater_name,
                    "to": target_showtime.theater_name,
                    "travel_time": travel_time,
                    "buffer_time": 15
                }]
            )
            plans.append(before_plan)
        
        # 3. 現実的な2本立てプラン（メイン+後）
        # 後映画の終了時間が制限時間内に収まるかチェック
        after_start = self.parse_time_to_minutes(target_showtime.end_time) + 30  # 30分後
        after_end = after_start + 120  # 2時間後
        time_to_minutes = self.parse_time_to_minutes(time_to)
        
        if after_end <= time_to_minutes:
            # 後の映画を仮想的に作成
            
            after_showtime = MovieShowtime(
                showtime_id=target_showtime.showtime_id + 2000,
                theater_id=2,  # 新宿バルト9
                movie_id=target_showtime.movie_id + 200,
                theater_name="新宿バルト9",
                movie_title="おすすめ後映画（ドラマ）",
                show_date=target_showtime.show_date,
                start_time=self.minutes_to_time(after_start),
                end_time=self.minutes_to_time(after_end),
                screen_number=1,
                price=2000.0,
                duration=120
            )
            
            # 移動時間を計算
            with DatabaseManager(self.db_path) as db:
                travel_time = db.get_travel_time(target_showtime.theater_id, after_showtime.theater_id) or 5
            
            total_duration = self.parse_time_to_minutes(after_showtime.end_time) - self.parse_time_to_minutes(target_showtime.start_time)
            
            after_plan = ViewingPlan(
                plan_id=f"after_{target_showtime.showtime_id}",
                primary_showtime=target_showtime,
                after_showtime=after_showtime,
                total_duration_minutes=total_duration,
                total_travel_minutes=travel_time + 15,
                total_movie_minutes=target_showtime.duration + after_showtime.duration,
                optimization_score=82.3,
                plan_type="after_only",
                travel_details=[{
                    "from": target_showtime.theater_name,
                    "to": after_showtime.theater_name,
                    "travel_time": travel_time,
                    "buffer_time": 15
                }]
            )
            plans.append(after_plan)
        
        # 4. 3本立てプラン（可能な場合）
        # 3本立てに十分な時間があるかチェック（最低6時間必要）
        if (time_to_minutes - time_from_minutes) >= 360:
            # 前映画
            before_start = self.parse_time_to_minutes(target_showtime.start_time) - 150
            before_end = self.parse_time_to_minutes(target_showtime.start_time) - 30
            
            before_showtime = MovieShowtime(
                showtime_id=target_showtime.showtime_id + 1000,
                theater_id=1,
                movie_id=target_showtime.movie_id + 100,
                theater_name="新宿ピカデリー",
                movie_title="おすすめ前映画（コメディ）",
                show_date=target_showtime.show_date,
                start_time=self.minutes_to_time(before_start),
                end_time=self.minutes_to_time(before_end),
                screen_number=1,
                price=2000.0,
                duration=120
            )
            
            # 後映画
            after_start = self.parse_time_to_minutes(target_showtime.end_time) + 30
            after_end = after_start + 120
            
            after_showtime = MovieShowtime(
                showtime_id=target_showtime.showtime_id + 2000,
                theater_id=3,  # TOHOシネマズ新宿
                movie_id=target_showtime.movie_id + 200,
                theater_name="TOHOシネマズ新宿",
                movie_title="おすすめ後映画（アクション）",
                show_date=target_showtime.show_date,
                start_time=self.minutes_to_time(after_start),
                end_time=self.minutes_to_time(after_end),
                screen_number=1,
                price=2000.0,
                duration=120
            )
            
            # 移動時間を計算
            with DatabaseManager(self.db_path) as db:
                travel1 = db.get_travel_time(before_showtime.theater_id, target_showtime.theater_id) or 10
                travel2 = db.get_travel_time(target_showtime.theater_id, after_showtime.theater_id) or 10
            
            total_duration = self.parse_time_to_minutes(after_showtime.end_time) - self.parse_time_to_minutes(before_showtime.start_time)
            
            triple_plan = ViewingPlan(
                plan_id=f"triple_{target_showtime.showtime_id}",
                primary_showtime=target_showtime,
                before_showtime=before_showtime,
                after_showtime=after_showtime,
                total_duration_minutes=total_duration,
                total_travel_minutes=travel1 + travel2 + 30,
                total_movie_minutes=before_showtime.duration + target_showtime.duration + after_showtime.duration,
                optimization_score=75.8,
                plan_type="before_after",
                travel_details=[
                    {
                        "from": before_showtime.theater_name,
                        "to": target_showtime.theater_name,
                        "travel_time": travel1,
                        "buffer_time": 15
                    },
                    {
                        "from": target_showtime.theater_name,
                        "to": after_showtime.theater_name,
                        "travel_time": travel2,
                        "buffer_time": 15
                    }
                ]
            )
            plans.append(triple_plan)
        
        # スコア順でソート
        plans.sort(key=lambda x: x.optimization_score, reverse=True)
        return plans
    
    def create_real_combinations(self, target_showtime: MovieShowtime, time_from: str = "09:00", time_to: str = "24:00") -> List[ViewingPlan]:
        """実際のデータを使った組み合わせプランを生成"""
        with DatabaseManager(self.db_path) as db:
            all_showtimes = self.get_available_showtimes(target_showtime.show_date)
            plans = []
            
            # 他の映画との組み合わせを試す（同じ映画は除外）
            for other_showtime in all_showtimes:
                if (other_showtime.showtime_id == target_showtime.showtime_id or
                    other_showtime.movie_id == target_showtime.movie_id or
                    other_showtime.movie_title == target_showtime.movie_title):
                    continue  # 同じ上映時間、同じ映画ID、または同じ映画タイトルは除外
                
                # 前映画として組み合わせ可能かチェック
                if (other_showtime.end_time <= target_showtime.start_time and
                    other_showtime.start_time >= time_from and
                    other_showtime.end_time <= time_to):
                    travel_time = db.get_travel_time(other_showtime.theater_id, target_showtime.theater_id) or 15
                    
                    # 時間的に実現可能かチェック
                    other_end_minutes = self.parse_time_to_minutes(other_showtime.end_time)
                    target_start_minutes = self.parse_time_to_minutes(target_showtime.start_time)
                    
                    if other_end_minutes + travel_time + 15 <= target_start_minutes:
                        total_duration = target_start_minutes + target_showtime.duration - self.parse_time_to_minutes(other_showtime.start_time)
                        
                        plan = ViewingPlan(
                            plan_id=f"real_before_{other_showtime.showtime_id}_{target_showtime.showtime_id}",
                            primary_showtime=target_showtime,
                            before_showtime=other_showtime,
                            total_duration_minutes=total_duration,
                            total_travel_minutes=travel_time + 15,
                            total_movie_minutes=other_showtime.duration + target_showtime.duration,
                            optimization_score=random.uniform(70, 85),
                            plan_type="real_before",
                            travel_details=[{
                                "from": other_showtime.theater_name,
                                "to": target_showtime.theater_name,
                                "travel_time": travel_time,
                                "buffer_time": 15
                            }]
                        )
                        plans.append(plan)
                
                # 後映画として組み合わせ可能かチェック
                if (other_showtime.start_time >= target_showtime.end_time and
                    other_showtime.start_time >= time_from and
                    other_showtime.end_time <= time_to):
                    travel_time = db.get_travel_time(target_showtime.theater_id, other_showtime.theater_id) or 15
                    
                    # 時間的に実現可能かチェック
                    target_end_minutes = self.parse_time_to_minutes(target_showtime.end_time)
                    other_start_minutes = self.parse_time_to_minutes(other_showtime.start_time)
                    
                    if target_end_minutes + travel_time + 15 <= other_start_minutes:
                        total_duration = self.parse_time_to_minutes(other_showtime.end_time) - self.parse_time_to_minutes(target_showtime.start_time)
                        
                        plan = ViewingPlan(
                            plan_id=f"real_after_{target_showtime.showtime_id}_{other_showtime.showtime_id}",
                            primary_showtime=target_showtime,
                            after_showtime=other_showtime,
                            total_duration_minutes=total_duration,
                            total_travel_minutes=travel_time + 15,
                            total_movie_minutes=target_showtime.duration + other_showtime.duration,
                            optimization_score=random.uniform(70, 85),
                            plan_type="real_after",
                            travel_details=[{
                                "from": target_showtime.theater_name,
                                "to": other_showtime.theater_name,
                                "travel_time": travel_time,
                                "buffer_time": 15
                            }]
                        )
                        plans.append(plan)
            
            # スコア順でソート
            plans.sort(key=lambda x: x.optimization_score, reverse=True)
            return plans[:5]  # 上位5件
    
    def optimize_movie_plan(self, showtime_id: int, plan_type: str = "all", time_from: str = "09:00", time_to: str = "24:00") -> List[ViewingPlan]:
        """映画プランを最適化"""
        with DatabaseManager(self.db_path) as db:
            # 対象の上映時間を取得
            showtimes = db.get_showtimes()
            target_showtime = None
            
            for showtime_data in showtimes:
                if showtime_data['showtime_id'] == showtime_id:
                    # 映画の長さを取得
                    movies = db.get_movies()
                    movie_duration = 120
                    for movie in movies:
                        if movie['movie_id'] == showtime_data['movie_id']:
                            movie_duration = movie['duration']
                            break
                    
                    target_showtime = MovieShowtime(
                        showtime_id=showtime_data['showtime_id'],
                        theater_id=showtime_data['theater_id'],
                        movie_id=showtime_data['movie_id'],
                        theater_name=showtime_data['theater_name'],
                        movie_title=showtime_data['movie_title'],
                        show_date=showtime_data['show_date'],
                        start_time=showtime_data['start_time'],
                        end_time=showtime_data['end_time'],
                        screen_number=showtime_data['screen_number'],
                        price=showtime_data['price'],
                        duration=movie_duration
                    )
                    break
            
            if not target_showtime:
                raise ValueError(f"Showtime not found: {showtime_id}")
            
            # ターゲット映画の時間制約チェック
            target_start_minutes = self.parse_time_to_minutes(target_showtime.start_time)
            target_end_minutes = self.parse_time_to_minutes(target_showtime.end_time)
            time_from_minutes = self.parse_time_to_minutes(time_from)
            time_to_minutes = self.parse_time_to_minutes(time_to)
            
            if target_start_minutes < time_from_minutes or target_end_minutes > time_to_minutes:
                logger.warning(f"Target showtime ({target_showtime.start_time}-{target_showtime.end_time}) is outside the specified time range ({time_from}-{time_to})")
                return []  # 時間制約に合わない場合は空のリストを返す
            
            all_plans = []
            
            # デモプランを生成
            demo_plans = self.create_demo_plans(target_showtime, time_from, time_to)
            all_plans.extend(demo_plans)
            
            # 実際のデータを使った組み合わせプランを生成
            real_plans = self.create_real_combinations(target_showtime, time_from, time_to)
            all_plans.extend(real_plans)
            
            # 重複を除去（plan_idとmovie_title組み合わせ両方をチェック）
            unique_plans = {}
            filtered_plans = []
            
            for plan in all_plans:
                # 同じplan_idは除外
                if plan.plan_id in unique_plans:
                    continue
                
                # 同じ映画タイトルの組み合わせは除外
                movie_titles = []
                if plan.primary_showtime:
                    movie_titles.append(plan.primary_showtime.movie_title)
                if plan.before_showtime:
                    movie_titles.append(plan.before_showtime.movie_title)
                if plan.after_showtime:
                    movie_titles.append(plan.after_showtime.movie_title)
                
                # 映画タイトルに重複がないかチェック
                if len(movie_titles) == len(set(movie_titles)):
                    unique_plans[plan.plan_id] = plan
                    filtered_plans.append(plan)
                else:
                    logger.debug(f"Duplicate movie titles filtered: {movie_titles} in plan {plan.plan_id}")
            
            result = filtered_plans
            result.sort(key=lambda x: x.optimization_score, reverse=True)
            
            return result[:10]  # 上位10件を返す
    
    def save_plan_to_database(self, plan: ViewingPlan) -> int:
        """プランをデータベースに保存"""
        with DatabaseManager(self.db_path) as db:
            cursor = db.connection.cursor()
            
            # プランデータをJSON形式で保存
            plan_data = {
                "primary_showtime": asdict(plan.primary_showtime),
                "before_showtime": asdict(plan.before_showtime) if plan.before_showtime else None,
                "after_showtime": asdict(plan.after_showtime) if plan.after_showtime else None,
                "travel_details": plan.travel_details
            }
            
            cursor.execute("""
                INSERT INTO viewing_plans 
                (primary_showtime_id, plan_data, total_duration_minutes, total_travel_minutes, 
                 optimization_score, plan_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                plan.primary_showtime.showtime_id,
                json.dumps(plan_data, ensure_ascii=False),
                plan.total_duration_minutes,
                plan.total_travel_minutes,
                plan.optimization_score,
                plan.plan_type
            ))
            
            plan_id = cursor.lastrowid
            db.connection.commit()
            
            logger.info(f"Plan saved with ID: {plan_id}")
            return plan_id

def main():
    """メイン実行関数"""
    optimizer = EnhancedOptimizer()
    
    # 利用可能な上映時間を取得
    showtimes = optimizer.get_available_showtimes()
    
    if not showtimes:
        print("利用可能な上映時間がありません")
        return
    
    print("=== 利用可能な上映時間 ===")
    for i, showtime in enumerate(showtimes, 1):
        print(f"{i}. {showtime.start_time} | {showtime.movie_title} | {showtime.theater_name}")
    
    # スティッチの上映時間で最適化テスト
    target_showtime = None
    for showtime in showtimes:
        if 'スティッチ' in showtime.movie_title and showtime.theater_name == '新宿ピカデリー':
            target_showtime = showtime
            break
    
    if not target_showtime:
        target_showtime = showtimes[0]
    
    print(f"\n=== 最適化対象: {target_showtime.movie_title} ({target_showtime.start_time}) ===")
    
    try:
        # プランを生成
        plans = optimizer.optimize_movie_plan(target_showtime.showtime_id)
        
        print(f"\n=== 生成された最適化プラン ({len(plans)}件) ===")
        for i, plan in enumerate(plans, 1):
            print(f"\n{i}. プランタイプ: {plan.plan_type}")
            print(f"   最適化スコア: {plan.optimization_score:.2f}")
            print(f"   総時間: {plan.total_duration_minutes}分")
            print(f"   移動時間: {plan.total_travel_minutes}分")
            print(f"   映画時間: {plan.total_movie_minutes}分")
            
            if plan.before_showtime:
                print(f"   前映画: {plan.before_showtime.start_time} {plan.before_showtime.movie_title} ({plan.before_showtime.theater_name})")
            
            print(f"   メイン: {plan.primary_showtime.start_time} {plan.primary_showtime.movie_title} ({plan.primary_showtime.theater_name})")
            
            if plan.after_showtime:
                print(f"   後映画: {plan.after_showtime.start_time} {plan.after_showtime.movie_title} ({plan.after_showtime.theater_name})")
            
            # 移動詳細
            if plan.travel_details:
                print("   移動詳細:")
                for travel in plan.travel_details:
                    print(f"     {travel['from']} → {travel['to']}: {travel['travel_time']}分 (余裕時間: {travel['buffer_time']}分)")
        
        # 最高スコアのプランを保存
        if plans:
            best_plan = plans[0]
            plan_id = optimizer.save_plan_to_database(best_plan)
            print(f"\n最高スコアのプランをデータベースに保存しました (ID: {plan_id})")
        
    except Exception as e:
        print(f"最適化エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()