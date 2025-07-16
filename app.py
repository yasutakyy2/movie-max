from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os

app = FastAPI(title="Movie Optimization System", version="1.0.0")

# 静的ファイルのマウント
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    """ルートパス - ホームページ"""
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print("映画最適化システム Webアプリケーション起動中...")
    print(f"URL: http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)