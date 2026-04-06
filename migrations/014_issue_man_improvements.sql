-- ─── 이슈맨 AI 개선 마이그레이션 ───────────────────────────────────────
-- 1. source_type 컬럼 추가 (시민 제보 vs AI 수집 뉴스 분리)
-- 2. news_url unique 인덱스 (재시작 후 중복 등록 방지)

-- 1) source_type 컬럼 추가
ALTER TABLE district_reports
    ADD COLUMN IF NOT EXISTS source_type TEXT DEFAULT 'citizen'
    CHECK (source_type IN ('citizen', 'ai_news'));

-- 기존 이슈맨AI 데이터 자동 마킹
UPDATE district_reports
    SET source_type = 'ai_news'
    WHERE user_name = '이슈맨AI' AND source_type = 'citizen';

-- 2) news_url unique 인덱스 (NULL은 중복 허용 - 시민 제보는 URL 없음)
CREATE UNIQUE INDEX IF NOT EXISTS idx_reports_news_url_unique
    ON district_reports (news_url)
    WHERE news_url IS NOT NULL;

-- 3) source_type 인덱스 (탭 필터링 성능)
CREATE INDEX IF NOT EXISTS idx_reports_source_type
    ON district_reports (source_type, created_at DESC);
