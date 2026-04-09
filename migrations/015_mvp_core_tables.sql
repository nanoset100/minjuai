-- ============================================================
-- 정책AI MVP 핵심 테이블
-- 생성일: 2026-04-08
-- 포함: members, issues, issue_reactions, letters
-- ============================================================

-- ─── 1. 의원 정보 테이블 ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS members (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    mona_cd VARCHAR NOT NULL UNIQUE,        -- 국회 API 코드
    name VARCHAR NOT NULL,
    party VARCHAR,
    district VARCHAR NOT NULL,              -- "광주 광산구을" 형태
    city VARCHAR,                           -- "광주광역시" 정규화
    email VARCHAR,                          -- Assembly API 이메일
    homepage TEXT,
    tel VARCHAR,
    photo_url TEXT,
    is_active BOOLEAN DEFAULT true,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_members_district ON members (district);
CREATE INDEX IF NOT EXISTS idx_members_city ON members (city);

-- ─── 2. 이슈 테이블 ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS issues (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title VARCHAR NOT NULL,
    summary TEXT,                           -- 2-3문장 요약
    source_url TEXT,
    committee VARCHAR,                      -- 관련 위원회 키워드
    keywords TEXT[],                        -- 매핑 키워드 배열
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true          -- 비활성화 플래그
);

CREATE INDEX IF NOT EXISTS idx_issues_collected ON issues (collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_issues_committee ON issues (committee);

-- ─── 3. 이슈 × 의원 반응 테이블 ─────────────────────────────
CREATE TABLE IF NOT EXISTS issue_reactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
    member_id VARCHAR NOT NULL,             -- mona_cd 참조 (FK 없이 유연하게)
    stance VARCHAR NOT NULL CHECK (stance IN ('찬성', '반대', '침묵', '수집중')),
    confidence FLOAT CHECK (confidence BETWEEN 0.0 AND 1.0),
    summary TEXT,                           -- AI 요약 30자 이내
    evidence TEXT,                          -- 근거 발언 50자 이내
    data_date DATE NOT NULL,               -- 데이터 기준일 (신뢰도 표시용)
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (issue_id, member_id, data_date) -- 같은 날 중복 저장 방지
);

CREATE INDEX IF NOT EXISTS idx_reactions_issue ON issue_reactions (issue_id, data_date DESC);
CREATE INDEX IF NOT EXISTS idx_reactions_member ON issue_reactions (member_id);
CREATE INDEX IF NOT EXISTS idx_reactions_stance ON issue_reactions (stance);

-- ─── 4. 시민 편지 테이블 ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS letters (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    member_id VARCHAR NOT NULL,             -- mona_cd
    issue_id UUID REFERENCES issues(id),    -- 이슈 연결 (선택)
    content TEXT NOT NULL,
    nickname VARCHAR DEFAULT '시민',
    sender_district VARCHAR,                -- 시민 입력 지역구
    status VARCHAR DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'blocked', 'failed')),
    block_reason TEXT,                      -- 차단 이유
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_letters_member ON letters (member_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_letters_status ON letters (status, created_at DESC);

-- 편지 누적 카운터 뷰 (홈화면 표시용)
CREATE OR REPLACE VIEW letter_stats AS
SELECT
    COUNT(*) FILTER (WHERE status = 'sent') AS total_sent,
    COUNT(*) FILTER (WHERE status = 'sent' AND created_at >= NOW() - INTERVAL '7 days') AS sent_last_7days,
    COUNT(*) AS total_submitted
FROM letters;


-- ─── 5. 광주광역시 의원 시드 데이터 ──────────────────────────
-- Assembly API 조회 결과 (2026-04-08 기준)
-- 이메일: 의원 개인 등록 이메일 (공식 의원실 이메일 아님, 추후 검증 필요)

INSERT INTO members (mona_cd, name, party, district, city, email, homepage, tel, photo_url)
VALUES
    ('VRY5522V', '민형배', '더불어민주당', '광주 광산구을', '광주광역시',
     'mhb1961@naver.com', 'https://blog.naver.com/gjminsim', '02-6788-6426',
     'https://www.assembly.go.kr/static/portal/img/openassm/VRY5522V.jpg'),

    ('IWR8966I', '박균택', '더불어민주당', '광주 광산구갑', '광주광역시',
     '7849580@naver.com', NULL, '02-784-9580',
     'https://www.assembly.go.kr/static/portal/img/openassm/IWR8966I.jpg'),

    ('EB16073M', '안도걸', '더불어민주당', '광주 동구남구을', '광주광역시',
     'ahndogeol@naver.com', 'https://blog.naver.com/ahndogeol', '02-784-4441',
     'https://www.assembly.go.kr/static/portal/img/openassm/EB16073M.jpg'),

    ('CK143054', '양부남', '더불어민주당', '광주 서구을', '광주광역시',
     'ybn733@naver.com', NULL, '02-784-1422',
     'https://www.assembly.go.kr/static/portal/img/openassm/CK143054.jpg'),

    ('QUR40502', '전진숙', '더불어민주당', '광주 북구을', '광주광역시',
     '518jjs@naver.com', 'https://blog.naver.com/gwangjusook', '02-784-6120',
     'https://www.assembly.go.kr/static/portal/img/openassm/QUR40502.jpg'),

    ('IC499858', '정준호', '더불어민주당', '광주 북구갑', '광주광역시',
     'jjhgj0503@naver.com', 'https://blog.naver.com/cyclops53', '02-784-1091',
     'https://www.assembly.go.kr/static/portal/img/openassm/IC499858.jpg'),

    ('9HE7226N', '정진욱', '더불어민주당', '광주 동구남구갑', '광주광역시',
     'chungco518@gmail.com', 'https://blog.naver.com/chungchinookofficial', '02-784-2570',
     'https://www.assembly.go.kr/static/portal/img/openassm/9HE7226N.jpg'),

    ('ZKB18611', '조인철', '더불어민주당', '광주 서구갑', '광주광역시',
     '2024iccho@gmail.com', 'https://blog.naver.com/iccho19', '02-784-8191',
     'https://www.assembly.go.kr/static/portal/img/openassm/ZKB18611.jpg')

ON CONFLICT (mona_cd) DO UPDATE SET
    email = EXCLUDED.email,
    homepage = EXCLUDED.homepage,
    tel = EXCLUDED.tel,
    updated_at = NOW();
