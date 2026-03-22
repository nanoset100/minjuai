
-- ========== 001_ontology_schema.sql ==========
-- ============================================================
-- 민주AI 정책 온톨로지 스키마 v1.0
-- 2026.03.22
-- ============================================================

-- 1. 52개 정책 분야
CREATE TABLE IF NOT EXISTS policy_topics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    week_number INTEGER NOT NULL UNIQUE CHECK (week_number BETWEEN 1 AND 52),
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    category_group TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 주간 정책 연구
CREATE TABLE IF NOT EXISTS weekly_research (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    topic_id UUID REFERENCES policy_topics(id),
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    cycle INTEGER DEFAULT 1,
    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'researching', 'draft', 'review', 'finalized')),
    phase TEXT DEFAULT 'mon_select' CHECK (phase IN ('mon_select', 'tue_wed_global', 'thu_draft', 'fri_sat_review', 'sun_finalize')),
    korea_status JSONB DEFAULT '{}',
    global_comparison JSONB DEFAULT '{}',
    policy_draft TEXT,
    policy_final TEXT,
    feasibility_score FLOAT,
    budget_estimate TEXT,
    expected_effect TEXT,
    citizen_votes_for INTEGER DEFAULT 0,
    citizen_votes_against INTEGER DEFAULT 0,
    citizen_comments_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    finalized_at TIMESTAMPTZ,
    UNIQUE(year, week_number)
);

-- 3. 온톨로지 노드 (지식 그래프)
CREATE TABLE IF NOT EXISTS ontology_nodes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('issue', 'policy', 'evidence', 'cause', 'effect', 'stakeholder', 'global_case')),
    name TEXT NOT NULL,
    description TEXT,
    data JSONB DEFAULT '{}',
    research_id UUID REFERENCES weekly_research(id),
    country TEXT,
    source_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 온톨로지 관계 (엣지)
