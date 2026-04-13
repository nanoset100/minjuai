-- ============================================================
-- 문의기능: letters 테이블 컬럼 추가 + 응답률 뷰 생성
-- 생성일: 2026-04-13
-- ============================================================

-- ─── 1. letters 테이블 컬럼 추가 ─────────────────────────────

ALTER TABLE letters
  ADD COLUMN IF NOT EXISTS letter_type VARCHAR DEFAULT 'letter'
    CHECK (letter_type IN ('letter', 'inquiry')),
  ADD COLUMN IF NOT EXISTS citizen_email VARCHAR,
  ADD COLUMN IF NOT EXISTS reply_status VARCHAR DEFAULT 'pending'
    CHECK (reply_status IN ('pending', 'replied', 'no_reply')),
  ADD COLUMN IF NOT EXISTS reply_content TEXT,
  ADD COLUMN IF NOT EXISTS reply_received_at TIMESTAMPTZ;

-- ─── 2. 인덱스 ───────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_letters_type
  ON letters (letter_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_letters_reply_status
  ON letters (member_id, reply_status);

-- ─── 3. 의원별 응답률 뷰 ─────────────────────────────────────

CREATE OR REPLACE VIEW member_reply_rates AS
SELECT
    member_id,
    COUNT(*) FILTER (WHERE letter_type = 'inquiry' AND status = 'sent')    AS total_inquiries,
    COUNT(*) FILTER (WHERE letter_type = 'inquiry' AND reply_status = 'replied') AS total_replied,
    ROUND(
        COUNT(*) FILTER (WHERE letter_type = 'inquiry' AND reply_status = 'replied')::numeric
        / NULLIF(
            COUNT(*) FILTER (WHERE letter_type = 'inquiry' AND status = 'sent'), 0
          ) * 100,
        1
    ) AS reply_rate_pct
FROM letters
GROUP BY member_id;

-- ─── 4. 기존 letter_stats 뷰 업데이트 ───────────────────────
-- 편지/문의 각각 카운터 추가

CREATE OR REPLACE VIEW letter_stats AS
SELECT
    COUNT(*) FILTER (WHERE status = 'sent')                              AS total_sent,
    COUNT(*) FILTER (WHERE status = 'sent' AND letter_type = 'letter')  AS letters_sent,
    COUNT(*) FILTER (WHERE status = 'sent' AND letter_type = 'inquiry') AS inquiries_sent,
    COUNT(*) FILTER (WHERE status = 'sent'
                       AND created_at >= NOW() - INTERVAL '7 days')     AS sent_last_7days,
    COUNT(*)                                                             AS total_submitted
FROM letters;
