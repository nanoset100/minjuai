"""
의정활동감시팀 AI 에이전트
국회의원 의정활동 모니터링 및 취약 지역구 발굴
"""

import json
import os
import random
from datetime import datetime, timedelta


class MonitoringAgent:
    """국회의원 의정활동을 모니터링하고 취약 지역구를 발굴하는 AI 에이전트"""

    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "monitoring")
        self.lawmakers_file = os.path.join(self.base_dir, "lawmakers.json")

        os.makedirs(self.base_dir, exist_ok=True)

        if not os.path.exists(self.lawmakers_file):
            self._generate_seed_data()

        self.lawmakers = self._load_lawmakers()

    def _load_lawmakers(self):
        with open(self.lawmakers_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_lawmakers(self):
        with open(self.lawmakers_file, "w", encoding="utf-8") as f:
            json.dump(self.lawmakers, f, ensure_ascii=False, indent=2)

    def _generate_seed_data(self):
        """20명의 시드 데이터 생성 (가상 데이터)"""
        seed = [
            {
                "id": "lm_001",
                "name": "김태호",
                "district": "서울 강남구갑",
                "party": "국민의힘",
                "term": 3,
                "age": 62,
                "activities": {
                    "bills_proposed": 5,
                    "attendance_rate": 55,
                    "committee_activity": "낮음",
                    "promise_fulfillment": 30
                },
                "scandals": ["부동산 투기 의혹", "정치자금법 위반 논란"],
                "local_issues": ["강남 교통 혼잡", "학원가 과열", "재건축 규제"]
            },
            {
                "id": "lm_002",
                "name": "박수진",
                "district": "서울 강북구을",
                "party": "더불어민주당",
                "term": 2,
                "age": 51,
                "activities": {
                    "bills_proposed": 18,
                    "attendance_rate": 88,
                    "committee_activity": "높음",
                    "promise_fulfillment": 72
                },
                "scandals": [],
                "local_issues": ["노후 주거환경", "상권 활성화"]
            },
            {
                "id": "lm_003",
                "name": "이정우",
                "district": "서울 송파구갑",
                "party": "국민의힘",
                "term": 1,
                "age": 45,
                "activities": {
                    "bills_proposed": 8,
                    "attendance_rate": 72,
                    "committee_activity": "보통",
                    "promise_fulfillment": 50
                },
                "scandals": ["논문 표절 의혹"],
                "local_issues": ["잠실 재건축", "교통 인프라"]
            },
            {
                "id": "lm_004",
                "name": "최미영",
                "district": "서울 마포구갑",
                "party": "더불어민주당",
                "term": 4,
                "age": 67,
                "activities": {
                    "bills_proposed": 3,
                    "attendance_rate": 45,
                    "committee_activity": "낮음",
                    "promise_fulfillment": 25
                },
                "scandals": ["보좌관 갑질 논란"],
                "local_issues": ["홍대입구 상권", "청년 주거"]
            },
            {
                "id": "lm_005",
                "name": "정현석",
                "district": "서울 영등포구갑",
                "party": "국민의힘",
                "term": 2,
                "age": 58,
                "activities": {
                    "bills_proposed": 10,
                    "attendance_rate": 78,
                    "committee_activity": "보통",
                    "promise_fulfillment": 55
                },
                "scandals": [],
                "local_issues": ["여의도 개발", "산업단지 현대화"]
            },
            {
                "id": "lm_006",
                "name": "한지민",
                "district": "경기 수원시갑",
                "party": "더불어민주당",
                "term": 1,
                "age": 42,
                "activities": {
                    "bills_proposed": 22,
                    "attendance_rate": 92,
                    "committee_activity": "높음",
                    "promise_fulfillment": 68
                },
                "scandals": [],
                "local_issues": ["수원 광교 교통", "화성 연계 개발"]
            },
            {
                "id": "lm_007",
                "name": "오승현",
                "district": "경기 성남시갑",
                "party": "국민의힘",
                "term": 2,
                "age": 55,
                "activities": {
                    "bills_proposed": 7,
                    "attendance_rate": 60,
                    "committee_activity": "낮음",
                    "promise_fulfillment": 35
                },
                "scandals": ["부동산 투기 의혹"],
                "local_issues": ["판교 IT밸리 확장", "구도심 재개발"]
            },
            {
                "id": "lm_008",
                "name": "윤서연",
                "district": "경기 용인시갑",
                "party": "더불어민주당",
                "term": 3,
                "age": 64,
                "activities": {
                    "bills_proposed": 4,
                    "attendance_rate": 50,
                    "committee_activity": "낮음",
                    "promise_fulfillment": 28
                },
                "scandals": ["선거법 위반 전력"],
                "local_issues": ["교통 인프라 부족", "난개발 문제"]
            },
            {
                "id": "lm_009",
                "name": "강민재",
                "district": "경기 부천시갑",
                "party": "국민의힘",
                "term": 1,
                "age": 48,
                "activities": {
                    "bills_proposed": 15,
                    "attendance_rate": 85,
                    "committee_activity": "높음",
                    "promise_fulfillment": 62
                },
                "scandals": [],
                "local_issues": ["산업단지 환경오염", "주거환경 개선"]
            },
            {
                "id": "lm_010",
                "name": "서영호",
                "district": "경기 고양시갑",
                "party": "더불어민주당",
                "term": 2,
                "age": 53,
                "activities": {
                    "bills_proposed": 11,
                    "attendance_rate": 75,
                    "committee_activity": "보통",
                    "promise_fulfillment": 58
                },
                "scandals": ["음주운전 전력"],
                "local_issues": ["일산 신도시 노후화", "GTX 연계"]
            },
            {
                "id": "lm_011",
                "name": "임도현",
                "district": "부산 해운대구갑",
                "party": "국민의힘",
                "term": 3,
                "age": 61,
                "activities": {
                    "bills_proposed": 6,
                    "attendance_rate": 58,
                    "committee_activity": "낮음",
                    "promise_fulfillment": 32
                },
                "scandals": ["부동산 투기", "세금 체납"],
                "local_issues": ["해운대 관광 활성화", "해수욕장 관리"]
            },
            {
                "id": "lm_012",
                "name": "배지혜",
                "district": "부산 사하구갑",
                "party": "더불어민주당",
                "term": 1,
                "age": 39,
                "activities": {
                    "bills_proposed": 20,
                    "attendance_rate": 90,
                    "committee_activity": "높음",
                    "promise_fulfillment": 70
                },
                "scandals": [],
                "local_issues": ["낙동강 하류 환경", "을숙도 보존"]
            },
            {
                "id": "lm_013",
                "name": "조성태",
                "district": "부산 동래구갑",
                "party": "국민의힘",
                "term": 2,
                "age": 57,
                "activities": {
                    "bills_proposed": 9,
                    "attendance_rate": 70,
                    "committee_activity": "보통",
                    "promise_fulfillment": 45
                },
                "scandals": ["학력 위조 의혹"],
                "local_issues": ["온천장 관광 개발", "교통체증"]
            },
            {
                "id": "lm_014",
                "name": "홍석진",
                "district": "대구 수성구갑",
                "party": "국민의힘",
                "term": 4,
                "age": 70,
                "activities": {
                    "bills_proposed": 2,
                    "attendance_rate": 40,
                    "committee_activity": "낮음",
                    "promise_fulfillment": 20
                },
                "scandals": ["비서 성추행 의혹", "정치자금 유용"],
                "local_issues": ["수성못 주변 개발", "대구 의료 특화"]
            },
            {
                "id": "lm_015",
                "name": "권나현",
                "district": "대구 달서구갑",
                "party": "국민의힘",
                "term": 1,
                "age": 44,
                "activities": {
                    "bills_proposed": 14,
                    "attendance_rate": 82,
                    "committee_activity": "보통",
                    "promise_fulfillment": 60
                },
                "scandals": [],
                "local_issues": ["성서공단 현대화", "교육 인프라"]
            },
            {
                "id": "lm_016",
                "name": "유진호",
                "district": "대전 유성구갑",
                "party": "더불어민주당",
                "term": 2,
                "age": 50,
                "activities": {
                    "bills_proposed": 16,
                    "attendance_rate": 87,
                    "committee_activity": "높음",
                    "promise_fulfillment": 65
                },
                "scandals": [],
                "local_issues": ["대덕연구단지 활성화", "충청권 메가시티"]
            },
            {
                "id": "lm_017",
                "name": "남궁혁",
                "district": "광주 서구갑",
                "party": "더불어민주당",
                "term": 3,
                "age": 63,
                "activities": {
                    "bills_proposed": 9,
                    "attendance_rate": 65,
                    "committee_activity": "보통",
                    "promise_fulfillment": 42
                },
                "scandals": ["위장전입 논란"],
                "local_issues": ["AI 집적단지", "광주형 일자리"]
            },
            {
                "id": "lm_018",
                "name": "신하은",
                "district": "울산 남구갑",
                "party": "국민의힘",
                "term": 1,
                "age": 46,
                "activities": {
                    "bills_proposed": 12,
                    "attendance_rate": 80,
                    "committee_activity": "보통",
                    "promise_fulfillment": 55
                },
                "scandals": [],
                "local_issues": ["현대자동차 전환", "에너지산업 전환"]
            },
            {
                "id": "lm_019",
                "name": "문재식",
                "district": "인천 남동구갑",
                "party": "더불어민주당",
                "term": 2,
                "age": 56,
                "activities": {
                    "bills_proposed": 6,
                    "attendance_rate": 62,
                    "committee_activity": "낮음",
                    "promise_fulfillment": 38
                },
                "scandals": ["투기 의혹"],
                "local_issues": ["소래포구 관광", "구월동 상권"]
            },
            {
                "id": "lm_020",
                "name": "장윤기",
                "district": "경남 창원시갑",
                "party": "국민의힘",
                "term": 3,
                "age": 66,
                "activities": {
                    "bills_proposed": 3,
                    "attendance_rate": 48,
                    "committee_activity": "낮음",
                    "promise_fulfillment": 22
                },
                "scandals": ["지역 업체 특혜 의혹"],
                "local_issues": ["방산업체 클러스터", "창원 경제 활성화"]
            },
        ]

        # 취약도 점수 및 약점 자동 계산
        for lm in seed:
            lm["vulnerability_score"] = self._calc_vulnerability(lm)
            lm["weak_points"] = self._identify_weak_points(lm)
            lm["last_updated"] = datetime.now().strftime("%Y-%m-%d")

        with open(self.lawmakers_file, "w", encoding="utf-8") as f:
            json.dump(seed, f, ensure_ascii=False, indent=2)

    def _calc_vulnerability(self, lm):
        """취약도 점수 계산 (0-100)"""
        act = lm["activities"]

        attendance_factor = (100 - act["attendance_rate"]) * 0.3
        promise_factor = (100 - act["promise_fulfillment"]) * 0.4
        scandal_factor = min(len(lm.get("scandals", [])) * 15, 30) * (20 / 30)
        age_factor = max(0, (lm.get("age", 50) - 55)) * 1.0

        raw = attendance_factor + promise_factor + scandal_factor + age_factor
        return round(min(max(raw, 0), 100), 1)

    def _identify_weak_points(self, lm):
        """약점 자동 파악"""
        points = []
        act = lm["activities"]

        if act["attendance_rate"] < 70:
            points.append(f"출석률 낮음 ({act['attendance_rate']}%)")
        if act["promise_fulfillment"] < 50:
            points.append(f"공약 이행률 {act['promise_fulfillment']}%")
        if act["bills_proposed"] < 7:
            points.append(f"법안 발의 저조 ({act['bills_proposed']}건)")
        if act["committee_activity"] == "낮음":
            points.append("위원회 활동 미흡")
        if lm.get("scandals"):
            for s in lm["scandals"]:
                points.append(f"스캔들: {s}")
        if lm.get("age", 0) >= 65:
            points.append(f"고령 ({lm['age']}세)")

        return points

    def analyze_lawmaker(self, lawmaker_id):
        """특정 의원 상세 분석"""
        lm = next((l for l in self.lawmakers if l["id"] == lawmaker_id), None)
        if not lm:
            return {"error": f"의원 ID '{lawmaker_id}'를 찾을 수 없습니다."}

        score = lm["vulnerability_score"]
        if score >= 70:
            level = "높음 (공략 가능)"
        elif score >= 50:
            level = "중간 (검토 필요)"
        else:
            level = "낮음 (어려움)"

        bills = lm["activities"]["bills_proposed"]
        if bills >= 15:
            bill_grade = "우수"
        elif bills >= 8:
            bill_grade = "보통"
        else:
            bill_grade = "미흡"

        return {
            "lawmaker": {
                "id": lm["id"],
                "name": lm["name"],
                "district": lm["district"],
                "party": lm["party"],
                "term": f"{lm['term']}선",
                "age": lm.get("age"),
            },
            "activities": {
                "bills_proposed": f"{bills}건 ({bill_grade})",
                "attendance_rate": f"{lm['activities']['attendance_rate']}%",
                "committee_activity": lm["activities"]["committee_activity"],
                "promise_fulfillment": f"{lm['activities']['promise_fulfillment']}%",
            },
            "vulnerability": {
                "score": score,
                "level": level,
                "weak_points": lm["weak_points"],
                "scandals": lm.get("scandals", []),
            },
            "local_issues": lm.get("local_issues", []),
            "last_updated": lm.get("last_updated"),
        }

    def find_vulnerable_districts(self, top_n=10):
        """취약 지역구 Top N 발굴"""
        sorted_lm = sorted(self.lawmakers, key=lambda x: x["vulnerability_score"], reverse=True)
        results = []

        for rank, lm in enumerate(sorted_lm[:top_n], 1):
            score = lm["vulnerability_score"]
            win_chance = self._estimate_win_chance(lm)

            results.append({
                "rank": rank,
                "lawmaker_id": lm["id"],
                "name": lm["name"],
                "district": lm["district"],
                "party": lm["party"],
                "vulnerability_score": score,
                "win_chance": win_chance,
                "top_weak_points": lm["weak_points"][:3],
                "priority": "최우선" if score >= 75 else ("우선" if score >= 65 else "검토"),
            })

        return {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_analyzed": len(self.lawmakers),
            "top_districts": results,
        }

    def _estimate_win_chance(self, lm):
        """AI 정당 승산 추정"""
        score = lm["vulnerability_score"]

        base = score * 0.55
        if lm["term"] >= 3:
            base += 5
        if len(lm.get("scandals", [])) >= 2:
            base += 8
        if lm["activities"]["attendance_rate"] < 50:
            base += 5

        chance = round(min(max(base, 5), 85), 1)
        return f"{chance}%"

    def get_attack_strategy(self, lawmaker_id):
        """해당 의원 공략 전략 생성"""
        lm = next((l for l in self.lawmakers if l["id"] == lawmaker_id), None)
        if not lm:
            return {"error": f"의원 ID '{lawmaker_id}'를 찾을 수 없습니다."}

        score = lm["vulnerability_score"]
        act = lm["activities"]

        # 필요 정책 도출
        policies = []
        for issue in lm.get("local_issues", []):
            policies.append(f"{issue} 해결 정책")
        if act["attendance_rate"] < 70:
            policies.append("의정활동 투명성 강화 공약")
        if act["promise_fulfillment"] < 50:
            policies.append("주민 직접 참여 정책결정 시스템")

        # 약점 기반 전략
        attack_points = []
        if act["attendance_rate"] < 70:
            attack_points.append(f"출석률 {act['attendance_rate']}% - 국정 태만 부각")
        if act["promise_fulfillment"] < 50:
            attack_points.append(f"공약 이행률 {act['promise_fulfillment']}% - 약속 불이행 강조")
        if act["bills_proposed"] < 7:
            attack_points.append(f"법안 발의 {act['bills_proposed']}건 - 입법 활동 부진 비판")
        for s in lm.get("scandals", []):
            attack_points.append(f"스캔들: {s}")

        # 예상 득표율
        win = float(self._estimate_win_chance(lm).replace("%", ""))
        incumbent = round(100 - win - random.uniform(15, 25), 1)
        others = round(100 - win - incumbent, 1)

        verdict = "승리 가능" if win > incumbent else ("접전" if abs(win - incumbent) < 5 else "도전적")

        return {
            "target": {
                "name": lm["name"],
                "district": lm["district"],
                "party": lm["party"],
                "vulnerability_score": score,
            },
            "strategy": {
                "required_policies": policies,
                "attack_points": attack_points,
                "key_message": f"{lm['district']} 주민을 위한 실질적 변화, AI 정당이 시작합니다",
            },
            "prediction": {
                "ai_party": f"{win}%",
                "incumbent": f"{incumbent}%",
                "others": f"{others}%",
                "verdict": verdict,
            },
            "action_plan": [
                f"1단계: {lm['district']} 지역 현안 조사 및 주민 의견 수렴",
                f"2단계: {', '.join(lm.get('local_issues', [])[:2])} 관련 정책 발표",
                f"3단계: 현역 의원 의정활동 평가 보고서 배포",
                f"4단계: AI 정당 후보자 선정 및 캠페인 시작",
            ],
        }

    def get_monitoring_stats(self):
        """전체 모니터링 통계"""
        total = len(self.lawmakers)

        high = [l for l in self.lawmakers if l["vulnerability_score"] >= 70]
        mid = [l for l in self.lawmakers if 50 <= l["vulnerability_score"] < 70]
        low = [l for l in self.lawmakers if l["vulnerability_score"] < 50]

        # 정당별 분석
        party_stats = {}
        for lm in self.lawmakers:
            p = lm["party"]
            if p not in party_stats:
                party_stats[p] = {"count": 0, "avg_vulnerability": 0, "total_score": 0}
            party_stats[p]["count"] += 1
            party_stats[p]["total_score"] += lm["vulnerability_score"]
        for p in party_stats:
            party_stats[p]["avg_vulnerability"] = round(
                party_stats[p]["total_score"] / party_stats[p]["count"], 1
            )
            del party_stats[p]["total_score"]

        # 지역별 분석
        region_stats = {}
        for lm in self.lawmakers:
            region = lm["district"].split()[0]
            if region not in region_stats:
                region_stats[region] = {"count": 0, "vulnerable": 0}
            region_stats[region]["count"] += 1
            if lm["vulnerability_score"] >= 70:
                region_stats[region]["vulnerable"] += 1

        avg_score = round(sum(l["vulnerability_score"] for l in self.lawmakers) / total, 1) if total else 0

        return {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "overview": {
                "total_lawmakers": total,
                "average_vulnerability": avg_score,
                "high_vulnerability": f"{len(high)}명 (70+)",
                "mid_vulnerability": f"{len(mid)}명 (50-69)",
                "low_vulnerability": f"{len(low)}명 (0-49)",
            },
            "by_party": party_stats,
            "by_region": region_stats,
            "target_summary": {
                "attackable": len(high),
                "review_needed": len(mid),
                "difficult": len(low),
            },
            "ai_party_goal": {
                "district_seats_target": 3,
                "proportional_seats_target": 7,
                "total_target": 10,
                "feasible_districts": len([l for l in high if float(self._estimate_win_chance(l).replace("%", "")) > 40]),
            },
        }

    def update_lawmaker(self, lawmaker_id, updates):
        """의원 정보 업데이트"""
        for i, lm in enumerate(self.lawmakers):
            if lm["id"] == lawmaker_id:
                if "activities" in updates:
                    lm["activities"].update(updates["activities"])
                if "scandals" in updates:
                    lm["scandals"] = updates["scandals"]
                if "local_issues" in updates:
                    lm["local_issues"] = updates["local_issues"]

                lm["vulnerability_score"] = self._calc_vulnerability(lm)
                lm["weak_points"] = self._identify_weak_points(lm)
                lm["last_updated"] = datetime.now().strftime("%Y-%m-%d")

                self.lawmakers[i] = lm
                self._save_lawmakers()
                return {"status": "updated", "lawmaker": lm["name"], "new_score": lm["vulnerability_score"]}

        return {"error": f"의원 ID '{lawmaker_id}'를 찾을 수 없습니다."}

    def generate_report(self):
        """종합 리포트 생성"""
        stats = self.get_monitoring_stats()
        top = self.find_vulnerable_districts(5)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = [
            f"# 의정활동 감시 리포트",
            f"생성일시: {now}",
            "",
            f"## 전체 현황",
            f"- 분석 의원: {stats['overview']['total_lawmakers']}명",
            f"- 평균 취약도: {stats['overview']['average_vulnerability']}점",
            f"- 공략 가능(70+): {stats['overview']['high_vulnerability']}",
            f"- 검토 필요(50-69): {stats['overview']['mid_vulnerability']}",
            f"- 어려움(~49): {stats['overview']['low_vulnerability']}",
            "",
            "## Top 5 공략 대상 지역구",
        ]

        for d in top["top_districts"]:
            lines.append(f"\n### {d['rank']}. {d['district']} ({d['name']}, {d['party']})")
            lines.append(f"- 취약도: {d['vulnerability_score']}점")
            lines.append(f"- 승산: {d['win_chance']}")
            lines.append(f"- 우선순위: {d['priority']}")
            for wp in d["top_weak_points"]:
                lines.append(f"  - {wp}")

        lines.append("\n## 정당별 분석")
        for party, data in stats["by_party"].items():
            lines.append(f"- {party}: {data['count']}명, 평균 취약도 {data['avg_vulnerability']}점")

        lines.append("\n## 지역별 분석")
        for region, data in stats["by_region"].items():
            lines.append(f"- {region}: {data['count']}명 중 취약 {data['vulnerable']}명")

        report_text = "\n".join(lines)

        report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "outputs")
        os.makedirs(report_dir, exist_ok=True)
        report_file = os.path.join(report_dir, f"monitoring_report_{datetime.now().strftime('%Y%m%d')}.md")

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_text)

        return {"report_file": report_file, "content": report_text}


