-- ============================================================
-- 민주AI 온톨로지 Phase 1: pgvector + report_node_links
-- 최종본 v2.0 (2026-03-27)
-- 검토: Claude Opus 4.6 + ChatGPT + Grok 종합 반영
-- ============================================================

-- ============ STEP 1: pgvector 확장 활성화 ============
-- Supabase Free Plan에서 무료 사용 가능
CREATE EXTENSION IF NOT EXISTS vector;


-- ============ STEP 2: ontology_nodes에 임베딩 컬럼 추가 ============
-- text-embedding-3-small 출력 차원: 1536
ALTER TABLE ontology_nodes
ADD COLUMN IF NOT EXISTS embedding vector(1536);


-- ============ STEP 3: report_node_links 테이블 생성 ============
-- 설계 원칙: 지식 그래프(ontology)와 시민 데이터(reports) 완전 분리
-- 3개 AI 만장일치 합의
CREATE TABLE IF NOT EXISTS report_node_links (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- FK: 제보 <-> 노드 연결
    report_id UUID NOT NULL REFERENCES district_reports(id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES ontology_nodes(id) ON DELETE CASCADE,

    -- AI 매칭 결과
    relevance FLOAT DEFAULT 0.0 CHECK (relevance BETWEEN 0 AND 1),
    match_reason TEXT,                              -- 매칭 이유 설명
    ai_match_version TEXT DEFAULT 'gpt-4o-mini',    -- 모델 변경 추적

    -- 시민 검증 (외부 검토 반영: upvotes/downvotes 분리)
    verify_upvotes INTEGER DEFAULT 0,               -- "맞아요" 수
    verify_downvotes INTEGER DEFAULT 0,             -- "아니에요" 수
    last_verified_at TIMESTAMPTZ,

    -- 메타
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- 중복 매칭 방지
    UNIQUE(report_id, node_id)
);

-- 양방향 조회 인덱스
CREATE INDEX IF NOT EXISTS idx_rnl_report ON report_node_links(report_id);
CREATE INDEX IF NOT EXISTS idx_rnl_node ON report_node_links(node_id);
CREATE INDEX IF NOT EXISTS idx_rnl_relevance ON report_node_links(relevance DESC);


-- ============ STEP 4: district_reports에 상태 컬럼 추가 ============
ALTER TABLE district_reports
ADD COLUMN IF NOT EXISTS ontology_status TEXT DEFAULT 'pending';
-- 상태값: pending, matched, unmatched, filtered, error


-- ============ STEP 5: node_candidates 테이블 생성 ============
-- 매칭 실패 시 키워드 수집 -> 온톨로지 유기적 성장
CREATE TABLE IF NOT EXISTS node_candidates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    keyword TEXT NOT NULL,
    raw_text_snippet TEXT,                          -- 원본 텍스트 일부
    first_report_id UUID REFERENCES district_reports(id),  -- 외부 검토 반영: 최초 제보 추적
    report_count INTEGER DEFAULT 1,
    embedding vector(1536),                         -- pgvector 중복 방지용
    status TEXT DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'node_created')),
    created_node_id UUID REFERENCES ontology_nodes(id), -- 승인 후 생성된 노드 참조
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);


-- ============ STEP 6: pgvector 인덱스 ============
-- 외부 검토 반영: 현재 30~150개 노드 수준에서는 IVFFlat 불필요
-- 순차 탐색(Exact Search)이 100% 정확도 + 더 빠름
-- TODO: 노드 10,000개 이상 시 아래 인덱스 활성화
-- CREATE INDEX idx_nodes_embedding ON ontology_nodes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX idx_candidates_embedding ON node_candidates USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);


-- ============ STEP 7: RLS 정책 ============
ALTER TABLE report_node_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE node_candidates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for service role" ON report_node_links FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON node_candidates FOR ALL USING (true);


-- ============ STEP 8: pgvector 유사도 검색 함수 ============
-- 서버에서 supabase_admin.rpc("match_ontology_nodes", {...}) 로 호출
CREATE OR REPLACE FUNCTION match_ontology_nodes(
    query_embedding vector(1536),
    match_threshold FLOAT DEFAULT 0.3,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    type TEXT,
    name TEXT,
    description TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        on_node.id,
        on_node.type,
        on_node.name,
        on_node.description,
        1 - (on_node.embedding <=> query_embedding) AS similarity
    FROM ontology_nodes on_node
    WHERE on_node.embedding IS NOT NULL
    AND 1 - (on_node.embedding <=> query_embedding) > match_threshold
    ORDER BY on_node.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


-- node_candidates 중복 검사용 함수
CREATE OR REPLACE FUNCTION find_similar_candidates(
    query_embedding vector(1536),
    similarity_threshold FLOAT DEFAULT 0.85
)
RETURNS TABLE (
    id UUID,
    keyword TEXT,
    report_count INTEGER,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        nc.id,
        nc.keyword,
        nc.report_count,
        1 - (nc.embedding <=> query_embedding) AS similarity
    FROM node_candidates nc
    WHERE nc.embedding IS NOT NULL
    AND nc.status = 'pending'
    AND 1 - (nc.embedding <=> query_embedding) > similarity_threshold
    ORDER BY nc.embedding <=> query_embedding
    LIMIT 1;
END;
$$;


-- ============ 완료 확인 쿼리 (실행 후 검증용) ============
-- 아래 쿼리를 별도로 실행하여 마이그레이션 성공 확인:
--
-- SELECT
--     (SELECT count(*) FROM information_schema.columns
--      WHERE table_name = 'ontology_nodes' AND column_name = 'embedding') AS has_embedding,
--     (SELECT count(*) FROM information_schema.tables
--      WHERE table_name = 'report_node_links') AS has_rnl,
--     (SELECT count(*) FROM information_schema.tables
--      WHERE table_name = 'node_candidates') AS has_nc,
--     (SELECT count(*) FROM information_schema.columns
--      WHERE table_name = 'district_reports' AND column_name = 'ontology_status') AS has_status;
-- 결과: 모두 1이면 성공
