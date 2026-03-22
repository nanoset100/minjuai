"""
AI Client Abstraction Layer
- 현재: OpenAI GPT-4o mini
- 나중에 모델 교체 시 이 파일만 수정하면 됨
"""
import os
from openai import OpenAI

# 설정
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # openai, anthropic, gemini
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")

_client = None

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def ai_call(
    prompt: str,
    system: str = "",
    max_tokens: int = 1000,
    model: str = None,
) -> str:
    """
    AI API 통합 호출 함수
    - prompt: 사용자 메시지
    - system: 시스템 프롬프트
    - max_tokens: 최대 출력 토큰
    - model: 모델 오버라이드 (기본: AI_MODEL 환경변수)
    """
    client = get_client()
    use_model = model or AI_MODEL

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=use_model,
        max_tokens=max_tokens,
        messages=messages,
    )
    return response.choices[0].message.content
