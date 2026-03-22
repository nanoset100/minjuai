-- 시민 제보 테이블
CREATE TABLE IF NOT EXISTS district_reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    district TEXT NOT NULL,
    mona_cd TEXT NOT NULL,
    report_type TEXT NOT NULL CHECK (report_type IN ('현안', '사진', '기사', '평가', '공약', '예산')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    news_url TEXT,
    photo_urls JSONB DEFAULT '[]',
    user_name TEXT DEFAULT '익명 시민',
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    status TEXT DEFAULT 'published' CHECK (status IN ('published', 'review', 'deleted')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 시민 평점 테이블
CREATE TABLE IF NOT EXISTS district_ratings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    district TEXT NOT NULL,
    mona_cd TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 1 AND score <= 5),
    comment TEXT DEFAULT '',
    user_name TEXT DEFAULT '익명 시민',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_reports_district ON district_reports(district);
CREATE INDEX IF NOT EXISTS idx_reports_mona_cd ON district_reports(mona_cd);
CREATE INDEX IF NOT EXISTS idx_reports_created ON district_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ratings_district ON district_ratings(district);
CREATE INDEX IF NOT EXISTS idx_ratings_mona_cd ON district_ratings(mona_cd);

-- RLS 비활성화 (백엔드에서 service key 사용)
ALTER TABLE district_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE district_ratings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for service role" ON district_reports FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON district_ratings FOR ALL USING (true);
