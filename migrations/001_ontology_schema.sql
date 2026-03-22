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
