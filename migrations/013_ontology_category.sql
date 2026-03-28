-- ============================================================
-- 민주AI 온톨로지 Phase 3: category 컬럼 추가
-- 52개 policy_topics 분류 체계 연동
-- ============================================================

-- STEP 1: ontology_nodes에 category 컬럼 추가
ALTER TABLE ontology_nodes
ADD COLUMN IF NOT EXISTS category TEXT;

-- STEP 2: 기존 30개 노드에 category = '복지' 설정
UPDATE ontology_nodes
SET category = '복지'
WHERE category IS NULL;

-- STEP 3: ontology_nodes의 type CHECK 제약 업데이트
-- 기존: issue, policy, evidence, cause, effect, stakeholder, global_case
-- 변경 없음 — issue와 policy는 이미 포함되어 있음
