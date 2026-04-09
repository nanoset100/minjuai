"""
letter_service.py
시민 → 의원 편지 발송 서비스

흐름:
  1. 편지 내용 GPT 스팸 필터 (100자 미만 / 욕설 / 허위사실)
  2. Supabase letters 테이블 저장 (status=pending)
  3. SendGrid 이메일 발송
  4. status=sent 업데이트 + sent_at 기록
  5. 누적 카운터 반환 (전달됨 화면용)
"""

import os
import json
import httpx
from datetime import datetime, timezone
from typing import Optional
from openai import OpenAI

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
LETTER_FROM_EMAIL = os.getenv("LETTER_FROM_EMAIL", "noreply@jeongchaek.ai")
LETTER_FROM_NAME = os.getenv("LETTER_FROM_NAME", "정책AI 시민편지")

# GPT 스팸 필터 프롬프트 (CLAUDE.md 지정)
LETTER_FILTER_PROMPT = """
다음 편지가 의원실 발송에 적합한지 판단하세요.

편지: {content}

차단 기준 (하나라도 해당되면 blocked=true):
- 욕설, 비속어, 혐오 표현
- 특정인에 대한 명백한 허위 사실
- 스팸성 반복 내용 또는 무의미한 텍스트
- 100자 미만의 너무 짧은 내용

JSON으로만 응답:
{{"blocked": true/false, "reason": "차단 이유 (blocked일 때만)"}}
"""

# 이메일 본문 템플릿 (CLAUDE.md 지정)
EMAIL_BODY_TEMPLATE = """안녕하세요, {member_name} 의원님.
정책AI 플랫폼을 통해 지역구 시민의 편지가 전달됩니다.

---
보낸 사람: {nickname} ({sender_district} 시민)
관련 정책: {issue_title}

{content}
---

정책AI(jeongchaek.ai) 시민 참여 플랫폼을 통해 발송됐습니다.
회신은 이 이메일로 보내주시면 시민에게 전달됩니다.
"""


