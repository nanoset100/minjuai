"""
의정활동감시팀 AI 에이전트 v2.0
- 국회 열린데이터 API 실제 데이터 연동
- GPT-4o mini AI 분석 리포트 생성
- Supabase DB 저장
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from agents.assembly_collector import AssemblyCollector


class MonitoringAgent:
    """국회의원 의정활동을 실시간 모니터링하고 AI 분석하는 에이전트"""

    def __init__(self):
        self.collector = AssemblyCollector()
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "assembly")
        self.cache_file = os.path.join(self.data_dir, "lawmakers_enriched.json")
        os.makedirs(self.data_dir, exist_ok=True)

        # 캐시 로드 (있으면)
        self.lawmakers = self._load_cache()

    def _load_cache(self) -> List[Dict]:
        """캐시된 데이터 로드"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_cache(self):
        """캐시 저장"""
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.lawmakers, f, ensure_ascii=False, indent=2)

    # ==================== 데이터 수집 ====================

    def refresh_data(self) -> Dict:
        """국회 API에서 최신 데이터 수집 (스케줄러용)"""
        result = self.collector.build_full_dataset()
        self.lawmakers = self._load_cache()
        return result

    def collect_lawmakers_only(self) -> Dict:
        """의원 인적사항만 빠르게 수집"""
        lawmakers = self.collector.collect_lawmakers()
        self.lawmakers = lawmakers
        return {
            "status": "success",
            "total": len(lawmakers),
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    # ==================== 의원 조회 ====================

    def get_all_lawmakers(self, party: str = None, sort_by: str = "name") -> Dict:
        """전체 의원 목록 (필터/정렬)"""
        if not self.lawmakers:
            return {"error": "데이터가 없습니다. /api/monitoring/refresh 를 먼저 호출하세요.", "lawmakers": []}

        filtered = self.lawmakers
        if party:
            filtered = [lm for lm in filtered if party in lm.get("party", "")]

        # 정렬
        if sort_by == "bills":
            filtered.sort(key=lambda x: x.get("bills_proposed", 0), reverse=True)
        elif sort_by == "party":
            filtered.sort(key=lambda x: x.get("party", ""))
        elif sort_by == "district":
            filtered.sort(key=lambda x: x.get("district", ""))
        else:
            filtered.sort(key=lambda x: x.get("name", ""))

        # 간략화된 목록
        summary = []
        for lm in filtered:
            summary.append({
                "mona_cd": lm.get("mona_cd", ""),
                "name": lm.get("name", ""),
                "party": lm.get("party", ""),
                "district": lm.get("district", ""),
                "election_type": lm.get("election_type", ""),
                "reelection": lm.get("reelection", ""),
                "committee": lm.get("committee", ""),
                "bills_proposed": lm.get("bills_proposed", 0),
                "photo_url": lm.get("photo_url", ""),
            })

        return {
            "total": len(summary),
            "filter": {"party": party} if party else "전체",
            "sort_by": sort_by,
            "lawmakers": summary,
        }

    def get_lawmaker_detail(self, mona_cd: str) -> Dict:
        """의원 상세 정보"""
        lm = next((l for l in self.lawmakers if l.get("mona_cd") == mona_cd), None)
        if not lm:
            # 이름으로도 검색
            lm = next((l for l in self.lawmakers if l.get("name") == mona_cd), None)
        if not lm:
            return {"error": f"의원 '{mona_cd}'을(를) 찾을 수 없습니다."}

        return {
            "lawmaker": lm,
            "analysis": self._quick_analysis(lm),
        }

    def search_lawmakers(self, query: str) -> Dict:
        """의원 검색 (이름, 지역구, 정당)"""
        results = []
        q = query.lower()
        for lm in self.lawmakers:
            if (q in lm.get("name", "").lower() or
                q in lm.get("district", "").lower() or
                q in lm.get("party", "").lower() or
                q in lm.get("committee", "").lower()):
                results.append({
                    "mona_cd": lm.get("mona_cd", ""),
                    "name": lm.get("name", ""),
                    "party": lm.get("party", ""),
                    "district": lm.get("district", ""),
                    "bills_proposed": lm.get("bills_proposed", 0),
                })
        return {"query": query, "results": results, "count": len(results)}

    # ==================== AI 분석 ====================

    def _quick_analysis(self, lm: Dict) -> Dict:
        """의원 빠른 분석"""
        bills = lm.get("bills_proposed", 0)
        reelection = lm.get("reelection", "")

        # 재선 횟수 파싱
        term = 1
        if "재선" in reelection:
            term = 2
        elif "3선" in reelection:
            term = 3
        elif "4선" in reelection:
            term = 4
        elif "5선" in reelection:
            term = 5
        elif "초선" in reelection:
            term = 1

        # 법안 발의 등급
        if bills >= 30:
            bill_grade = "매우 우수"
        elif bills >= 15:
            bill_grade = "우수"
        elif bills >= 8:
            bill_grade = "보통"
        elif bills >= 3:
            bill_grade = "미흡"
        else:
            bill_grade = "매우 저조"

        # 활동 점수 계산 (법안 기반, 0~100)
        activity_score = min(100, round(bills * 2.5))

        return {
            "term": f"{term}선" if term > 1 else "초선",
            "bills_proposed": bills,
            "bill_grade": bill_grade,
            "activity_score": activity_score,
            "election_type": lm.get("election_type", ""),
            "committee": lm.get("committee", ""),
        }

    def analyze_lawmaker(self, identifier: str) -> Dict:
        """특정 의원 상세 AI 분석"""
        detail = self.get_lawmaker_detail(identifier)
        if "error" in detail:
            return detail

        lm = detail["lawmaker"]
        analysis = detail["analysis"]

        # AI 분석 리포트 생성 (GPT-4o mini)
        try:
            from ai_client import ai_call
            prompt = f"""다음 국회의원의 의정활동을 분석해주세요:

이름: {lm['name']}
정당: {lm['party']}
지역구: {lm['district']}
선수: {analysis['term']}
소속위원회: {lm.get('committee', '없음')}
발의법안 수: {analysis['bills_proposed']}건 ({analysis['bill_grade']})
선거유형: {lm.get('election_type', '')}
경력: {lm.get('career', '')[:200]}

분석 항목:
1. 입법 활동 평가 (발의 법안 수 기준)
2. 위원회 활동 의미
3. 종합 의정활동 등급 (A/B/C/D/F)
4. 개선이 필요한 부분
5. 시민을 위한 한줄 요약

한국어로 간결하게 답변해주세요."""

            ai_report = ai_call(prompt, system="당신은 대한민국 국회 의정활동 전문 분석가입니다. 객관적이고 공정하게 분석합니다.", max_tokens=500)
        except Exception as e:
            ai_report = f"AI 분석 일시 불가: {str(e)}"

        return {
            "lawmaker": {
                "mona_cd": lm.get("mona_cd", ""),
                "name": lm["name"],
                "party": lm["party"],
                "district": lm["district"],
                "photo_url": lm.get("photo_url", ""),
                "email": lm.get("email", ""),
                "homepage": lm.get("homepage", ""),
            },
            "analysis": analysis,
            "ai_report": ai_report,
            "data_source": "국회 열린데이터 포털 (open.assembly.go.kr)",
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    # ==================== 통계 ====================

    def get_monitoring_stats(self) -> Dict:
        """전체 모니터링 통계"""
        if not self.lawmakers:
            return {"error": "데이터가 없습니다. /api/monitoring/refresh 를 먼저 호출하세요."}

        total = len(self.lawmakers)

        # 정당별 통계
        party_stats = {}
        for lm in self.lawmakers:
            p = lm.get("party", "무소속")
            if p not in party_stats:
                party_stats[p] = {"count": 0, "total_bills": 0, "districts": [], "proportional": 0}
            party_stats[p]["count"] += 1
            party_stats[p]["total_bills"] += lm.get("bills_proposed", 0)
            if lm.get("election_type") == "비례대표":
                party_stats[p]["proportional"] += 1
            else:
                party_stats[p]["districts"].append(lm.get("district", ""))

        for p in party_stats:
            cnt = party_stats[p]["count"]
            party_stats[p]["avg_bills"] = round(party_stats[p]["total_bills"] / cnt, 1) if cnt else 0
            party_stats[p]["district_count"] = cnt - party_stats[p]["proportional"]
            del party_stats[p]["districts"]  # 목록은 제거 (길어서)

        # 지역별 통계
        region_stats = {}
        for lm in self.lawmakers:
            district = lm.get("district", "")
            if not district:
                continue
            region = district.split()[0] if " " in district else district
            if region not in region_stats:
                region_stats[region] = {"count": 0, "total_bills": 0}
            region_stats[region]["count"] += 1
            region_stats[region]["total_bills"] += lm.get("bills_proposed", 0)

        for r in region_stats:
            cnt = region_stats[r]["count"]
            region_stats[r]["avg_bills"] = round(region_stats[r]["total_bills"] / cnt, 1) if cnt else 0

        # 전체 법안 통계
        all_bills = [lm.get("bills_proposed", 0) for lm in self.lawmakers]
        avg_bills = round(sum(all_bills) / total, 1) if total else 0
        max_bills = max(all_bills) if all_bills else 0
        min_bills = min(all_bills) if all_bills else 0

        # 법안 발의 분포
        grade_dist = {
            "매우우수(30+)": len([b for b in all_bills if b >= 30]),
            "우수(15-29)": len([b for b in all_bills if 15 <= b < 30]),
            "보통(8-14)": len([b for b in all_bills if 8 <= b < 14]),
            "미흡(3-7)": len([b for b in all_bills if 3 <= b < 8]),
            "매우저조(0-2)": len([b for b in all_bills if b < 3]),
        }

        # 상위/하위 의원
        sorted_by_bills = sorted(self.lawmakers, key=lambda x: x.get("bills_proposed", 0), reverse=True)
        top5 = [{"name": lm["name"], "party": lm["party"], "district": lm.get("district", ""), "bills": lm.get("bills_proposed", 0)} for lm in sorted_by_bills[:5]]
        bottom5 = [{"name": lm["name"], "party": lm["party"], "district": lm.get("district", ""), "bills": lm.get("bills_proposed", 0)} for lm in sorted_by_bills[-5:]]

        return {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "data_source": "국회 열린데이터 포털 (open.assembly.go.kr)",
            "overview": {
                "total_lawmakers": total,
                "total_bills": sum(all_bills),
                "avg_bills_per_lawmaker": avg_bills,
                "max_bills": max_bills,
                "min_bills": min_bills,
            },
            "grade_distribution": grade_dist,
            "by_party": party_stats,
            "by_region": region_stats,
            "top5_lawmakers": top5,
            "bottom5_lawmakers": bottom5,
            "ai_party_goal": {
                "district_seats_target": 3,
                "proportional_seats_target": 7,
                "total_target": 10,
                "target_election": "2028 총선",
            },
        }

    def find_vulnerable_districts(self, top_n: int = 10) -> Dict:
        """취약 지역구 발굴 (법안 발의 저조한 의원 지역구)"""
        if not self.lawmakers:
            return {"error": "데이터가 없습니다."}

        # 지역구 의원만 (비례대표 제외)
        district_lawmakers = [
            lm for lm in self.lawmakers
            if lm.get("election_type") != "비례대표" and lm.get("district")
        ]

        # 법안 발의 수 기준 오름차순 (적은 순서)
        sorted_lm = sorted(district_lawmakers, key=lambda x: x.get("bills_proposed", 0))

        results = []
        for rank, lm in enumerate(sorted_lm[:top_n], 1):
            bills = lm.get("bills_proposed", 0)
            analysis = self._quick_analysis(lm)

            weak_points = []
            if bills < 3:
                weak_points.append(f"법안 발의 극히 저조 ({bills}건)")
            elif bills < 8:
                weak_points.append(f"법안 발의 미흡 ({bills}건)")

            reelection = lm.get("reelection", "")
            if "3선" in reelection or "4선" in reelection or "5선" in reelection:
                weak_points.append(f"다선 의원 ({reelection}) - 활동 대비 경험")

            results.append({
                "rank": rank,
                "mona_cd": lm.get("mona_cd", ""),
                "name": lm["name"],
                "party": lm["party"],
                "district": lm["district"],
                "bills_proposed": bills,
                "bill_grade": analysis["bill_grade"],
                "activity_score": analysis["activity_score"],
                "weak_points": weak_points,
                "priority": "최우선" if bills < 3 else ("우선" if bills < 8 else "검토"),
            })

        return {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_district_lawmakers": len(district_lawmakers),
            "top_vulnerable": results,
        }

    def get_attack_strategy(self, identifier: str) -> Dict:
        """해당 의원 공략 전략 생성 (AI 활용)"""
        detail = self.get_lawmaker_detail(identifier)
        if "error" in detail:
            return detail

        lm = detail["lawmaker"]
        analysis = detail["analysis"]

        # AI로 공략 전략 생성
        try:
            from ai_client import ai_call
            prompt = f"""다음 현역 국회의원의 지역구에 AI 정당이 출마할 전략을 분석해주세요:

현역 의원: {lm['name']}
정당: {lm['party']}
지역구: {lm['district']}
선수: {analysis['term']}
발의법안: {analysis['bills_proposed']}건 ({analysis['bill_grade']})
소속위원회: {lm.get('committee', '')}

분석해주세요:
1. 현역 의원의 약점 (구체적)
2. AI 정당이 내세울 핵심 정책 3가지
3. 캠페인 핵심 메시지 1개
4. 예상 승산 (상/중/하)
5. 실행 계획 3단계

한국어로 간결하게 답변해주세요."""

            ai_strategy = ai_call(prompt, system="당신은 대한민국 선거 전략 전문 컨설턴트입니다. 데이터 기반으로 분석합니다.", max_tokens=600)
        except Exception as e:
            ai_strategy = f"AI 전략 생성 불가: {str(e)}"

        return {
            "target": {
                "mona_cd": lm.get("mona_cd", ""),
                "name": lm["name"],
                "district": lm["district"],
                "party": lm["party"],
                "bills_proposed": analysis["bills_proposed"],
                "bill_grade": analysis["bill_grade"],
            },
            "ai_strategy": ai_strategy,
            "data_source": "국회 열린데이터 포털",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    # ==================== 리포트 ====================

    def generate_report(self) -> Dict:
        """종합 리포트 생성"""
        stats = self.get_monitoring_stats()
        if "error" in stats:
            return stats

        top = self.find_vulnerable_districts(5)

        lines = [
            "# 의정활동 감시 리포트 v2.0",
            f"생성일시: {stats['generated_at']}",
            f"데이터 출처: {stats['data_source']}",
            "",
            "## 전체 현황",
            f"- 분석 의원: {stats['overview']['total_lawmakers']}명",
            f"- 총 법안 발의: {stats['overview']['total_bills']}건",
            f"- 의원당 평균: {stats['overview']['avg_bills_per_lawmaker']}건",
            f"- 최다 발의: {stats['overview']['max_bills']}건",
            f"- 최소 발의: {stats['overview']['min_bills']}건",
            "",
            "## 법안 발의 등급 분포",
        ]
        for grade, cnt in stats["grade_distribution"].items():
            lines.append(f"- {grade}: {cnt}명")

        lines.append("\n## Top 5 의원 (법안 발의)")
        for lm in stats["top5_lawmakers"]:
            lines.append(f"- {lm['name']} ({lm['party']}, {lm['district']}): {lm['bills']}건")

        lines.append("\n## Bottom 5 의원 (법안 발의)")
        for lm in stats["bottom5_lawmakers"]:
            lines.append(f"- {lm['name']} ({lm['party']}, {lm['district']}): {lm['bills']}건")

        if "top_vulnerable" in top:
            lines.append("\n## Top 5 공략 대상 지역구")
            for d in top["top_vulnerable"]:
                lines.append(f"\n### {d['rank']}. {d['district']} ({d['name']}, {d['party']})")
                lines.append(f"- 발의 법안: {d['bills_proposed']}건 ({d['bill_grade']})")
                lines.append(f"- 우선순위: {d['priority']}")
                for wp in d.get("weak_points", []):
                    lines.append(f"  - {wp}")

        lines.append("\n## 정당별 분석")
        for party, data in stats["by_party"].items():
            lines.append(f"- {party}: {data['count']}명, 평균 {data['avg_bills']}건")

        report_text = "\n".join(lines)

        # 저장
        report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "outputs")
        os.makedirs(report_dir, exist_ok=True)
        report_file = os.path.join(report_dir, f"monitoring_report_{datetime.now().strftime('%Y%m%d')}.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_text)

        return {"report_file": report_file, "content": report_text}


# CLI 테스트
if __name__ == "__main__":
    agent = MonitoringAgent()

    print("=" * 60)
    print("  의정활동감시팀 AI v2.0 (국회 API 연동)")
    print("=" * 60)

    # 데이터 수집
    print("\n[1] 데이터 수집 중...")
    result = agent.refresh_data()
    print(f"  수집 완료: 의원 {result['total_lawmakers']}명")

    # 통계
    print("\n[2] 전체 통계")
    stats = agent.get_monitoring_stats()
    o = stats["overview"]
    print(f"  의원: {o['total_lawmakers']}명, 총 법안: {o['total_bills']}건, 평균: {o['avg_bills_per_lawmaker']}건")

    # 취약 지역구
    print("\n[3] 취약 지역구 Top 5")
    top = agent.find_vulnerable_districts(5)
    for d in top.get("top_vulnerable", []):
        print(f"  {d['rank']}. {d['district']} ({d['name']}, {d['party']}) - {d['bills_proposed']}건 [{d['priority']}]")

    print("\n완료!")
