-- AI 온톨로지 태그 컬럼 추가
-- district_reports 테이블에 ontology_tags 컬럼 추가
ALTER TABLE district_reports ADD COLUMN IF NOT EXISTS ontology_tags JSONB DEFAULT NULL;

-- proposals 테이블에 ontology_tags 컬럼 추가
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS ontology_tags JSONB DEFAULT NULL;

-- 인덱스 (태그 기반 검색용)
CREATE INDEX IF NOT EXISTS idx_reports_ontology ON district_reports USING GIN (ontology_tags);
CREATE INDEX IF NOT EXISTS idx_proposals_ontology ON proposals USING GIN (ontology_tags);
