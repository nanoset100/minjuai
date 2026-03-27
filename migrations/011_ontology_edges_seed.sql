-- ============================================================
-- 기존 30개 온톨로지 노드 간 엣지(관계) 생성
-- 2026.03.26
-- ============================================================

-- ========== 1. 정책 → 이슈 (solves: 정책이 이슈를 해결) ==========

-- 포괄적 복지 시스템 구축 → 고령화 복지 부담
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('eeecb1e5-5af5-4c95-935c-d1bfb3428d78', '5f3deac2-008e-4a2a-8546-9a29307497d4', 'solves', 0.8, '포괄적 복지 시스템으로 고령화 복지 부담 해결', 0.8);

-- 포괄적 복지 시스템 구축 → 저출산 인력 부족
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('eeecb1e5-5af5-4c95-935c-d1bfb3428d78', '1fccdca9-4152-468e-8d5a-a198297dfc1d', 'solves', 0.7, '아동수당 등으로 저출산 문제 대응', 0.7);

-- 포괄적 복지 시스템 구축 → 사회적 불평등 확대
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('eeecb1e5-5af5-4c95-935c-d1bfb3428d78', '67d115fd-cc22-4f05-9273-00f8122ec4cd', 'solves', 0.7, '사회적 불평등 해소 목적 포함', 0.7);

-- 통합 복지 증진 정책 → 노인복지 부족
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('45ca1830-add3-4dcb-bc91-c705c1a1917c', '5baee187-89ba-4d4f-8388-3a1d0fff0c3e', 'solves', 0.9, '노인복지 개편이 핵심 목적', 0.8);

-- 통합 복지 증진 정책 → 저출산 문제
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('45ca1830-add3-4dcb-bc91-c705c1a1917c', 'ffb63770-4784-4bcc-8855-a5d51a52a9e0', 'solves', 0.7, '저출산 문제 종합 해결 포함', 0.7);

-- 포용적 복지 시스템 구축 → 청년 실업 및 주거
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('3a3e6168-8b2e-4f83-af26-d5dfa22f05ff', 'a93d193f-3cd7-4a56-b033-cdd4a5d1b770', 'solves', 0.9, '청년·저소득층 집중 지원 정책', 0.8);

-- 포용적 복지 시스템 구축 → 소득 불평등
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('3a3e6168-8b2e-4f83-af26-d5dfa22f05ff', 'b1975cd6-185b-44c8-8607-ed5eec9c9651', 'solves', 0.8, '소득 불평등 해결이 핵심 목적', 0.8);


-- ========== 2. 이슈 → 이슈 (causes: 원인-결과) ==========

-- 저출산 → 고령화 복지 부담 가속
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('ffb63770-4784-4bcc-8855-a5d51a52a9e0', '5f3deac2-008e-4a2a-8546-9a29307497d4', 'causes', 0.9, '저출산이 고령화를 가속시켜 복지 부담 증가', 0.9);

-- 사회적 불평등 → 지역 간 복지 격차
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('67d115fd-cc22-4f05-9273-00f8122ec4cd', '6769c2f7-32cb-4ba8-9981-88daf1b0adaf', 'causes', 0.8, '사회적 불평등이 지역 간 격차로 이어짐', 0.8);

-- 소득 불평등 → 청년 실업 및 주거 문제
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('b1975cd6-185b-44c8-8607-ed5eec9c9651', 'a93d193f-3cd7-4a56-b033-cdd4a5d1b770', 'causes', 0.7, '소득 격차가 청년층 주거 문제를 악화', 0.7);

-- 저출산 인력 부족 → 고령화 사회 대응 필요성 증가
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('1fccdca9-4152-468e-8d5a-a198297dfc1d', '4370d871-eac8-4ac0-8ddd-0b9b0b6a6a18', 'causes', 0.8, '인력 부족이 고령화 대응을 더 시급하게 만듦', 0.8);


-- ========== 3. 이슈 ↔ 이슈 (similar_to: 유사 이슈) ==========

-- 고령화 복지 부담 ↔ 고령화 사회 대응
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('5f3deac2-008e-4a2a-8546-9a29307497d4', '4370d871-eac8-4ac0-8ddd-0b9b0b6a6a18', 'similar_to', 0.9, '같은 고령화 문제의 다른 측면', 0.9);

-- 저출산 인력 부족 ↔ 저출산 문제
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('1fccdca9-4152-468e-8d5a-a198297dfc1d', 'ffb63770-4784-4bcc-8855-a5d51a52a9e0', 'similar_to', 0.9, '같은 저출산 문제의 다른 측면', 0.9);

-- 사회적 불평등 ↔ 소득 불평등
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('67d115fd-cc22-4f05-9273-00f8122ec4cd', 'b1975cd6-185b-44c8-8607-ed5eec9c9651', 'similar_to', 0.85, '불평등 문제의 서로 다른 측면', 0.85);

-- 노인복지 부족 ↔ 고령화 사회 대응
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('5baee187-89ba-4d4f-8388-3a1d0fff0c3e', '4370d871-eac8-4ac0-8ddd-0b9b0b6a6a18', 'similar_to', 0.85, '고령화 관련 이슈', 0.85);


-- ========== 4. 해외 사례 → 정책/이슈 (evidence_for: 근거 제공) ==========

