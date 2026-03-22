#!/usr/bin/env python3
"""
AI 정당 웹 백엔드 API
FastAPI 기반 + Supabase 연동
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import sys
from pathlib import Path

# 에이전트 임포트
sys.path.insert(0, str(Path(__file__).parent))
from agents.support_agent import SupportAgent
from agents.analytics_agent import AnalyticsAgent
from agents.policy_agent import PolicyAgent
from agents.monitoring_agent import MonitoringAgent
from agents.marketing_agent import MarketingAgent
from agents.batch_helper import BatchHelper
from db import supabase_admin

# FastAPI 앱
app = FastAPI(
    title="AI 정당 API",
    description="1인 AI 정당 운영 시스템 API — Supabase 연동",
    version="0.2.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 도메인 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 에이전트 (7개)
support_agent = SupportAgent()          # 1. 챗봇
analytics_agent = AnalyticsAgent()      # 2. 데이터분석
policy_agent = PolicyAgent()            # 3. 정책분석
monitoring_agent = MonitoringAgent()    # 4. 의정활동 감시
marketing_agent = MarketingAgent()      # 5. SNS 마케팅
batch_helper = BatchHelper()            # 6. 배치 처리 (비용절감)


# ============== 모델 정의 ==============

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict]] = None

class ChatResponse(BaseModel):
    text: str
    category: str
    confidence: float
    requires_human: bool
    timestamp: str

class PolicyProposal(BaseModel):
    title: str
    description: str
    category: str
    proposer_name: Optional[str] = None
    proposer_email: Optional[str] = None

class MemberJoin(BaseModel):
    name: str
    email: str
    phone: str
    region: Optional[str] = None
    age_group: Optional[str] = None

class VoteRequest(BaseModel):
    proposal_id: str
    member_id: str
    vote_type: str  # "for" or "against"


# ============== 루트 ==============

@app.get("/")
async def root():
    return {
        "message": "AI 정당 API에 오신 것을 환영합니다!",
        "version": "0.2.0",
        "database": "Supabase PostgreSQL",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "chat": "/api/chat",
            "status": "/api/status",
            "policies": "/api/policies",
            "stats": "/api/stats",
            "members": "/api/members/join",
        }
    }


@app.get("/api/status")
async def get_status():
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "database": "Supabase (PostgreSQL)",
        "services": {
            "chatbot": "운영 중",
            "website": "운영 중",
            "database": "Supabase 연동 완료",
            "ai_agents": "운영 중"
        }
    }


# ============== 회원 ==============

@app.post("/api/members/join")
async def join_member(member: MemberJoin):
    try:
        result = supabase_admin.table("members").insert({
            "name": member.name,
            "email": member.email,
            "phone": member.phone,
            "region": member.region,
            "age_group": member.age_group,
            "auth_provider": "direct",
        }).execute()

        new_member = result.data[0]
        return {
            "status": "success",
            "message": f"{member.name}님, 환영합니다!",
            "member_id": new_member["id"],
            "next_steps": [
                "프로필을 완성해주세요",
                "첫 정책 투표에 참여해보세요"
            ]
        }
    except Exception as e:
        if "duplicate key" in str(e):
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/members/stats")
async def get_member_stats():
    try:
        result = supabase_admin.table("members").select("*").execute()
        members = result.data
        total = len(members)

        # 지역별 집계
        region_counts = {}
        for m in members:
            r = m.get("region") or "미지정"
            region_counts[r] = region_counts.get(r, 0) + 1

        return {
            "total": total,
            "by_region": region_counts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 챗봇 ==============

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await support_agent.chat(
            user_message=request.message,
            conversation_history=request.conversation_history
        )
        return ChatResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/faq")
async def get_faq():
    return {
        "faq": support_agent.faq,
        "categories": list(support_agent.faq.keys())
    }


# ============== 정책 ==============

@app.get("/api/policies")
async def get_policies():
    try:
        result = supabase_admin.table("proposals").select("*").order("created_at", desc=True).execute()
        proposals = result.data

        # 각 정책의 투표 수 집계
        for p in proposals:
            votes_result = supabase_admin.table("votes").select("vote_type").eq("proposal_id", p["id"]).execute()
            votes = votes_result.data
            p["votes_for"] = sum(1 for v in votes if v["vote_type"] == "for")
            p["votes_against"] = sum(1 for v in votes if v["vote_type"] == "against")

        return {"policies": proposals, "total": len(proposals)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/policies/{proposal_id}")
async def get_policy_detail(proposal_id: str):
    try:
        result = supabase_admin.table("proposals").select("*").eq("id", proposal_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="정책을 찾을 수 없습니다.")

        policy = result.data[0]
        votes_result = supabase_admin.table("votes").select("vote_type").eq("proposal_id", proposal_id).execute()
        votes = votes_result.data
        policy["votes_for"] = sum(1 for v in votes if v["vote_type"] == "for")
        policy["votes_against"] = sum(1 for v in votes if v["vote_type"] == "against")

        return policy
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/policies")
async def create_policy(proposal: PolicyProposal):
    try:
        result = supabase_admin.table("proposals").insert({
            "title": proposal.title,
            "description": proposal.description,
            "category": proposal.category,
            "status": "검토중",
        }).execute()

        new_proposal = result.data[0]
        return {
            "status": "submitted",
            "message": "정책 제안이 접수되었습니다.",
            "proposal": new_proposal,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/policies/{proposal_id}/analyze")
async def analyze_policy(proposal_id: str):
    try:
        # DB에서 정책 조회
        result = supabase_admin.table("proposals").select("*").eq("id", proposal_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="정책을 찾을 수 없습니다.")

        proposal = result.data[0]

        # PolicyAgent로 AI 분석
        analysis = policy_agent.analyze_proposal_data(
            title=proposal["title"],
            description=proposal["description"],
            category=proposal["category"]
        )

        # 분석 결과 DB 업데이트
        supabase_admin.table("proposals").update({
            "status": "분석완료",
            "feasibility_score": analysis.get("feasibility_score", 0),
            "analysis": analysis,
        }).eq("id", proposal_id).execute()

        return {"status": "analyzed", "analysis": analysis}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 투표 ==============

@app.post("/api/policies/{proposal_id}/vote")
async def vote_policy(proposal_id: str, vote: VoteRequest):
    try:
        result = supabase_admin.table("votes").insert({
            "proposal_id": proposal_id,
            "member_id": vote.member_id,
            "vote_type": vote.vote_type,
        }).execute()

        return {"status": "voted", "message": "투표가 완료되었습니다."}
    except Exception as e:
        if "duplicate key" in str(e) or "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail="이미 투표하셨습니다.")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/policies/{proposal_id}/votes")
async def get_votes(proposal_id: str):
    try:
        result = supabase_admin.table("votes").select("vote_type").eq("proposal_id", proposal_id).execute()
        votes = result.data
        return {
            "proposal_id": proposal_id,
            "votes_for": sum(1 for v in votes if v["vote_type"] == "for"),
            "votes_against": sum(1 for v in votes if v["vote_type"] == "against"),
            "total": len(votes),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 분석 ==============

@app.get("/api/stats")
async def get_stats():
    try:
        # DB에서 실제 회원 수 조회
        members_result = supabase_admin.table("members").select("id", count="exact").execute()
        proposals_result = supabase_admin.table("proposals").select("id", count="exact").execute()

        member_count = members_result.count or 0
        proposal_count = proposals_result.count or 0

        return {
            "members": {"total": member_count},
            "policies": {"total": proposal_count},
            "social": {"twitter_followers": 0},
            "support": {"avg_response_time": "3초"}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/trends")
async def get_trends():
    try:
        trends = await analytics_agent.analyze_trends()
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/predictions")
async def get_predictions():
    try:
        predictions = await analytics_agent.predict_election_outcome()
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/report")
async def get_analytics_report():
    try:
        report = await analytics_agent.generate_analytics_report()
        return {"report": report, "generated_at": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 국회의원 모니터링 ==============

@app.get("/api/lawmakers")
async def get_lawmakers():
    try:
        result = supabase_admin.table("lawmakers").select("*").execute()
        return {"lawmakers": result.data, "total": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/lawmakers/{lawmaker_id}")
async def get_lawmaker_detail(lawmaker_id: str):
    try:
        result = supabase_admin.table("lawmakers").select("*").eq("id", lawmaker_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="국회의원을 찾을 수 없습니다.")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 의정활동 모니터링 (MonitoringAgent) ==============

@app.get("/api/monitoring/stats")
async def get_monitoring_stats():
    """전체 의정활동 모니터링 통계"""
    try:
        return monitoring_agent.get_monitoring_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/vulnerable")
async def get_vulnerable_districts():
    """취약 지역구 Top 10"""
    try:
        return monitoring_agent.find_vulnerable_districts(10)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/lawmaker/{lawmaker_id}")
async def analyze_lawmaker(lawmaker_id: str):
    """특정 의원 상세 분석"""
    try:
        result = monitoring_agent.analyze_lawmaker(lawmaker_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/strategy/{lawmaker_id}")
async def get_attack_strategy(lawmaker_id: str):
    """의원 공략 전략 생성"""
    try:
        result = monitoring_agent.get_attack_strategy(lawmaker_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 마케팅 (MarketingAgent) ==============

@app.get("/api/marketing/stats")
async def get_marketing_stats():
    """마케팅 성과 통계"""
    try:
        return marketing_agent.get_performance_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/marketing/report")
async def get_marketing_report():
    """마케팅 리포트"""
    try:
        report = marketing_agent.get_marketing_report()
        return {"report": report, "generated_at": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 에이전트 대시보드 ==============

@app.get("/api/agents")
async def get_agents_status():
    """7개 AI 에이전트 현황 대시보드"""
    try:
        return {
            "total_agents": 7,
            "agents": [
                {
                    "id": "orchestrator",
                    "name": "오케스트레이터",
                    "role": "총괄 지휘관",
                    "description": "7개 에이전트를 조정하고 자동 스케줄링 실행",
                    "status": "operational",
                    "features": ["일일 브리핑", "주간 전략", "자동 스케줄링", "에이전트 조정"],
                },
                {
                    "id": "support",
                    "name": "서포트 챗봇",
                    "role": "시민 상담",
                    "description": "24시간 AI 챗봇으로 정책 문의 및 당원 상담",
                    "status": "active",
                    "features": ["실시간 대화", "FAQ 자동 응답", "카테고리 분류", "대화 기록"],
                },
                {
                    "id": "policy",
                    "name": "정책 분석가",
                    "role": "정책 분석",
                    "description": "AI가 정책의 실현 가능성, 예산, 장단점을 분석",
                    "status": "active",
                    "features": ["실현가능성 점수", "예산 추정", "장단점 분석", "권고사항"],
                },
                {
                    "id": "analytics",
                    "name": "데이터 분석가",
                    "role": "데이터 분석",
                    "description": "당원 통계, 트렌드 분석, 선거 예측",
                    "status": "active",
                    "features": ["실시간 통계", "트렌드 분석", "선거 예측", "지역별 분석"],
                },
                {
                    "id": "monitoring",
                    "name": "의정 감시관",
                    "role": "국회의원 모니터링",
                    "description": "국회의원 의정활동 감시 및 취약 지역구 발굴",
                    "status": "active",
                    "features": ["출석률 추적", "공약 이행 감시", "취약도 분석", "공략 전략"],
                },
                {
                    "id": "marketing",
                    "name": "마케팅 매니저",
                    "role": "SNS 마케팅",
                    "description": "트위터/인스타 콘텐츠 자동 생성 및 스케줄링",
                    "status": "active",
                    "features": ["콘텐츠 자동 생성", "해시태그 최적화", "포스팅 스케줄", "성과 추적"],
                },
                {
                    "id": "batch",
                    "name": "비용 절감기",
                    "role": "비용 최적화",
                    "description": "Batch API로 비실시간 작업 50% 비용 절감",
                    "status": "active",
                    "features": ["50% 비용 절감", "주간 전략 배치", "대용량 처리", "자동 스케줄"],
                },
            ],
            "system": {
                "uptime_days": (datetime.now() - datetime(2026, 2, 2)).days,
                "status": "operational",
                "cost_optimization": "Batch API 50% + Prompt Caching 90%",
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 정적 파일 서빙 (웹 프론트엔드) ==============

@app.get("/manifest.json")
async def manifest():
    return FileResponse(Path(__file__).parent / "manifest.json")

@app.get("/sw.js")
async def service_worker():
    return FileResponse(Path(__file__).parent / "sw.js", media_type="application/javascript")

@app.get("/app")
async def serve_frontend():
    return FileResponse(Path(__file__).parent / "index.html")

@app.get("/privacy")
async def privacy_policy():
    return FileResponse(Path(__file__).parent / "privacy_policy.html")


# 서버 실행
if __name__ == "__main__":
    import uvicorn

    print("AI 정당 API 서버 시작...")
    print("웹사이트: http://localhost:8000/app")
    print("API 문서: http://localhost:8000/docs")
    print("DB: Supabase PostgreSQL")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )
