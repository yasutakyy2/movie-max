#!/usr/bin/env python3
"""
映画最適化システム FastAPI Webアプリケーション
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os

from optimization_api import MovieOptimizationAPI
from database_manager import DatabaseManager
from crawler_api import MovieCrawlerAPI

app = FastAPI(title="Movie Optimization System", version="1.0.0")

# 静的ファイルのマウント
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# API初期化
movie_api = MovieOptimizationAPI()
crawler_api = MovieCrawlerAPI()

# Pydanticモデル
class OptimizationRequest(BaseModel):
    showtime_id: int
    max_travel_time: int = 30
    buffer_time: int = 15
    plan_type: str = "all"
    max_total_duration: int = 480
    time_from: str = "19:00"
    time_to: str = "22:00"

class MovieSearchRequest(BaseModel):
    date: str = "2025-07-14"
    time_from: str = "19:00"
    time_to: str = "20:00"

class CrawlingRequest(BaseModel):
    date: str
    time_from: str
    time_to: str
    available_hours: List[int] = []

class UserAvailabilityRequest(BaseModel):
    available_hours: List[int]
    preferred_date: str
    max_movies: int = 3

@app.get("/")
async def read_root():
    """ルートパス - React アプリを提供"""
    return FileResponse("static/index.html")

@app.get("/api/movies")
async def get_movies(date: str = "2025-07-14", time_from: str = "19:00", time_to: str = "20:00"):
    """利用可能な映画を取得"""
    try:
        movies = movie_api.get_available_movies(date, time_from, time_to)
        return {
            "success": True,
            "movies": movies,
            "total": len(movies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimize")
async def optimize_plan(request: OptimizationRequest):
    """映画プランを最適化"""
    try:
        result = movie_api.optimize_plan(
            showtime_id=request.showtime_id,
            max_travel_time=request.max_travel_time,
            buffer_time=request.buffer_time,
            plan_type=request.plan_type,
            max_total_duration=request.max_total_duration,
            time_from=request.time_from,
            time_to=request.time_to
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/plan/{plan_id}")
async def get_plan_details(plan_id: int):
    """プランの詳細を取得"""
    try:
        result = movie_api.get_plan_details(plan_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_database_stats():
    """データベース統計情報を取得"""
    try:
        stats = movie_api.get_database_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crawling-status")
async def get_crawling_status():
    """クローリング状況を取得"""
    try:
        status = movie_api.get_crawling_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/theaters")
async def get_theaters():
    """映画館一覧を取得"""
    try:
        with DatabaseManager() as db:
            theaters = db.get_theaters()
            return {
                "success": True,
                "theaters": theaters,
                "total": len(theaters)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/distances")
async def get_theater_distances():
    """映画館間距離を取得"""
    try:
        distances = movie_api.get_theater_distances()
        return {
            "success": True,
            "distances": distances,
            "total": len(distances)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crawler/dates")
async def get_available_dates():
    """利用可能な日付を取得"""
    try:
        dates = crawler_api.get_available_dates()
        return {
            "success": True,
            "dates": dates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crawler/time-slots")
async def get_time_slots():
    """推奨時間スロットを取得"""
    try:
        slots = crawler_api.get_time_slots()
        return {
            "success": True,
            "time_slots": slots
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crawler/validate-time")
async def validate_time_input(request: CrawlingRequest):
    """時間入力を検証"""
    try:
        result = crawler_api.validate_time_input(
            request.time_from, 
            request.time_to, 
            request.available_hours
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crawler/estimate")
async def estimate_crawling_time(request: CrawlingRequest):
    """クローリング時間を見積もり"""
    try:
        estimate = crawler_api.estimate_crawling_time(
            request.date,
            request.time_from,
            request.time_to
        )
        return {
            "success": True,
            "estimate": estimate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crawler/crawl")
async def crawl_movies(request: CrawlingRequest):
    """映画をクローリング"""
    try:
        # デバッグログ
        print(f"Crawl request received: {request}")
        print(f"  date: {request.date}")
        print(f"  time_from: '{request.time_from}'")
        print(f"  time_to: '{request.time_to}'")
        print(f"  available_hours: {request.available_hours}")
        
        # まず時間入力を検証
        validation = crawler_api.validate_time_input(
            request.time_from,
            request.time_to,
            request.available_hours
        )
        
        print(f"Validation result: {validation}")
        
        if not validation['valid']:
            return {
                "success": False,
                "error": validation['error']
            }
        
        # クローリング実行
        result = crawler_api.crawl_movies(
            request.date,
            request.time_from,
            request.time_to
        )
        
        return result
    except Exception as e:
        print(f"Crawl error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "service": "Movie Optimization System"}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    print("映画最適化システム Webアプリケーション起動中...")
    print(f"URL: http://localhost:{port}")
    print(f"API文書: http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port)