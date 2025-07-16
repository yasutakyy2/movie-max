# コアファイル一覧

このドキュメントでは、映画最適化システムの動作に必要な核となるファイルを説明します。

## 必須ファイル（削除禁止）

### 1. Webアプリケーション
- **app.py** - FastAPIメインアプリケーション
- **static/index.html** - React.jsフロントエンドUI

### 2. データベース関連
- **database_manager.py** - データベース操作クラス
- **movie_optimization.db** - メインデータベースファイル
- **database_schema.sql** - スキーマ定義
- **setup_database.py** - データベース初期化スクリプト

### 3. 最適化エンジン
- **enhanced_optimizer.py** - 最適化アルゴリズム実装
- **optimization_api.py** - 最適化API インターフェース

### 4. データクローリング
- **complete_eiga_crawler.py** - メインクローリングシステム
- **quick_nakayama_search.py** - 特定映画検索機能

### 5. ドキュメント
- **README.md** - システム概要とセットアップガイド
- **ARCHITECTURE.md** - システムアーキテクチャ文書
- **CORE_FILES.md** - このファイル

## テスト・開発用ファイル（削除可能）

### クローリングテスト
- **accurate_movie_crawler.py** - 精度テスト用クローラー
- **improved_accurate_crawler.py** - 改良版クローラー
- **improved_movie_crawler.py** - 旧版クローラー
- **movie_crawler.py** - 初期版クローラー
- **updated_movie_crawler.py** - 更新版クローラー
- **comprehensive_theater_crawler.py** - 包括的クローラー
- **eiga_com_theater_crawler.py** - 映画.com専用クローラー
- **musashino_crawler.py** - 武蔵野館専用クローラー

### データベーステスト
- **check_db.py** - データベース確認スクリプト
- **check_actual_times.py** - 時間データ確認
- **check_database_movies.py** - 映画データ確認
- **find_nakayama_showtime.py** - 特定映画上映時間検索

### 最適化テスト
- **test_time_constraints.py** - 時間制約テスト
- **test_14_hour_movie.py** - 14時映画テスト
- **test_single_theater.py** - 単一映画館テスト
- **test_known_movie.py** - 既知映画テスト

### ユーティリティ
- **clean_titles.py** - タイトル正規化
- **update_movie_titles.py** - 映画タイトル更新
- **update_theater_database.py** - 映画館データ更新
- **movie_title_extractor.py** - タイトル抽出ツール
- **data_importer.py** - データインポート
- **score_calculator.py** - スコア計算
- **debug_html.py** - HTMLデバッグ
- **crawler_api.py** - クローラーAPI
- **crawler_health_monitor.py** - クローラー監視

### 静的ファイル
- **static/setup.html** - セットアップページ
- **static/test.html** - テストページ

## データファイル（削除可能）

### クローリング結果
- **accurate_crawling_test.json**
- **accurate_movies_20250715_170044.json**
- **actual_movie_titles.json**
- **comprehensive_theater_data.json**
- **crawler_health.json**
- **known_movie_test.json**
- **latest_movie_data.json**
- **movie_accuracy_verification.json**
- **movie_verification_result.json**
- **nakayama_final_info.json**
- **nakayama_quick_search.json**
- **shinjuku_movies_20250715_151948.json**
- **single_theater_test.json**
- **musashino_schedule.json**

### ログファイル
- **movie_crawler.log**
- **debug_html.html**

### ドキュメント（保持推奨）
- **database_setup_report.md**
- **movie_optimization_system_spec.md**
- **optimization_system_summary.md**

## ファイル削除の優先順位

### 高優先度（すぐに削除可能）
1. 重複するクローリングスクリプト
2. 古いテストファイル
3. 一時的なJSONデータファイル
4. デバッグ用ファイル

### 中優先度（確認後削除）
1. 旧版の最適化スクリプト
2. 実験的な機能ファイル
3. 古いドキュメント

### 低優先度（保持推奨）
1. データベーススキーマファイル
2. 設定関連ファイル
3. 現在使用中のドキュメント

## システム動作に必要な最小構成

```
movie-max/
├── app.py                      # Webサーバー
├── database_manager.py         # DB操作
├── enhanced_optimizer.py       # 最適化
├── optimization_api.py         # API
├── complete_eiga_crawler.py    # クローリング
├── setup_database.py           # DB初期化
├── movie_optimization.db       # データベース
├── database_schema.sql         # スキーマ
├── static/
│   └── index.html             # フロントエンド
└── README.md                  # ドキュメント
```

この最小構成でシステムの完全な動作が可能です。