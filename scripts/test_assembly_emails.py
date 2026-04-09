"""
Assembly API 이메일 테스트
광주 8개 지역구 의원 이메일 주소 확인
→ Case A (API 이메일 사용) / B (수동 수집) / C (홈페이지 URL) 결정
"""

import sys
import os
import json
import httpx
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

ASSEMBLY_API_KEY = os.getenv("ASSEMBLY_API_KEY", "9803e6a51c334322ace8627791ce36a9")
BASE_URL = "https://open.assembly.go.kr/portal/openapi"

# 광주 지역구 키워드
GWANGJU_KEYWORDS = ["광주"]

def fetch_all_lawmakers():
    """22대 국회의원 전체 조회"""
    url = f"{BASE_URL}/nwvrqwxyaytdsfvhu"
    all_rows = []

    for page in range(1, 5):
        params = {
            "Key": ASSEMBLY_API_KEY,
            "Type": "json",
            "pIndex": page,
            "pSize": 100,
            "AGE": 22,
        }
        try:
            resp = httpx.get(url, params=params, timeout=30)
            data = resp.json()
            api_data = data.get("nwvrqwxyaytdsfvhu", {})
            if isinstance(api_data, list) and len(api_data) >= 2:
                rows = api_data[1].get("row", [])
                if not rows:
                    break
                all_rows.extend(rows)

                head = api_data[0].get("head", [])
                total = 0
                for h in head:
                    if "list_total_count" in h:
                        total = h["list_total_count"]
                        break
                if len(all_rows) >= total:
                    break
            else:
                break
        except Exception as e:
            print(f"  API 오류 (page {page}): {e}")
            break

    return all_rows

def main():
    print("=" * 60)
    print("  Assembly API 광주 의원 이메일 테스트")
    print("=" * 60)

    print("\n[1] API 호출 중...")
    rows = fetch_all_lawmakers()
    print(f"    전체 의원 {len(rows)}명 조회됨")

    # 광주 필터링
    gwangju = []
    for row in rows:
        district = row.get("ORIG_NM", "")
        if "광주" in district:
            gwangju.append({
                "name": row.get("HG_NM", ""),
                "party": row.get("POLY_NM", ""),
                "district": district,
                "election_type": row.get("ELECT_GBN_NM", ""),
                "email": row.get("E_MAIL", ""),
                "homepage": row.get("HOMEPAGE", ""),
                "tel": row.get("TEL_NO", ""),
                "mona_cd": row.get("MONA_CD", ""),
            })

    print(f"\n[2] 광주 의원 {len(gwangju)}명 발견")
    print()

    # 이메일 현황 분석
    has_email = [m for m in gwangju if m["email"] and "@" in m["email"]]
    no_email_has_homepage = [m for m in gwangju if (not m["email"] or "@" not in m["email"]) and m["homepage"]]
    no_email_no_homepage = [m for m in gwangju if (not m["email"] or "@" not in m["email"]) and not m["homepage"]]

    print("┌─────────────────────────────────────────────────────────┐")
    print("│  이름        │ 정당     │ 지역구        │ 이메일               │")
    print("├─────────────────────────────────────────────────────────┤")
    for m in gwangju:
        email_display = m["email"] if m["email"] else f"(없음) → {m['homepage'][:30] if m['homepage'] else '홈페이지도 없음'}"
        print(f"│  {m['name']:<6} │ {m['party']:<8} │ {m['district']:<13} │ {email_display:<20} │")
    print("└─────────────────────────────────────────────────────────┘")

    print(f"\n[3] 이메일 현황 분석")
    print(f"    [OK] 이메일 보유: {len(has_email)}명 -> Case A (API 이메일 직접 사용)")
    print(f"    [--] 이메일 없음 + 홈페이지 있음: {len(no_email_has_homepage)}명 -> Case C (홈페이지 URL)")
    print(f"    [XX] 이메일 없음 + 홈페이지도 없음: {len(no_email_no_homepage)}명 -> Case B (수동 수집 필요)")

    # 판정
    print()
    if len(has_email) >= 6:
        print("[GREEN] 판정: Case A 가능 -- API 이메일로 편지 발송 구현 시작")
    elif len(has_email) >= 3:
        print("[YELLOW] 판정: 혼합 -- 이메일 있는 의원은 A, 나머지는 C로 처리")
    else:
        print("[RED] 판정: Case B/C -- 이메일 수동 수집 또는 홈페이지 URL 방식 필요")

    # JSON 저장
    output = {
        "tested_at": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_gwangju": len(gwangju),
        "has_email_count": len(has_email),
        "no_email_count": len(gwangju) - len(has_email),
        "lawmakers": gwangju
    }

    output_path = os.path.join(os.path.dirname(__file__), "gwangju_lawmakers.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] 결과 저장: {output_path}")

if __name__ == "__main__":
    main()
