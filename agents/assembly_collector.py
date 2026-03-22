"""
국회 열린데이터 API 수집기
- 국회의원 인적사항 수집
- 발의법률안 수집
- GPT-4o mini로 AI 분석 리포트 생성
"""

import os
import json
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 국회 API 설정
ASSEMBLY_API_KEY = os.getenv("ASSEMBLY_API_KEY", "9803e6a51c334322ace8627791ce36a9")
BASE_URL = "https://open.assembly.go.kr/portal/openapi"

# API 엔드포인트
ENDPOINTS = {
    "lawmakers": "nwvrqwxyaytdsfvhu",       # 국회의원 인적사항
    "bills": "nzmimeepazxkubdpn",            # 발의법률안
}

# 현재 국회 대수 (22대: 2024~2028)
CURRENT_AGE = 22


class AssemblyCollector:
    """국회 열린데이터 API에서 실제 데이터를 수집하는 클래스"""

    def __init__(self):
        self.api_key = ASSEMBLY_API_KEY
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "assembly")
        os.makedirs(self.data_dir, exist_ok=True)

    def _api_call(self, endpoint_key: str, params: dict = None, page_size: int = 100) -> list:
        """국회 API 호출 공통 함수"""
        endpoint = ENDPOINTS.get(endpoint_key, endpoint_key)
        url = f"{BASE_URL}/{endpoint}"

        base_params = {
            "Key": self.api_key,
            "Type": "json",
            "pIndex": 1,
            "pSize": page_size,
        }
        if params:
            base_params.update(params)

        all_rows = []
        max_pages = 20  # 안전장치

        for page in range(1, max_pages + 1):
            base_params["pIndex"] = page
            try:
                resp = httpx.get(url, params=base_params, timeout=30)
                data = resp.json()

                # 응답 구조: { "endpoint_name": [ {head}, {row} ] }
                api_data = data.get(endpoint, {})
                if isinstance(api_data, list) and len(api_data) >= 2:
                    rows = api_data[1].get("row", [])
                    if not rows:
                        break
                    all_rows.extend(rows)

                    # 전체 건수 확인
                    head = api_data[0].get("head", [])
                    total_count = 0
                    for h in head:
                        if "list_total_count" in h:
                            total_count = h["list_total_count"]
                            break

                    if len(all_rows) >= total_count:
                        break
                else:
                    break
            except Exception as e:
                print(f"[AssemblyCollector] API 호출 오류 (page {page}): {e}")
                break

        return all_rows

    def collect_lawmakers(self) -> List[Dict]:
        """22대 국회의원 전체 수집"""
        print("[AssemblyCollector] 국회의원 인적사항 수집 시작...")
        rows = self._api_call("lawmakers", {"AGE": CURRENT_AGE}, page_size=300)

        lawmakers = []
        for row in rows:
            lm = {
                "mona_cd": row.get("MONA_CD", ""),
                "name": row.get("HG_NM", ""),
                "name_hanja": row.get("HJ_NM", ""),
                "name_eng": row.get("ENG_NM", ""),
                "party": row.get("POLY_NM", ""),
                "district": row.get("ORIG_NM", ""),
                "election_type": row.get("ELECT_GBN_NM", ""),
                "reelection": row.get("REELE_GBN_NM", ""),
                "committee": row.get("CMIT_NM", ""),
                "committees": row.get("CMITS", ""),
                "gender": row.get("SEX_GBN_NM", ""),
                "birth_date": row.get("BTH_DATE", ""),
                "tel": row.get("TEL_NO", ""),
                "email": row.get("E_MAIL", ""),
                "homepage": row.get("HOMEPAGE", ""),
                "office": row.get("ASSEM_ADDR", ""),
                "career": row.get("MEM_TITLE", ""),
                "photo_url": f"https://www.assembly.go.kr/photo/9770{row.get('MONA_CD', '')}.jpg",
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            lawmakers.append(lm)

        # 로컬 저장
        save_path = os.path.join(self.data_dir, "lawmakers_real.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(lawmakers, f, ensure_ascii=False, indent=2)

        print(f"[AssemblyCollector] 국회의원 {len(lawmakers)}명 수집 완료 → {save_path}")
        return lawmakers

    def collect_bills(self, proposer_name: str = None, recent_days: int = 90) -> List[Dict]:
        """발의법률안 수집"""
        print(f"[AssemblyCollector] 발의법률안 수집 시작... (최근 {recent_days}일)")

        params = {"AGE": CURRENT_AGE}

        rows = self._api_call("bills", params, page_size=100)

        bills = []
        cutoff = datetime.now() - timedelta(days=recent_days)

        for row in rows:
            propose_dt = row.get("PROPOSE_DT", "")
            try:
                dt = datetime.strptime(propose_dt, "%Y-%m-%d")
                if dt < cutoff:
                    continue
            except (ValueError, TypeError):
                pass

            # 특정 의원 필터
            if proposer_name and proposer_name not in row.get("RST_PROPOSER", ""):
                continue

            bill = {
                "bill_id": row.get("BILL_ID", ""),
                "bill_no": row.get("BILL_NO", ""),
                "bill_name": row.get("BILL_NAME", ""),
                "proposer": row.get("RST_PROPOSER", ""),
                "proposer_code": row.get("RST_MONA_CD", ""),
                "propose_date": propose_dt,
                "committee": row.get("COMMITTEE", ""),
                "proc_result": row.get("PROC_RESULT", ""),
                "detail_link": row.get("DETAIL_LINK", ""),
                "age": row.get("AGE", CURRENT_AGE),
            }
            bills.append(bill)

        print(f"[AssemblyCollector] 법안 {len(bills)}건 수집 완료")
        return bills

    def collect_lawmaker_bills_count(self, lawmakers: List[Dict]) -> Dict[str, int]:
        """의원별 발의 법안 수 집계"""
        print("[AssemblyCollector] 의원별 법안 발의 수 집계 중...")

        # 전체 법안 가져오기 (22대 전체)
        all_bills = self._api_call("bills", {"AGE": CURRENT_AGE}, page_size=100)

        # 의원 코드별 카운트
        bill_counts = {}
        for bill in all_bills:
            proposer_code = bill.get("RST_MONA_CD", "")
            if proposer_code:
                bill_counts[proposer_code] = bill_counts.get(proposer_code, 0) + 1

            # 공동발의자도 카운트 (PUBL_MONA_CD에 쉼표로 구분)
            publ_codes = bill.get("PUBL_MONA_CD", "") or ""
            for code in publ_codes.split(","):
                code = code.strip()
                if code:
                    bill_counts[code] = bill_counts.get(code, 0) + 1

        return bill_counts

    def build_full_dataset(self) -> Dict:
        """전체 데이터셋 구축 (의원 + 법안 통합)"""
        print("=" * 60)
        print("  국회 열린데이터 전체 수집 시작")
        print("=" * 60)

        # 1. 의원 수집
        lawmakers = self.collect_lawmakers()

        # 2. 법안 수집 & 의원별 집계
        bill_counts = self.collect_lawmaker_bills_count(lawmakers)

        # 3. 통합 데이터 구축
        enriched = []
        for lm in lawmakers:
            mona_cd = lm["mona_cd"]
            lm["bills_proposed"] = bill_counts.get(mona_cd, 0)
            enriched.append(lm)

        # 정렬 (법안 발의 수 기준 내림차순)
        enriched.sort(key=lambda x: x["bills_proposed"], reverse=True)

        # 저장
        save_path = os.path.join(self.data_dir, "lawmakers_enriched.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(enriched, f, ensure_ascii=False, indent=2)

        result = {
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_lawmakers": len(enriched),
            "total_bills_tracked": sum(bill_counts.values()),
            "top_proposers": [
                {"name": lm["name"], "party": lm["party"], "district": lm["district"], "bills": lm["bills_proposed"]}
                for lm in enriched[:10]
            ],
            "low_proposers": [
                {"name": lm["name"], "party": lm["party"], "district": lm["district"], "bills": lm["bills_proposed"]}
                for lm in enriched[-10:]
            ],
        }

        print(f"\n[결과] 의원 {result['total_lawmakers']}명, 법안 {result['total_bills_tracked']}건 수집 완료")
        return result


# CLI 테스트
if __name__ == "__main__":
    collector = AssemblyCollector()
    result = collector.build_full_dataset()
    print(json.dumps(result, ensure_ascii=False, indent=2))
