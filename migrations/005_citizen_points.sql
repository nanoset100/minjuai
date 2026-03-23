-- 시민 감시관 포인트 테이블
CREATE TABLE IF NOT EXISTS citizen_points (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_name TEXT NOT NULL UNIQUE,
    total_points INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1 CHECK (level >= 1 AND level <= 5),
    level_name TEXT DEFAULT '견습 감시자',
    report_count INTEGER DEFAULT 0,
    rating_count INTEGER DEFAULT 0,
    vote_received INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 포인트 활동 기록
CREATE TABLE IF NOT EXISTS citizen_point_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_name TEXT NOT NULL,
    action TEXT NOT NULL,
    points INTEGER NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_citizen_points_user ON citizen_points(user_name);
CREATE INDEX IF NOT EXISTS idx_citizen_points_total ON citizen_points(total_points DESC);
CREATE INDEX IF NOT EXISTS idx_citizen_points_level ON citizen_points(level DESC);
CREATE INDEX IF NOT EXISTS idx_point_logs_user ON citizen_point_logs(user_name);
CREATE INDEX IF NOT EXISTS idx_point_logs_created ON citizen_point_logs(created_at DESC);

-- RLS
ALTER TABLE citizen_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE citizen_point_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for service role" ON citizen_points FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON citizen_point_logs FOR ALL USING (true);