CREATE TABLE IF NOT EXISTS ontology_edges (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    from_node_id UUID REFERENCES ontology_nodes(id) ON DELETE CASCADE,
    to_node_id UUID REFERENCES ontology_nodes(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL CHECK (relation_type IN ('causes', 'solves', 'conflicts_with', 'synergy_with', 'requires', 'affects', 'evidence_for', 'similar_to')),
    strength FLOAT DEFAULT 0.5 CHECK (strength BETWEEN 0 AND 1),
    description TEXT,
    ai_confidence FLOAT DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. 글로벌 정책 사례
CREATE TABLE IF NOT EXISTS global_cases (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    country TEXT NOT NULL,
    country_code TEXT,
    policy_area TEXT NOT NULL,
    policy_name TEXT NOT NULL,
    year_started INTEGER,
    description TEXT,
    outcome TEXT CHECK (outcome IN ('success', 'partial', 'failure')),
    outcome_detail TEXT,
    key_metrics JSONB DEFAULT '{}',
    lessons_learned TEXT,
    applicability_to_korea TEXT,
    source_urls JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. 시민 의견
CREATE TABLE IF NOT EXISTS citizen_opinions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    research_id UUID REFERENCES weekly_research(id),
    member_id UUID,
    opinion_type TEXT NOT NULL CHECK (opinion_type IN ('support', 'oppose', 'modify')),
    content TEXT NOT NULL,
    ai_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. 에이전트 활동 로그
CREATE TABLE IF NOT EXISTS agent_activities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT,
    status TEXT DEFAULT 'success' CHECK (status IN ('success', 'error', 'running')),
    result_summary TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_weekly_research_status ON weekly_research(status);
CREATE INDEX IF NOT EXISTS idx_weekly_research_year_week ON weekly_research(year, week_number);
CREATE INDEX IF NOT EXISTS idx_ontology_nodes_type ON ontology_nodes(type);
CREATE INDEX IF NOT EXISTS idx_ontology_edges_from ON ontology_edges(from_node_id);
CREATE INDEX IF NOT EXISTS idx_ontology_edges_to ON ontology_edges(to_node_id);
CREATE INDEX IF NOT EXISTS idx_ontology_edges_relation ON ontology_edges(relation_type);
CREATE INDEX IF NOT EXISTS idx_global_cases_area ON global_cases(policy_area);
CREATE INDEX IF NOT EXISTS idx_agent_activities_agent ON agent_activities(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_activities_created ON agent_activities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_citizen_opinions_research ON citizen_opinions(research_id);


-- ========== 002_seed_policy_topics.sql ==========
-- ============================================================
-- 52개 정책 분야 시드 데이터
-- 1년 52주 = 52개 분야 로테이션
-- ============================================================

INSERT INTO policy_topics (week_number, name, description, icon, category_group) VALUES
-- 경제 분야 (1~6)
(1, '경제·일자리', '거시경제 정책, 고용 창출, 산업 경쟁력', 'work', '경제'),
(2, '중소기업·소상공인', '중소기업 육성, 소상공인 보호, 창업 생태계', 'store', '경제'),
(3, '부동산·주거', '주택 정책, 전세 제도, 공공주택, 도시 재생', 'home', '경제'),
(4, '금융·세제', '세금 정책, 금융 규제, 가계부채, 자산 불평등', 'account_balance', '경제'),
(5, '디지털·AI', 'AI 산업 육성, 디지털 전환, 데이터 경제, 플랫폼 규제', 'computer', '경제'),
(6, '에너지·자원', '에너지 전환, 원전 정책, 신재생 에너지, 자원 안보', 'bolt', '경제'),

-- 사회 분야 (7~18)
(7, '교육', '공교육 혁신, 입시 개혁, 교육 격차, 평생 학습', 'school', '사회'),
(8, '청년', '청년 고용, 주거, 결혼·출산, 세대 갈등', 'people', '사회'),
(9, '고령화·노인', '초고령사회 대비, 연금, 돌봄, 노인 일자리', 'elderly_woman', '사회'),
(10, '저출생·육아', '출산율 제고, 보육 서비스, 일·가정 양립', 'child_care', '사회'),
(11, '의료·건강', '건강보험, 의료 접근성, 공공의료, 정신건강', 'local_hospital', '사회'),
(12, '복지', '기본소득, 사회안전망, 장애인 복지, 기초생활', 'volunteer_activism', '사회'),
(13, '노동·근로', '최저임금, 근로시간, 비정규직, 산업안전', 'engineering', '사회'),
(14, '여성·평등', '성평등, 유리천장, 경력단절, 젠더 폭력', 'balance', '사회'),
(15, '이민·다문화', '외국인 노동자, 다문화 가정, 이민 정책, 난민', 'public', '사회'),
(16, '장애인·소수자', '장애인 권리, 접근성, 소수자 보호, 차별 금지', 'accessibility', '사회'),
(17, '문화·예술', '문화 정책, 예술인 지원, 콘텐츠 산업, 한류', 'palette', '사회'),
(18, '스포츠·체육', '생활체육, 엘리트 스포츠, 체육 시설, e스포츠', 'sports_soccer', '사회'),

-- 정치·행정 분야 (19~26)
(19, '지방분권·균형발전', '수도권 집중, 지방 소멸, 행정 분권, 재정 자주', 'map', '정치'),
(20, '법·사법', '사법 개혁, 법원 독립, 검찰 권한, 국민 참여 재판', 'gavel', '정치'),
(21, '국방·안보', '군사력, 병역 제도, 사이버 안보, 방위산업', 'shield', '정치'),
(22, '외교·통일', '한반도 평화, 북한 정책, 외교 전략, 동맹 관계', 'handshake', '정치'),
(23, '미디어·언론', '언론 자유, 가짜뉴스, 미디어 리터러시, 공영방송', 'newspaper', '정치'),
(24, '선거·정치개혁', '선거 제도, 정당 구조, 정치 자금, 국회 개혁', 'how_to_vote', '정치'),
(25, '행정·공공', '정부 효율화, 공무원 제도, 전자정부, 규제 개혁', 'account_balance_wallet', '정치'),
(26, '부패·투명성', '반부패, 공직자 윤리, 내부고발, 공공데이터 공개', 'visibility', '정치'),

-- 환경·인프라 분야 (27~34)
(27, '기후변화·환경', '탄소중립, 기후 위기, 환경 규제, 그린뉴딜', 'eco', '환경'),
(28, '교통', '대중교통, 자율주행, 교통 혼잡, 물류', 'directions_bus', '환경'),
(29, '농업·어업', '식량 안보, 스마트팜, 농촌 활성화, 수산업', 'agriculture', '환경'),
(30, '재난·안전', '자연재해, 산업재해, 감염병, 안전 관리', 'warning', '환경'),
(31, '과학·기술', 'R&D 투자, 기초과학, 우주산업, 바이오', 'science', '환경'),
(32, '도시·건축', '스마트시티, 도시재생, 건축 규제, 공공시설', 'location_city', '환경'),
(33, '해양·영토', '해양 경제, 영토 관리, 해양 환경, 도서 지역', 'sailing', '환경'),
(34, '산림·생태', '산림 보전, 생태계 보호, 동물 복지, 국립공원', 'forest', '환경'),

-- 미래 분야 (35~42)
(35, '인공지능·로봇', 'AI 윤리, 자동화 일자리, 로봇 규제, AI 거버넌스', 'smart_toy', '미래'),
(36, '바이오·생명', '유전자 편집, 바이오산업, 생명윤리, 신약 개발', 'biotech', '미래'),
(37, '우주·항공', '우주 산업, 위성, 항공 규제, 우주 자원', 'rocket_launch', '미래'),
(38, '블록체인·핀테크', '가상자산 규제, CBDC, 핀테크, 탈중앙화', 'currency_bitcoin', '미래'),
(39, '메타버스·XR', '가상현실, 디지털 트윈, 메타버스 경제, XR 교육', 'view_in_ar', '미래'),
(40, '양자컴퓨팅', '양자 기술, 암호화, 양자 인터넷, 기술 주권', 'memory', '미래'),
(41, '자율주행·모빌리티', '자율주행 법제, UAM, 모빌리티 혁신, 공유 경제', 'directions_car', '미래'),
(42, '사이버보안', '사이버 위협, 개인정보, 디지털 주권, 해킹 방어', 'security', '미래'),

-- 생활 분야 (43~52)
(43, '소비자·물가', '물가 안정, 소비자 보호, 공정거래, 독점 규제', 'shopping_cart', '생활'),
(44, '관광', '관광 산업, 지역 관광, 의료 관광, 관광 인프라', 'luggage', '생활'),
(45, '반려동물·동물복지', '동물 보호법, 반려 산업, 동물 실험, 유기동물', 'pets', '생활'),
(46, '식품·안전', '식품 안전, 먹거리 정의, GMO, 학교 급식', 'restaurant', '생활'),
(47, '주민자치·참여', '주민 참여, 마을 공동체, 직접 민주주의, 시민 사회', 'groups', '생활'),
(48, '가족·사회구조', '가족 형태 변화, 1인 가구, 비혼, 공동체 주거', 'family_restroom', '생활'),
(49, '중독·정신건강', '게임·도박·알코올 중독, 정신건강, 자살 예방', 'psychology', '생활'),
(50, '통신·인터넷', '통신비, 5G/6G, 디지털 격차, 망 중립성', 'wifi', '생활'),
(51, '유산·전통', '문화유산 보전, 전통 산업, 역사 교육, 무형유산', 'museum', '생활'),
(52, '통일 대비', '통일 비용, 북한 이해, 탈북민, 남북 교류, 거버넌스 OS', 'flag', '생활')
ON CONFLICT (week_number) DO NOTHING;

