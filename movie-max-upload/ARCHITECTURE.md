# システムアーキテクチャ

## 概要

映画最適化システムは、Webクローリング、データベース管理、最適化アルゴリズム、Webアプリケーションの4つの主要コンポーネントから構成されています。

## アーキテクチャ図

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React.js)    │◄──►│   (FastAPI)     │◄──►│   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Crawler       │
                       │   (映画.com)     │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Optimizer     │
                       │   (Algorithm)   │
                       └─────────────────┘
```

## コンポーネント詳細

### 1. フロントエンド (static/index.html)

**技術スタック**: React.js + Tailwind CSS

**主要機能**:
- 時間選択インターフェース
- 映画カード表示
- 最適化プラン表示
- クローリング状況表示

**コンポーネント構成**:
```javascript
App
├── TimeInputForm
├── MovieCard
├── PlanCard
├── CrawlingStatusDisplay
└── TheaterModal
```

### 2. バックエンド (app.py)

**技術スタック**: FastAPI + Uvicorn

**APIエンドポイント**:
- `GET /api/stats` - システム統計
- `GET /api/movies` - 映画検索
- `POST /api/optimize` - プラン最適化
- `GET /api/crawling-status` - クローリング状況
- `GET /api/theaters` - 映画館一覧

### 3. データベース (SQLite)

**スキーマ構成**:
```sql
theaters (映画館情報)
├── theater_id (PK)
├── name
├── address
├── area
└── screen_count

movies (映画情報)
├── movie_id (PK)
├── title
├── duration
└── image_url

showtimes (上映情報)
├── showtime_id (PK)
├── movie_id (FK)
├── theater_id (FK)
├── showtime_date
├── start_time
├── end_time
├── screen_number
└── price

viewing_plans (最適化プラン)
├── plan_id (PK)
├── plan_type
├── optimization_score
├── total_duration_minutes
├── total_travel_minutes
└── plan_data (JSON)
```

### 4. クローリングシステム

**主要クラス**:
- `CompleteEigaCrawler`: 映画.comからの完全データ取得
- `QuickNakayamaSearch`: 特定映画の高速検索
- `DatabaseManager`: データベース操作の抽象化

**データフロー**:
```
映画.com → HTML解析 → データ抽出 → データベース保存
```

### 5. 最適化エンジン

**主要クラス**:
- `EnhancedOptimizer`: 最適化アルゴリズムの実装
- `MovieOptimizationAPI`: 最適化機能のAPIラッパー

**最適化ロジック**:
1. 時間制約の検証
2. 移動時間の計算
3. プランタイプ別の生成
4. スコア計算と順位付け

## データフロー

### 1. 初期データ取得
```
complete_eiga_crawler.py → movie_optimization.db
```

### 2. リアルタイム検索
```
Frontend → Backend API → Database → 最適化エンジン → Frontend
```

### 3. プラン生成
```
選択映画 → 時間制約チェック → 移動時間計算 → プラン生成 → スコア計算
```

## セキュリティ考慮事項

### 1. クローリング制限
- リクエスト間隔の制御（1-2秒）
- タイムアウト設定（15秒）
- エラーハンドリングとリトライ

### 2. データベースセキュリティ
- SQLインジェクション対策（パラメータ化クエリ）
- データ型の検証
- 入力値のサニタイズ

### 3. API セキュリティ
- CORS設定
- レート制限（実装可能）
- 入力データの検証

## パフォーマンス最適化

### 1. データベース
- インデックスの設定（時間、映画館ID）
- クエリの最適化
- 接続プールの利用

### 2. フロントエンド
- 画像の遅延読み込み
- コンポーネントの最適化
- 状態管理の効率化

### 3. クローリング
- 並列処理の制限
- キャッシュの活用
- 差分更新の実装

## スケーラビリティ

### 1. 水平スケーリング
- データベースの分散化
- API サーバーの負荷分散
- CDN の利用

### 2. 垂直スケーリング
- メモリ使用量の最適化
- CPU 処理の効率化
- ディスク I/O の改善

## 監視とログ

### 1. アプリケーション監視
- API レスポンス時間
- エラー率の追跡
- リソース使用状況

### 2. ログ管理
- 構造化ログの採用
- ログレベルの分類
- ローテーション設定

## 今後の拡張性

### 1. 機能拡張
- 他エリアの映画館対応
- ユーザー設定の永続化
- レコメンデーション機能

### 2. 技術的改善
- リアルタイム更新（WebSocket）
- PWA 対応
- モバイルアプリ化

## 依存関係

### Python パッケージ
```
fastapi==0.104.1
uvicorn==0.24.0
requests==2.31.0
beautifulsoup4==4.12.2
sqlite3 (標準ライブラリ)
```

### JavaScript ライブラリ
```
React 18
Tailwind CSS 2.2.19
Babel Standalone
```

## 開発環境

### 必要な環境
- Python 3.8+
- SQLite 3
- モダンブラウザ（Chrome, Firefox, Safari）

### 開発ツール
- テキストエディタ（VS Code推奨）
- ブラウザ開発者ツール
- SQLite管理ツール（DB Browser for SQLite推奨）