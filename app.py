from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import logging
from datetime import datetime
import json

# 最適化API関連インポート
from optimization_api import MovieOptimizationAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Movie Optimization System", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイルのマウント
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 最適化APIインスタンス
optimization_api = MovieOptimizationAPI()

# リクエストモデル
class SearchRequest(BaseModel):
    date: str = "2025-07-14"
    time_from: str = "19:00"
    time_to: str = "22:00"

class OptimizationRequest(BaseModel):
    showtime_id: int
    plan_type: str = "all"
    max_travel_time: int = 30
    buffer_time: int = 15
    time_from: str = "19:00"
    time_to: str = "22:00"

@app.get("/")
async def read_root():
    """メインページ - HTMLファイルを返す"""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "映画最適化システムが正常に動作しています！", "status": "running"}

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "service": "Movie Optimization System"}

@app.get("/api/test")
async def test_api():
    """テスト用API"""
    return {
        "success": True,
        "message": "APIが正常に動作しています",
        "data": {
            "system": "Movie Optimization System",
            "version": "1.0.0",
            "environment": "production"
        }
    }

@app.post("/api/search")
async def search_movies(request: SearchRequest):
    """映画を検索"""
    try:
        movies = optimization_api.get_available_movies(
            date=request.date,
            time_from=request.time_from,
            time_to=request.time_to
        )
        return {
            "success": True,
            "movies": movies,
            "total_movies": len(movies),
            "search_params": {
                "date": request.date,
                "time_from": request.time_from,
                "time_to": request.time_to
            }
        }
    except Exception as e:
        logger.error(f"Movie search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimize")
async def optimize_plan(request: OptimizationRequest):
    """プランを最適化"""
    try:
        result = optimization_api.optimize_plan(
            showtime_id=request.showtime_id,
            max_travel_time=request.max_travel_time,
            buffer_time=request.buffer_time,
            plan_type=request.plan_type,
            time_from=request.time_from,
            time_to=request.time_to
        )
        return result
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crawling-status")
async def get_crawling_status():
    """クローリング状況を取得"""
    try:
        status = optimization_api.get_crawling_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get crawling status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/plan/{plan_id}")
async def get_plan_details(plan_id: int):
    """プランの詳細を取得"""
    try:
        plan = optimization_api.get_plan_details(plan_id)
        return plan
    except Exception as e:
        logger.error(f"Failed to get plan details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/database-stats")
async def get_database_stats():
    """データベース統計情報を取得"""
    try:
        stats = optimization_api.get_database_stats()
        return {
            "success": True,
            "stats": stats,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/theater-distances")
async def get_theater_distances():
    """映画館間距離を取得"""
    try:
        distances = optimization_api.get_theater_distances()
        return {
            "success": True,
            "distances": distances,
            "total_distances": len(distances)
        }
    except Exception as e:
        logger.error(f"Failed to get theater distances: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crawl")
async def trigger_crawling():
    """クローリングを実行（デモ用）"""
    try:
        # 実際のクローリングは時間がかかるため、ここでは状態を返すだけ
        return {
            "success": True,
            "message": "クローリングが開始されました",
            "status": "started",
            "estimated_duration": "5-10分"
        }
    except Exception as e:
        logger.error(f"Failed to trigger crawling: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system-info")
async def get_system_info():
    """システム情報を取得"""
    try:
        # データベース統計
        db_stats = optimization_api.get_database_stats()
        
        # システム情報
        system_info = {
            "system_name": "Movie Optimization System",
            "version": "1.0.0",
            "status": "running",
            "database_path": optimization_api.db_path,
            "database_stats": db_stats,
            "features": [
                "映画検索",
                "プラン最適化",
                "移動時間計算",
                "スケジュール管理"
            ],
            "supported_theaters": [
                "新宿バルト9",
                "TOHOシネマズ新宿",
                "シネマート新宿",
                "テアトル新宿"
            ]
        }
        
        return {
            "success": True,
            "system_info": system_info,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# エラーハンドリング
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print("映画最適化システム Webアプリケーション起動中...")
    print(f"URL: http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)