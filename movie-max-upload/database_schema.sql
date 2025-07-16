-- 映画最適化システム データベース設計
-- SQLite版 DDL (Data Definition Language)

-- 1. 映画館テーブル
CREATE TABLE theaters (
    theater_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    latitude REAL,
    longitude REAL,
    area TEXT DEFAULT 'shinjuku',
    screens INTEGER,
    facilities TEXT, -- JSON形式で保存
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 映画テーブル
CREATE TABLE movies (
    movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    duration INTEGER, -- 分単位
    rating TEXT, -- G, PG12, R15+, R18+
    genre TEXT, -- JSON配列形式
    description TEXT,
    director TEXT,
    cast TEXT, -- JSON配列形式
    release_date DATE,
    imdb_rating REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 上映スケジュールテーブル
CREATE TABLE showtimes (
    showtime_id INTEGER PRIMARY KEY AUTOINCREMENT,
    theater_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL,
    show_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME,
    screen_number INTEGER,
    price REAL DEFAULT 2000.0,
    special_format TEXT DEFAULT '通常', -- IMAX, 4DX, Dolby Atmos, etc.
    available_seats INTEGER,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (theater_id) REFERENCES theaters(theater_id),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
    UNIQUE(theater_id, show_date, start_time, screen_number)
);

-- 4. 映画館間距離テーブル
CREATE TABLE theater_distances (
    distance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_theater_id INTEGER NOT NULL,
    to_theater_id INTEGER NOT NULL,
    walking_minutes INTEGER,
    train_minutes INTEGER,
    taxi_minutes INTEGER,
    distance_km REAL,
    route_info TEXT, -- JSON形式
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_theater_id) REFERENCES theaters(theater_id),
    FOREIGN KEY (to_theater_id) REFERENCES theaters(theater_id),
    UNIQUE(from_theater_id, to_theater_id)
);

-- 5. 閲覧プランテーブル
CREATE TABLE viewing_plans (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    primary_showtime_id INTEGER NOT NULL,
    plan_data TEXT, -- JSON形式で全プラン詳細
    total_duration_minutes INTEGER,
    total_travel_minutes INTEGER,
    optimization_score REAL,
    plan_type TEXT DEFAULT 'before_after', -- before_after, before_only, after_only
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (primary_showtime_id) REFERENCES showtimes(showtime_id)
);

-- 6. プラン推薦テーブル
CREATE TABLE plan_recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    recommended_showtime_id INTEGER NOT NULL,
    recommendation_type TEXT NOT NULL, -- before, after
    confidence_score REAL DEFAULT 0.5, -- 0.0-1.0
    reason TEXT,
    sequence_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES viewing_plans(plan_id),
    FOREIGN KEY (recommended_showtime_id) REFERENCES showtimes(showtime_id)
);

-- 7. クローリングログテーブル
CREATE TABLE crawling_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    target_date DATE,
    area TEXT,
    total_theaters INTEGER,
    total_movies INTEGER,
    total_showtimes INTEGER,
    success_rate REAL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX idx_showtimes_theater_date ON showtimes(theater_id, show_date);
CREATE INDEX idx_showtimes_movie_date ON showtimes(movie_id, show_date);
CREATE INDEX idx_showtimes_date_time ON showtimes(show_date, start_time);
CREATE INDEX idx_theater_distances_from ON theater_distances(from_theater_id);
CREATE INDEX idx_theater_distances_to ON theater_distances(to_theater_id);
CREATE INDEX idx_viewing_plans_primary ON viewing_plans(primary_showtime_id);
CREATE INDEX idx_plan_recommendations_plan ON plan_recommendations(plan_id);

-- 更新時間自動更新のトリガー
CREATE TRIGGER update_theaters_timestamp 
    AFTER UPDATE ON theaters
    FOR EACH ROW
    BEGIN
        UPDATE theaters SET updated_at = CURRENT_TIMESTAMP WHERE theater_id = NEW.theater_id;
    END;

CREATE TRIGGER update_movies_timestamp 
    AFTER UPDATE ON movies
    FOR EACH ROW
    BEGIN
        UPDATE movies SET updated_at = CURRENT_TIMESTAMP WHERE movie_id = NEW.movie_id;
    END;

CREATE TRIGGER update_showtimes_timestamp 
    AFTER UPDATE ON showtimes
    FOR EACH ROW
    BEGIN
        UPDATE showtimes SET updated_at = CURRENT_TIMESTAMP WHERE showtime_id = NEW.showtime_id;
    END;

CREATE TRIGGER update_theater_distances_timestamp 
    AFTER UPDATE ON theater_distances
    FOR EACH ROW
    BEGIN
        UPDATE theater_distances SET updated_at = CURRENT_TIMESTAMP WHERE distance_id = NEW.distance_id;
    END;