class LetterService:
    def __init__(self):
        self.openai = OpenAI(api_key=OPENAI_API_KEY)
        self.sb_headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
        }

    # ─── Supabase 헬퍼 ────────────────────────────────────────

    def _sb_get(self, table: str, query: str = "") -> list:
        url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
        resp = httpx.get(url, headers=self.sb_headers, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def _sb_insert(self, table: str, row: dict) -> dict:
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        headers = {**self.sb_headers, "Prefer": "return=representation"}
        resp = httpx.post(url, headers=headers, json=row, timeout=20)
        resp.raise_for_status()
        result = resp.json()
        return result[0] if isinstance(result, list) else result

    def _sb_update(self, table: str, row_id: str, data: dict) -> None:
        url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{row_id}"
        resp = httpx.patch(url, headers=self.sb_headers, json=data, timeout=20)
        resp.raise_for_status()

    # ─── 스팸 필터 ────────────────────────────────────────────

    def filter_letter(self, content: str) -> dict:
        """GPT 스팸 필터. 반환: {"blocked": bool, "reason": str|None}"""
        # 100자 미만 즉시 차단 (GPT 호출 절약)
        if len(content.strip()) < 100:
            return {"blocked": True, "reason": "100자 미만의 너무 짧은 내용입니다"}

        try:
            prompt = LETTER_FILTER_PROMPT.format(content=content[:1000])
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100,
            )
            raw = response.choices[0].message.content.strip()
            if "```" in raw:
                raw = raw.split("```")[1].replace("json", "").strip()
            return json.loads(raw)
        except Exception as e:
            print(f"[LetterService] 스팸 필터 오류: {e}")
            # 필터 오류 시 통과 (오류로 인한 차단 방지)
            return {"blocked": False, "reason": None}

    # ─── 의원 정보 조회 ──────────────────────────────────────

    def get_member(self, mona_cd: str) -> Optional[dict]:
        rows = self._sb_get("members", f"?mona_cd=eq.{mona_cd}&limit=1")
        return rows[0] if rows else None

    def get_issue(self, issue_id: str) -> Optional[dict]:
        rows = self._sb_get("issues", f"?id=eq.{issue_id}&limit=1")
        return rows[0] if rows else None

    # ─── SendGrid 이메일 발송 ────────────────────────────────

    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
    ) -> bool:
        """SendGrid API로 이메일 발송. 성공 시 True 반환"""
        if not SENDGRID_API_KEY:
            print("[LetterService] SENDGRID_API_KEY 없음 — 발송 건너뜀")
            return False

        payload = {
            "personalizations": [{"to": [{"email": to_email, "name": to_name}]}],
            "from": {"email": LETTER_FROM_EMAIL, "name": LETTER_FROM_NAME},
            "reply_to": {"email": LETTER_FROM_EMAIL, "name": LETTER_FROM_NAME},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        }

        try:
            resp = httpx.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {SENDGRID_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=20,
            )
            if resp.status_code == 202:
                return True
            else:
                print(f"[LetterService] SendGrid 오류 {resp.status_code}: {resp.text[:200]}")
                return False
        except Exception as e:
            print(f"[LetterService] 이메일 발송 예외: {e}")
            return False

    # ─── 메인: 편지 제출 ─────────────────────────────────────

    def submit_letter(
        self,
        mona_cd: str,
        content: str,
        nickname: str = "시민",
        sender_district: str = "",
        issue_id: Optional[str] = None,
    ) -> dict:
        """
        편지 제출 엔드포인트에서 호출.
        반환: {"success": bool, "letter_id": str, "total_sent": int, "blocked": bool, "reason": str}
        """
        # 1. 의원 정보 조회
        member = self.get_member(mona_cd)
        if not member:
            return {"success": False, "error": f"의원 정보를 찾을 수 없습니다: {mona_cd}"}

        # 2. 이슈 정보 조회 (선택)
        issue_title = "일반 정책"
        if issue_id:
            issue = self.get_issue(issue_id)
            if issue:
                issue_title = issue["title"]

        # 3. 스팸 필터
        filter_result = self.filter_letter(content)
        if filter_result.get("blocked"):
            # 차단된 편지도 DB에 기록 (통계 목적)
            self._sb_insert("letters", {
                "member_id": mona_cd,
                "issue_id": issue_id,
                "content": content[:500],
                "nickname": nickname,
                "sender_district": sender_district,
                "status": "blocked",
                "block_reason": filter_result.get("reason"),
            })
            return {
                "success": False,
                "blocked": True,
                "reason": filter_result.get("reason"),
            }

        # 4. DB 저장 (pending)
        letter = self._sb_insert("letters", {
            "member_id": mona_cd,
            "issue_id": issue_id,
            "content": content,
            "nickname": nickname,
            "sender_district": sender_district,
            "status": "pending",
        })
        letter_id = letter["id"]

        # 5. 이메일 발송
        body = EMAIL_BODY_TEMPLATE.format(
            member_name=member["name"],
            nickname=nickname,
            sender_district=sender_district or "광주",
            issue_title=issue_title,
            content=content,
        )
        subject = f"[정책AI 시민편지] {member['name']} 의원님께"
        sent = self.send_email(
            to_email=member["email"],
            to_name=f"{member['name']} 의원실",
            subject=subject,
            body=body,
        )

        # 6. 상태 업데이트
        now = datetime.now(timezone.utc).isoformat()
        if sent:
            self._sb_update("letters", letter_id, {"status": "sent", "sent_at": now})
        else:
            self._sb_update("letters", letter_id, {"status": "failed"})

        # 7. 누적 카운터 조회
        stats = self._sb_get("letter_stats")
        total_sent = stats[0]["total_sent"] if stats else 0

        return {
            "success": sent,
            "letter_id": letter_id,
            "total_sent": total_sent,
            "member_name": member["name"],
            "sent_at": now if sent else None,
            "blocked": False,
        }
