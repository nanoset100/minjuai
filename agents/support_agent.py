#!/usr/bin/env python3
"""
AI 정당 고객지원팀 에이전트
24/7 자동 상담 챗봇
- GPT-4o mini 사용 (비용 최적화)
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from openai import AsyncOpenAI
from dotenv import load_dotenv
from loguru import logger

load_dotenv(Path(__file__).parent.parent / "config" / ".env")


class SupportAgent:
    """
    고객지원 AI 에이전트

    기능:
    - 24/7 챗봇 상담
    - FAQ 자동 응답
    - 문의 분류 및 처리
    - 복잡한 문의는 사람에게 에스컬레이션
    - 응답 캐싱 (동일/유사 질문 API 호출 절감)
    """

    # 캐시 설정
    CACHE_TTL_HOURS = 24       # 캐시 유효시간
    CACHE_MAX_SIZE = 200       # 최대 캐시 항목 수

    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "").strip())
        self.model = "gpt-4o-mini"
        self.party_name = os.getenv("PARTY_NAME", "민주AI")

        # FAQ 데이터베이스
        self.faq = self.load_faq()

        # 시스템 프롬프트
        self._system_prompt = self._build_system_prompt()

        # 문의 이력
        self.inquiry_history = []

        # 응답 캐시: {hash: {"response": ..., "expires_at": datetime}}
        self._response_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_hits = 0
        self._cache_misses = 0

        logger.info(f"💬 {self.party_name} 고객지원 에이전트 초기화 (GPT-4o mini + 24h 캐시)")

    def _build_system_prompt(self) -> str:
        """시스템 프롬프트 생성"""
        faq_text = "\n\n".join(
            f"[{key}]\n{value.strip()}" for key, value in self.faq.items()
        )

        return (
            f"당신은 '{self.party_name}' 정당의 친절한 고객지원 AI입니다.\n\n"
            "역할:\n"
            "- 시민들의 질문에 정확하고 친절하게 답변\n"
            "- 정당의 비전과 정책을 설명\n"
            "- 참여 방법 안내\n"
            '- 복잡한 질문은 "담당자가 확인 후 연락드리겠습니다" 답변\n\n'
            "톤:\n"
            "- 친근하고 존중하는 태도\n"
            "- 전문적이지만 어렵지 않게\n\n"
            "중요:\n"
            "- 거짓 정보 절대 금지\n"
            "- 모르면 솔직히 인정\n"
            "- 정치적 중립성 유지\n\n"
            "=== FAQ 데이터베이스 ===\n"
            "아래 FAQ를 참고하여 답변하세요. FAQ에 있는 내용은 그대로 활용하되,\n"
            "추가 설명이 필요하면 보충하세요.\n\n"
            f"{faq_text}"
        )

    def load_faq(self) -> Dict[str, str]:
        """FAQ 데이터 로드"""
        return {
            "당원가입": """
당원 가입 방법:
1. 웹사이트 방문 (ai-party.kr)
2. '당원가입' 버튼 클릭
3. 기본 정보 입력 (이름, 이메일, 전화번호)
4. 이메일 인증
5. 가입 완료!

가입비: 무료
당비: 월 1,000원 (선택)
""",
            "정책제안": """
정책 제안 방법:
1. 로그인 후 '정책 제안하기' 클릭
2. 카테고리 선택 (경제, 복지, 환경 등)
3. 제안 내용 작성
4. 제출하면 AI가 24시간 내 분석
5. 실현가능성 높으면 전문가 검토
6. 당원 투표로 최종 결정

누구나 제안 가능합니다!
""",
            "후원방법": """
후원 방법:
1. 웹사이트 '후원하기' 메뉴
2. 금액 선택 또는 직접 입력
3. 결제 방법 선택:
   - 신용카드
   - 계좌이체
   - 간편결제 (카카오페이 등)
4. 영수증 자동 발급

모든 후원금은 투명하게 공개됩니다.
""",
            "AI정당": """
AI 정당이란?
- AI가 모든 업무를 자동화하여 효율적 운영
- 사람이 최종 결정, AI는 보조 역할
- 24/7 시민과 소통
- 데이터 기반 정책 개발
- 완전한 투명성

AI가 정치인을 대체하는 것이 아니라,
시민의 목소리를 더 잘 듣고 반영하기 위한 도구입니다.
""",
            "선거목표": """
2028년 4월 국회의원 선거 목표:
- 총 10석 당선
- 지역구: 3석
- 비례대표: 7석

