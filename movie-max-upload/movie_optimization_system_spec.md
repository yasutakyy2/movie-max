# 映画最適化閲覧システム 設計仕様書

## 概要

映画.comからクローリングしたデータを基に、移動距離を考慮した最適な映画閲覧プランを推薦するシステムです。ユーザーが選択した映画の前後に最適な映画を組み合わせて、効率的な映画鑑賞体験を提供します。

---

## システム要件

### 機能要件

1. **映画データ管理**
   - 映画.comからクローリングしたデータの格納・更新
   - 映画館情報、上映スケジュール、映画詳細の管理

2. **最適化エンジン**
   - 移動時間を考慮した映画組み合わせの計算
   - ユーザーの時間制約内での最適プラン生成
   - 複数の最適化アルゴリズムの実装

3. **推薦システム**
   - ユーザー選択映画を基点とした前後映画の推薦
   - ジャンル、評価、移動効率を考慮した推薦
   - 複数プランの比較・提示

### 非機能要件

- **レスポンス時間**: 最適化計算は3秒以内
- **データ精度**: 移動時間の誤差は±5分以内
- **拡張性**: 新しい映画館・エリアの追加が容易
- **保守性**: データ更新の自動化

---

## データベース設計

### ERD概要

```mermaid
erDiagram
    THEATERS ||--o{ SHOWTIMES : has
    MOVIES ||--o{ SHOWTIMES : scheduled
    SHOWTIMES ||--o{ VIEWING_PLANS : included_in
    VIEWING_PLANS ||--o{ PLAN_RECOMMENDATIONS : generates
    THEATERS ||--o{ THEATER_DISTANCES : from
    THEATERS ||--o{ THEATER_DISTANCES : to

    THEATERS {
        int theater_id PK
        string name
        string address
        decimal latitude
        decimal longitude
        string access_info
        int total_screens
        json facilities
        datetime created_at
        datetime updated_at
    }

    MOVIES {
        int movie_id PK
        string title
        int duration_minutes
        string rating
        string genre
        text description
        decimal imdb_rating
        string director
        json cast
        date release_date
        datetime created_at
        datetime updated_at
    }

    SHOWTIMES {
        int showtime_id PK
        int theater_id FK
        int movie_id FK
        date show_date
        time start_time
        time end_time
        int screen_number
        decimal price
        string special_format
        boolean is_available
        datetime created_at
        datetime updated_at
    }

    THEATER_DISTANCES {
        int distance_id PK
        int from_theater_id FK
        int to_theater_id FK
        int walking_minutes
        int train_minutes
        int taxi_minutes
        decimal distance_km
        json route_info
        datetime created_at
        datetime updated_at
    }

    VIEWING_PLANS {
        int plan_id PK
        int primary_showtime_id FK
        json plan_data
        int total_duration_minutes
        int total_travel_minutes
        decimal optimization_score
        string plan_type
        datetime created_at
    }

    PLAN_RECOMMENDATIONS {
        int recommendation_id PK
        int plan_id FK
        int recommended_showtime_id FK
        string recommendation_type
        decimal confidence_score
        string reason
        int sequence_order
        datetime created_at
    }
```

### 詳細テーブル設計

#### 1. theaters（映画館）
```sql
CREATE TABLE theaters (
    theater_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    access_info TEXT,
    total_screens INTEGER,
    facilities JSON, -- {"parking": true, "restaurant": true, "imax": true}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. movies（映画）
```sql
CREATE TABLE movies (
    movie_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    duration_minutes INTEGER NOT NULL,
    rating VARCHAR(10), -- G, PG12, R15+, R18+
    genre VARCHAR(100),
    description TEXT,
    imdb_rating DECIMAL(3,1),
    director VARCHAR(100),
    cast JSON, -- ["俳優1", "俳優2", ...]
    release_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. showtimes（上映スケジュール）
```sql
CREATE TABLE showtimes (
    showtime_id SERIAL PRIMARY KEY,
    theater_id INTEGER REFERENCES theaters(theater_id),
    movie_id INTEGER REFERENCES movies(movie_id),
    show_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME,
    screen_number INTEGER,
    price DECIMAL(6,0) DEFAULT 2000,
    special_format VARCHAR(20), -- IMAX, 4DX, Dolby Atmos
    is_available BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(theater_id, show_date, start_time, screen_number)
);
```

#### 4. theater_distances（映画館間距離）
```sql
CREATE TABLE theater_distances (
    distance_id SERIAL PRIMARY KEY,
    from_theater_id INTEGER REFERENCES theaters(theater_id),
    to_theater_id INTEGER REFERENCES theaters(theater_id),
    walking_minutes INTEGER,
    train_minutes INTEGER,
    taxi_minutes INTEGER,
    distance_km DECIMAL(5,2),
    route_info JSON, -- {"stations": ["新宿三丁目", "新宿"], "lines": ["丸ノ内線"]}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(from_theater_id, to_theater_id)
);
```

#### 5. viewing_plans（閲覧プラン）
```sql
CREATE TABLE viewing_plans (
    plan_id SERIAL PRIMARY KEY,
    primary_showtime_id INTEGER REFERENCES showtimes(showtime_id),
    plan_data JSON, -- 全プラン詳細
    total_duration_minutes INTEGER,
    total_travel_minutes INTEGER,
    optimization_score DECIMAL(5,2),
    plan_type VARCHAR(20), -- "before_after", "before_only", "after_only"
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 6. plan_recommendations（プラン推薦）
```sql
CREATE TABLE plan_recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    plan_id INTEGER REFERENCES viewing_plans(plan_id),
    recommended_showtime_id INTEGER REFERENCES showtimes(showtime_id),
    recommendation_type VARCHAR(20), -- "before", "after"
    confidence_score DECIMAL(3,2), -- 0.00-1.00
    reason TEXT,
    sequence_order INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 最適化アルゴリズム設計

### 1. 基本アルゴリズム

#### A. 時間制約チェック
```python
def is_time_feasible(movie1_end, travel_time, movie2_start, buffer_time=15):
    """
    移動時間を考慮して上映時間が実現可能かチェック
    
    Args:
        movie1_end: 前の映画の終了時間
        travel_time: 移動時間（分）
        movie2_start: 次の映画の開始時間
        buffer_time: 余裕時間（分）
    """
    required_time = movie1_end + timedelta(minutes=travel_time + buffer_time)
    return required_time <= movie2_start
```

#### B. 最適化スコア計算
```python
def calculate_optimization_score(plan):
    """
    プランの最適化スコアを計算
    
    要素:
    - 移動効率 (40%)
    - 時間効率 (30%)
    - ジャンルバランス (20%)
    - 料金効率 (10%)
    """
    travel_efficiency = 100 - (plan.total_travel_minutes / plan.total_duration_minutes * 100)
    time_efficiency = plan.movie_minutes / plan.total_duration_minutes * 100
    genre_balance = calculate_genre_diversity(plan.movies)
    price_efficiency = calculate_price_per_minute(plan)
    
    score = (
        travel_efficiency * 0.4 +
        time_efficiency * 0.3 +
        genre_balance * 0.2 +
        price_efficiency * 0.1
    )
    return score
```

### 2. 推薦アルゴリズム

#### A. 前映画推薦
```python
def recommend_before_movies(target_movie, max_travel_time=30, buffer_time=15):
    """
    選択映画の前に見られる映画を推薦
    
    条件:
    - 終了時間 + 移動時間 + 余裕時間 <= 選択映画開始時間
    - 移動時間がmax_travel_time以内
    - ジャンルバランスを考慮
    """
    candidates = []
    for movie in get_available_movies_before(target_movie):
        travel_time = get_travel_time(movie.theater, target_movie.theater)
        if travel_time <= max_travel_time:
            if is_time_feasible(movie.end_time, travel_time, target_movie.start_time, buffer_time):
                score = calculate_recommendation_score(movie, target_movie, "before")
                candidates.append((movie, score))
    
    return sorted(candidates, key=lambda x: x[1], reverse=True)[:5]
```

#### B. 後映画推薦
```python
def recommend_after_movies(target_movie, max_travel_time=30, buffer_time=15):
    """
    選択映画の後に見られる映画を推薦
    """
    candidates = []
    for movie in get_available_movies_after(target_movie):
        travel_time = get_travel_time(target_movie.theater, movie.theater)
        if travel_time <= max_travel_time:
            if is_time_feasible(target_movie.end_time, travel_time, movie.start_time, buffer_time):
                score = calculate_recommendation_score(target_movie, movie, "after")
                candidates.append((movie, score))
    
    return sorted(candidates, key=lambda x: x[1], reverse=True)[:5]
```

### 3. 組み合わせ最適化

#### A. 3本立てプラン生成
```python
def generate_triple_plan(target_movie, max_total_time=480):  # 8時間
    """
    メイン映画を含む3本立てプランを生成
    """
    best_plans = []
    
    before_movies = recommend_before_movies(target_movie)
    after_movies = recommend_after_movies(target_movie)
    
    for before in before_movies:
        for after in after_movies:
            plan = create_plan([before[0], target_movie, after[0]])
            if plan.total_duration_minutes <= max_total_time:
                plan.score = calculate_optimization_score(plan)
                best_plans.append(plan)
    
    return sorted(best_plans, key=lambda x: x.score, reverse=True)[:3]
```

---

## API設計

### エンドポイント一覧

#### 1. 映画検索・選択
```
GET /api/movies/search
  ?date=2025-07-14
  &area=shinjuku
  &time_from=18:00
  &time_to=20:00
  &genre=action
```

#### 2. 最適化プラン生成
```
POST /api/plans/optimize
{
  "target_showtime_id": 123,
  "max_travel_time": 30,
  "buffer_time": 15,
  "plan_type": "before_after",  // "before_only", "after_only"
  "max_total_duration": 480
}
```

#### 3. プラン詳細取得
```
GET /api/plans/{plan_id}
```

#### 4. 推薦理由取得
```
GET /api/plans/{plan_id}/recommendations
```

---

## フロントエンド仕様

### 画面構成

#### 1. 映画選択画面
- **検索フィルター**: 日付、エリア、時間帯、ジャンル
- **映画一覧**: カード形式で表示
- **詳細情報**: 上映時間、映画館、移動情報

#### 2. プラン生成画面
- **選択映画表示**: 中央に配置
- **設定パネル**: 最大移動時間、余裕時間、プランタイプ
- **生成ボタン**: 最適化実行

#### 3. プラン比較画面
- **プラン一覧**: 3つまでの推薦プラン
- **タイムライン表示**: 時間軸での視覚化
- **スコア比較**: レーダーチャート
- **詳細情報**: 移動経路、料金、推薦理由

#### 4. プラン詳細画面
- **詳細スケジュール**: 分刻みのタイムテーブル
- **移動マップ**: 映画館間のルート表示
- **チケット情報**: 購入リンク

### UI/UX設計原則

1. **直感的操作**: ワンクリックでプラン生成
2. **視覚的理解**: タイムラインとマップでの可視化
3. **比較しやすさ**: 並列表示での比較機能
4. **詳細情報**: 推薦理由の透明性

---

## 技術スタック

### バックエンド
- **言語**: Python 3.11+
- **フレームワーク**: FastAPI
- **データベース**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **キャッシュ**: Redis
- **タスクキュー**: Celery

### フロントエンド
- **フレームワーク**: React 18 + TypeScript
- **状態管理**: Zustand
- **UI library**: Chakra UI
- **地図API**: Google Maps API
- **チャート**: Recharts

### インフラ
- **コンテナ**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **モニタリング**: Grafana + Prometheus
- **ログ**: ELK Stack

---

## 実装フェーズ（Claude主導開発）

### Phase 1: プロトタイプ構築（即座実行）
- [x] 映画.comクローリング機能
- [ ] 🤖 **インメモリDB + 基本最適化ロジック実装**
- [ ] 🤖 **React Webアプリケーション作成**
- [ ] 🤖 **映画選択→プラン生成の最小機能実装**

### Phase 2: DB統合版（次回セッション）
- [ ] 🤖 **SQLiteデータベース設計・実装**
- [ ] 🤖 **データ永続化機能**
- [ ] 🤖 **バックエンドAPI実装（FastAPI）**
- [ ] 🤖 **フロントエンドとAPI統合**

### Phase 3: 高度化版（その後のセッション）
- [ ] 🤖 **移動時間API統合（Google Maps等）**
- [ ] 🤖 **高度な最適化アルゴリズム実装**
- [ ] 🤖 **UI/UX改善・可視化強化**
- [ ] 🤖 **レスポンシブ対応・パフォーマンス最適化**

### Phase 4: 運用準備版（最終段階）
- [ ] 🤖 **エラーハンドリング・バリデーション強化**
- [ ] 🤖 **データ更新の自動化**
- [ ] 🤖 **Docker化・デプロイ準備**
- [ ] 🤖 **ドキュメント・テスト整備**

## 開発方針転換

### 🎯 Claude主導開発の特徴
1. **即座にプロトタイプ作成**: 今すぐ動作するものを実装
2. **段階的機能拡張**: 各セッションで実用性を向上
3. **完全なコード提供**: 人間は要件確認とテストのみ
4. **実データ活用**: 既にクローリング済みのデータを即活用

### 📝 今回のセッション実装予定
1. **データ構造設計**: 今回クローリングしたデータの構造化
2. **最適化ロジック**: 移動時間を考慮した推薦アルゴリズム
3. **Webアプリ作成**: React使用の完全動作アプリ
4. **統合テスト**: 実際のデータでの動作確認

### 🚀 次回以降の進化
- **セッション2**: データベース永続化とAPI化
- **セッション3**: 地図API統合と高度な最適化
- **セッション4**: 本格運用に向けた完成度向上

---

## 運用・保守

### データ更新
- **自動クローリング**: 毎日早朝に映画.comから最新データ取得
- **差分更新**: 変更があった情報のみ更新
- **データ品質チェック**: 異常値検出とアラート

### パフォーマンス監視
- **レスポンス時間**: API応答時間の監視
- **データベース**: クエリパフォーマンスの最適化
- **キャッシュ**: Redis使用率とヒット率

### 拡張計画
- **対応エリア拡大**: 渋谷、池袋などへの展開
- **個人化推薦**: ユーザー履歴に基づく推薦
- **SNS連携**: 友人との映画プラン共有

---

## まとめ

本システムは映画愛好家の「効率的に複数の映画を楽しみたい」というニーズに応える、移動最適化に特化した推薦システムです。技術的な実現可能性と実用性を両立させ、段階的な開発によってMVPから本格運用まで拡張可能な設計としています。