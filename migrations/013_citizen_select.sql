-- 민주AI Phase 5: 시민 직접 이슈 선택 컬럼 추가
-- report_node_links에 시민 선택 여부 + 매칭 주체 추가

ALTER TABLE report_node_links
ADD COLUMN IF NOT EXISTS citizen_selected BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS matched_by TEXT DEFAULT 'ai';
-- matched_by: 'ai' (자동매칭), 'citizen' (시민직접선택)

-- district_reports.ontology_status에 'citizen_none' 값 허용 (해당 없음 선택)
COMMENT ON COLUMN report_node_links.citizen_selected IS '시민이 직접 선택한 매칭인지 여부';
COMMENT ON COLUMN report_node_links.matched_by IS '매칭 주체: ai 또는 citizen';