우리의 전략:
1. 투명한 정책 플랫폼
2. 시민 참여 극대화
3. 데이터 기반 선거 운동
4. 지역 밀착형 활동
"""
        }

    async def chat(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """사용자 메시지에 응답"""
        if conversation_history is None:
            conversation_history = []

        # 1. 메시지 분류
        category = await self.classify_message(user_message)

        # 2. FAQ로 답변 가능한지 확인
        if category in self.faq:
            confidence = 0.95
            response_text = self.faq[category]
            requires_human = False
        else:
            # 3. AI로 응답 생성
            response = await self.generate_response(
                user_message,
                conversation_history,
                category
            )
            response_text = response['text']
            confidence = response['confidence']
            requires_human = response['requires_human']

        # 4. 문의 로그 저장
        inquiry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'category': category,
            'response': response_text,
            'confidence': confidence,
            'requires_human': requires_human
        }
        self.inquiry_history.append(inquiry)

        if requires_human:
            logger.warning(f"🚨 사람 검토 필요: {category} - 확신도 {confidence:.2f}")

        return {
            'text': response_text,
            'category': category,
            'confidence': confidence,
            'requires_human': requires_human,
            'timestamp': inquiry['timestamp']
        }

    async def classify_message(self, message: str) -> str:
        """메시지 분류"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['가입', '회원', '당원']):
            return '당원가입'
        elif any(word in message_lower for word in ['정책', '제안', '아이디어']):
            return '정책제안'
        elif any(word in message_lower for word in ['후원', '기부', '돈']):
            return '후원방법'
        elif any(word in message_lower for word in ['ai', '인공지능', '자동화']):
            return 'AI정당'
        elif any(word in message_lower for word in ['선거', '후보', '국회의원']):
            return '선거목표'
        else:
            return '일반문의'

    # ─── 캐싱 시스템 ───

    def _cache_key(self, message: str, category: str) -> str:
        """메시지+카테고리로 캐시 키 생성 (소문자 정규화)"""
        normalized = f"{category}:{message.strip().lower()}"
        return hashlib.md5(normalized.encode()).hexdigest()

    def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """캐시에서 응답 조회 (TTL 초과 시 None)"""
        entry = self._response_cache.get(key)
        if entry and datetime.now() < entry["expires_at"]:
            self._cache_hits += 1
            logger.debug(f"💾 캐시 HIT (총 {self._cache_hits}회)")
            return entry["response"]
        if entry:
            del self._response_cache[key]  # 만료된 항목 제거
        self._cache_misses += 1
        return None

    def _set_cached(self, key: str, response: Dict[str, Any]):
        """캐시에 응답 저장"""
        # 캐시 크기 제한: 초과 시 가장 오래된 항목 제거
        if len(self._response_cache) >= self.CACHE_MAX_SIZE:
            oldest_key = min(self._response_cache, key=lambda k: self._response_cache[k]["expires_at"])
            del self._response_cache[oldest_key]

        self._response_cache[key] = {
            "response": response,
            "expires_at": datetime.now() + timedelta(hours=self.CACHE_TTL_HOURS),
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        total = self._cache_hits + self._cache_misses
        return {
            "cache_size": len(self._response_cache),
            "max_size": self.CACHE_MAX_SIZE,
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_rate": round(self._cache_hits / max(total, 1) * 100, 1),
            "estimated_savings": f"~${self._cache_hits * 0.0003:.4f}",
        }

    # ─── AI 응답 생성 ───

    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict],
        category: str
    ) -> Dict[str, Any]:
        """GPT-4o mini로 응답 생성 (캐시 우선)"""

        # 대화 이력이 없는 단독 질문만 캐싱 (맥락 의존 질문은 캐싱 X)
        use_cache = len(conversation_history) == 0
        cache_key = self._cache_key(user_message, category) if use_cache else None

        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                return cached

        messages = [{"role": "system", "content": self._system_prompt}]

        for msg in conversation_history[-5:]:
            messages.append({"role": "user", "content": msg.get('user', '')})
            messages.append({"role": "assistant", "content": msg.get('assistant', '')})

        messages.append({"role": "user", "content": user_message})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=1000,
                messages=messages,
            )

            response_text = response.choices[0].message.content
            confidence = 0.8

            requires_human = any(word in user_message.lower() for word in [
                '불만', '항의', '환불', '법률', '소송'
            ]) or confidence < 0.7

            result = {
                'text': response_text,
                'confidence': confidence,
                'requires_human': requires_human
            }

            # 캐시 저장 (에스컬레이션 필요 없는 일반 응답만)
            if use_cache and not requires_human:
                self._set_cached(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"❌ 응답 생성 실패: {e}")
            return {
                'text': "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                'confidence': 0.0,
                'requires_human': True
            }

    def get_daily_stats(self) -> Dict[str, Any]:
        """일일 통계"""
        today_inquiries = [
            inq for inq in self.inquiry_history
            if inq['timestamp'].startswith(datetime.now().strftime('%Y-%m-%d'))
        ]

        return {
            'total_inquiries': len(today_inquiries),
            'auto_resolved': len([inq for inq in today_inquiries if not inq['requires_human']]),
            'human_required': len([inq for inq in today_inquiries if inq['requires_human']]),
            'categories': {}
        }


async def test_chatbot():
    """챗봇 테스트"""
    agent = SupportAgent()

    test_messages = [
        "안녕하세요! 당원 가입하고 싶은데 어떻게 하나요?",
        "AI 정당이 뭔가요?",
        "정책 제안은 어떻게 하나요?",
        "2028년 선거 목표가 어떻게 되나요?"
    ]

    logger.info("🧪 챗봇 테스트 시작")
    for msg in test_messages:
        print(f"👤 사용자: {msg}")
        response = await agent.chat(msg)
        print(f"🤖 챗봇: {response['text']}")
        print("-" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_chatbot())