-- 스웨덴 보편적 복지 → 포괄적 복지 시스템
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('08114f05-ce01-4d25-85de-c5f5dfd7fe23', 'eeecb1e5-5af5-4c95-935c-d1bfb3428d78', 'evidence_for', 0.85, '스웨덴 보편적 복지가 포괄적 시스템의 근거', 0.85);

-- 스웨덴 사회복지 시스템 → 통합 복지 증진 정책
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('82b4c435-f368-4d5d-a309-919313794378', '45ca1830-add3-4dcb-bc91-c705c1a1917c', 'evidence_for', 0.8, '스웨덴 모델을 참고한 정책', 0.8);

-- 핀란드 기본소득 실험 → 통합 복지 증진 정책
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('05368f88-5a4d-483d-a221-0ef959e1a4f9', '45ca1830-add3-4dcb-bc91-c705c1a1917c', 'evidence_for', 0.75, '핀란드 모델을 참고한 정책', 0.75);

-- 일본 고령자 복지 → 고령화 사회 대응 (이슈)
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('5c6ccdd5-d8cc-4078-8697-1ef73ac2a598', '4370d871-eac8-4ac0-8ddd-0b9b0b6a6a18', 'evidence_for', 0.8, '일본의 고령화 대응 사례가 참고 근거', 0.8);

-- 일본 노인 복지 증진 → 노인복지 부족 (이슈)
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('b472356a-c598-49c2-a759-ffbe493b4c61', '5baee187-89ba-4d4f-8388-3a1d0fff0c3e', 'evidence_for', 0.8, '일본 노인복지 사례가 한국 문제의 근거', 0.8);

-- 독일 연금 개혁 → 노인복지 부족 (이슈)
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('508f2b26-e422-47e3-ab27-189ece02b364', '5baee187-89ba-4d4f-8388-3a1d0fff0c3e', 'evidence_for', 0.75, '독일 연금 개혁이 노인복지 개선의 근거', 0.75);

-- 영국 복지 축소 → 사회적 불평등 확대 (실패 사례)
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('ff9fc3c9-3108-40aa-8fd5-c231f7c310e3', '67d115fd-cc22-4f05-9273-00f8122ec4cd', 'evidence_for', 0.85, '영국 복지 축소가 불평등 심화의 반면교사', 0.85);

-- 독일 사회적 보호법 → 소득 불평등 (이슈)
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('ed783f1a-76a3-446c-8d33-2dee538ed965', 'b1975cd6-185b-44c8-8607-ed5eec9c9651', 'evidence_for', 0.7, '독일 사회적 보호법이 소득 불평등 해결 근거', 0.7);

-- 프랑스 최저임금 → 소득 불평등 (이슈)
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('4e6a509e-2910-4f98-b580-f90b3527763a', 'b1975cd6-185b-44c8-8607-ed5eec9c9651', 'evidence_for', 0.7, '프랑스 최저임금 정책이 소득 격차 해결 근거', 0.7);

-- 독일 구직자 수당 → 청년 실업 및 주거 (이슈)
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('3f33e6a4-8b45-45cf-a2b1-dd110fce3398', 'a93d193f-3cd7-4a56-b033-cdd4a5d1b770', 'evidence_for', 0.7, '독일 구직자 수당이 청년 실업 해결 참고 사례', 0.7);

-- 노르웨이 노동자 복지 → 포용적 복지 시스템
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('0395a297-27c9-4604-884c-f24f1dfff1c2', '3a3e6168-8b2e-4f83-af26-d5dfa22f05ff', 'evidence_for', 0.7, '노르웨이 노동자 복지가 포용적 시스템의 근거', 0.7);

-- 캐나다 의료 시스템 → 포괄적 복지 시스템
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('88ed29a3-0e27-4214-997f-395df52424bd', 'eeecb1e5-5af5-4c95-935c-d1bfb3428d78', 'evidence_for', 0.7, '캐나다 의료 모델이 포괄적 복지의 근거', 0.7);


-- ========== 5. 정책 ↔ 정책 (synergy_with: 시너지) ==========

-- 포괄적 복지 ↔ 통합 복지 (서로 보완)
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('eeecb1e5-5af5-4c95-935c-d1bfb3428d78', '45ca1830-add3-4dcb-bc91-c705c1a1917c', 'synergy_with', 0.8, '두 정책이 서로 보완하여 복지 확대 가능', 0.8);

-- 통합 복지 ↔ 포용적 복지 (서로 보완)
INSERT INTO ontology_edges (from_node_id, to_node_id, relation_type, strength, description, ai_confidence) VALUES
('45ca1830-add3-4dcb-bc91-c705c1a1917c', '3a3e6168-8b2e-4f83-af26-d5dfa22f05ff', 'synergy_with', 0.75, '노인 복지와 청년 복지가 함께 작동해야 효과적', 0.75);


-- ============================================================
-- 총 27개 엣지 생성
-- solves: 7개 (정책→이슈)
-- causes: 4개 (이슈→이슈)
-- similar_to: 4개 (이슈↔이슈)
-- evidence_for: 10개 (해외사례→정책/이슈)
-- synergy_with: 2개 (정책↔정책)
-- ============================================================