# CLI 실행
if __name__ == "__main__":
    agent = MonitoringAgent()

    print("=" * 60)
    print("  의정활동감시팀 AI 에이전트")
    print("=" * 60)

    # 1. 전체 통계
    stats = agent.get_monitoring_stats()
    o = stats["overview"]
    print(f"\n[전체 현황]")
    print(f"  분석 의원: {o['total_lawmakers']}명")
    print(f"  평균 취약도: {o['average_vulnerability']}점")
    print(f"  공략 가능(70+): {o['high_vulnerability']}")
    print(f"  검토 필요(50-69): {o['mid_vulnerability']}")
    print(f"  어려움(~49): {o['low_vulnerability']}")

    # 2. 취약 지역구 Top 10
    top = agent.find_vulnerable_districts(10)
    print(f"\n{'=' * 60}")
    print(f"  Top 10 공략 가능 지역구")
    print(f"{'=' * 60}")

    for d in top["top_districts"]:
        print(f"\n  {d['rank']}. {d['district']} ({d['name']}, {d['party']})")
        print(f"     취약도: {d['vulnerability_score']}점 | 승산: {d['win_chance']} | {d['priority']}")
        for wp in d["top_weak_points"]:
            print(f"     - {wp}")

    # 3. 1위 의원 공략 전략
    if top["top_districts"]:
        target_id = top["top_districts"][0]["lawmaker_id"]
        strategy = agent.get_attack_strategy(target_id)
        t = strategy["target"]
        print(f"\n{'=' * 60}")
        print(f"  공략 전략: {t['name']} ({t['district']})")
        print(f"{'=' * 60}")
        print(f"\n  [필요 정책]")
        for p in strategy["strategy"]["required_policies"]:
            print(f"    - {p}")
        print(f"\n  [약점 공략]")
        for a in strategy["strategy"]["attack_points"]:
            print(f"    - {a}")
        print(f"\n  [예상 득표율]")
        pred = strategy["prediction"]
        print(f"    AI정당: {pred['ai_party']}")
        print(f"    현역: {pred['incumbent']}")
        print(f"    기타: {pred['others']}")
        print(f"    판정: {pred['verdict']}")

    # 4. 리포트 생성
    report = agent.generate_report()
    print(f"\n리포트 저장: {report['report_file']}")
    print(f"\n{'=' * 60}")
    print("  완료!")
    print(f"{'=' * 60}")
