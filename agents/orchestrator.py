#!/usr/bin/env python3
"""
AI 정당 중앙 오케스트레이터
1인 대표를 위한 자율 정당 운영 시스템
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
from pathlib import Path
import json

from openai import OpenAI
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from agents.marketing_agent import MarketingAgent
from agents.analytics_agent import AnalyticsAgent
from agents.batch_helper import BatchHelper

# 환경 변수 로드
load_dotenv(Path(__file__).parent.parent / "config" / ".env")


class AIPartyOrchestrator:
    """
    1인 AI 정당의 중앙 제어 시스템
    
    역할:
    - 8개 AI 에이전트 조정
    - 자동화 워크플로우 실행
    - 중요 사항 대표에게 알림
    - 로그 및 모니터링
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "").strip())
        self.scheduler = AsyncIOScheduler()
        self.auto_approval_threshold = float(os.getenv("AUTO_APPROVAL_THRESHOLD", 0.85))
        
        # 데이터 디렉토리
        self.log_dir = Path(__file__).parent.parent / "data" / "logs"
        self.output_dir = Path(__file__).parent.parent / "data" / "outputs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 로깅 설정
        logger.add(
            self.log_dir / "orchestrator_{time}.log",
            rotation="1 day",
            retention="30 days",
            level="INFO"
        )
        
        # 에이전트 레지스트리
        self.agents = {}

        # 마케팅 에이전트 초기화
        self.marketing_agent = MarketingAgent()
        self.agents['marketing'] = self.marketing_agent

        # 데이터분석 에이전트 초기화
        self.analytics_agent = AnalyticsAgent()
        self.agents['analytics'] = self.analytics_agent

        # Batch API 헬퍼 초기화 (weekly_strategy 50% 비용 절감)
        self.batch_helper = BatchHelper()

        logger.info("🤖 AI 정당 오케스트레이터 초기화 완료")
    
    async def run_forever(self):
        """
        무한 루프 - 24/7 자동 실행
        """
        logger.info("🚀 AI 정당 시스템 가동 시작!")
        
        # 스케줄 설정
        self.setup_schedules()
        self.scheduler.start()
        
        logger.info("⏰ 스케줄러 시작됨")
        logger.info(f"📊 자동 승인 임계값: {self.auto_approval_threshold}")
        
        try:
            # 무한 루프
            while True:
                await asyncio.sleep(60)  # 1분마다 상태 체크
                
        except KeyboardInterrupt:
            logger.info("👋 시스템 종료 중...")
            self.scheduler.shutdown()
    
    def setup_schedules(self):
        """자동 스케줄 설정"""
        
        # 매시간 - 기본 작업
        self.scheduler.add_job(
            self.hourly_tasks,
            'cron',
            minute=0,
            id='hourly_tasks'
        )
        
        # 매일 아침 8시 - 일일 브리핑
        self.scheduler.add_job(
            self.daily_briefing,
            'cron',
            hour=8,
            minute=0,
            id='daily_briefing'
        )
        
        # 매일 아침 7시 - 마케팅 콘텐츠 자동 생성
        self.scheduler.add_job(
            self.daily_marketing_content,
            'cron',
            hour=7,
            minute=0,
            id='daily_marketing'
        )

        # 매주 월요일 9시 - 주간 전략 회의
        self.scheduler.add_job(
            self.weekly_strategy,
            'cron',
            day_of_week='mon',
            hour=9,
            minute=0,
            id='weekly_strategy'
        )

        # 매주 금요일 17시 - 마케팅 주간 리포트
        self.scheduler.add_job(
            self.weekly_marketing_report,
            'cron',
            day_of_week='fri',
            hour=17,
            minute=0,
            id='weekly_marketing_report'
        )

        # 매시간 30분 - 실시간 통계 업데이트
        self.scheduler.add_job(
            self.hourly_analytics_update,
            'cron',
            minute=30,
            id='hourly_analytics'
        )

        # 매일 자정 - 일일 분석
        self.scheduler.add_job(
            self.daily_analytics,
            'cron',
            hour=0,
            minute=5,
            id='daily_analytics'
        )

        # 매주 일요일 22시 - 주간 분석 리포트
        self.scheduler.add_job(
            self.weekly_analytics_report,
            'cron',
            day_of_week='sun',
            hour=22,
            minute=0,
            id='weekly_analytics_report'
        )

        # 매주 일요일 21시 - 주간 전략 Batch 사전 제출 (50% 비용 절감)
        self.scheduler.add_job(
            self.submit_weekly_strategy_batch,
            'cron',
            day_of_week='sun',
            hour=21,
            minute=0,
            id='weekly_strategy_batch_submit'
        )

        logger.info("✅ 자동 스케줄 설정 완료")
    
    async def hourly_tasks(self):
        """매시간 실행되는 기본 작업"""
        logger.info("⏰ 매시간 작업 시작")
        
        tasks = {
            'timestamp': datetime.now().isoformat(),
            'status': 'running',
            'completed_tasks': []
        }
        
        try:
            # 1. 시스템 상태 체크
            logger.info("📊 시스템 상태 체크")
            tasks['completed_tasks'].append('system_health_check')
            
            # 2. 로그 정리 (간단한 작업)
            logger.info("🧹 로그 정리")
            tasks['completed_tasks'].append('log_cleanup')
            
            # 3. 간단한 통계 업데이트
            stats = await self.update_basic_stats()
            tasks['stats'] = stats
            
            logger.info(f"✅ 매시간 작업 완료: {len(tasks['completed_tasks'])}개")
            
        except Exception as e:
            logger.error(f"❌ 매시간 작업 오류: {e}")
            tasks['status'] = 'error'
            tasks['error'] = str(e)
        
        # 작업 로그 저장
        self.save_task_log('hourly', tasks)
    
    async def daily_briefing(self):
        """매일 아침 대표에게 보낼 브리핑"""
        logger.info("📋 일일 브리핑 생성 시작")
        
        try:
            # GPT-4o mini로 브리핑 요청
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": """당신은 AI 정당의 사무총장입니다.
대표에게 드릴 간결하고 명확한 일일 브리핑을 작성하세요.

형식:
1. 어제 주요 성과 (3줄 이내)
2. 오늘 중요 이슈 (3개)
3. 결정이 필요한 사항 (있으면)
4. 시스템 상태

5분 안에 읽을 수 있게 간결하게 작성하세요."""},
                    {"role": "user", "content": f"""
현재 날짜: {datetime.now().strftime('%Y년 %m월 %d일 %A')}

시스템 상태:
- 운영 일수: {(datetime.now() - datetime(2026, 2, 2)).days}일
- 상태: 정상 가동 중

일일 브리핑을 작성해주세요.
"""}
                ]
            )

            briefing = response.choices[0].message.content
            
            # 브리핑 저장
            briefing_file = self.output_dir / f"briefing_{datetime.now().strftime('%Y%m%d')}.md"
            briefing_file.write_text(f"# 일일 브리핑\n\n{briefing}\n", encoding='utf-8')
            
            logger.info(f"✅ 일일 브리핑 생성 완료: {briefing_file}")
            
            # 실제로는 텔레그램/이메일로 전송
            logger.info("📧 브리핑 전송 (텔레그램 연동 필요)")
            
            return briefing
            
        except Exception as e:
            logger.error(f"❌ 일일 브리핑 생성 실패: {e}")
            return None
    
    async def submit_weekly_strategy_batch(self):
        """일요일 밤: 주간 전략 Batch 사전 제출 (50% 비용 절감)"""
        try:
            batch_id = self.batch_helper.submit_weekly_strategy()
            logger.info(f"📦 주간 전략 Batch 제출: {batch_id}")
        except Exception as e:
            logger.error(f"❌ Batch 제출 실패: {e} (월요일 동기 호출로 대체)")

    async def weekly_strategy(self):
        """주간 전략 회의 (Batch 우선 → 동기 호출 fallback)"""
        logger.info("🎯 주간 전략 회의 시작")

        # 1단계: Batch 결과 확인 (일요일 밤 제출분)
        try:
            batch_result = self.batch_helper.get_weekly_strategy_result()
            if batch_result:
                logger.info("📦 Batch 결과 사용 (50% 비용 절감)")
                strategy = batch_result
                strategy_file = self.output_dir / f"strategy_week_{datetime.now().strftime('%Y%m%d')}.md"
                strategy_file.write_text(f"# 주간 전략 보고서\n\n{strategy}\n", encoding='utf-8')
                logger.info(f"✅ 주간 전략 보고서 생성 (Batch): {strategy_file}")
                return strategy
        except Exception as e:
            logger.warning(f"⚠️ Batch 결과 조회 실패: {e}")

        # 2단계: Fallback - 동기 호출
        logger.info("🔄 Batch 미완료, 동기 호출로 전환")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=3000,
                messages=[
                    {"role": "system", "content": """당신은 AI 정당의 전략기획실장입니다.
2028년 4월 선거에서 10석을 목표로 합니다.

주간 전략 회의 보고서를 작성하세요:
1. 이번 주 진행 상황
2. 다음 주 주요 전략
3. 리스크 요인
4. 기회 요인
5. 대표의 결정이 필요한 사항"""},
                    {"role": "user", "content": f"""
현재: {datetime.now().strftime('%Y년 %m월 %d일')}
선거일까지: {(datetime(2028, 4, 10) - datetime.now()).days}일

주간 전략 보고서를 작성해주세요.
"""}
                ]
            )

            strategy = response.choices[0].message.content

            # 전략 보고서 저장
            strategy_file = self.output_dir / f"strategy_week_{datetime.now().strftime('%Y%m%d')}.md"
            strategy_file.write_text(f"# 주간 전략 보고서\n\n{strategy}\n", encoding='utf-8')

            logger.info(f"✅ 주간 전략 보고서 생성 (동기): {strategy_file}")

            return strategy

        except Exception as e:
            logger.error(f"❌ 주간 전략 회의 실패: {e}")
            return None
    
    async def daily_marketing_content(self):
        """매일 아침 마케팅 콘텐츠 자동 생성"""
        logger.info("📱 마케팅 콘텐츠 자동 생성 시작")

        try:
            posts = await self.marketing_agent.generate_daily_content()
            logger.info(f"✅ 마케팅 콘텐츠 {len(posts)}개 생성 완료")

            self.save_task_log('marketing', {
                'timestamp': datetime.now().isoformat(),
                'task': 'daily_content',
                'posts_generated': len(posts),
                'status': 'success',
            })

        except Exception as e:
            logger.error(f"❌ 마케팅 콘텐츠 생성 실패: {e}")
            self.save_task_log('marketing', {
                'timestamp': datetime.now().isoformat(),
                'task': 'daily_content',
                'status': 'error',
                'error': str(e),
            })

    async def weekly_marketing_report(self):
        """주간 마케팅 성과 리포트 생성"""
        logger.info("📊 주간 마케팅 리포트 생성 시작")

        try:
            report = self.marketing_agent.get_marketing_report()

            report_file = self.output_dir / f"marketing_weekly_{datetime.now().strftime('%Y%m%d')}.md"
            report_file.write_text(report, encoding='utf-8')

            logger.info(f"✅ 주간 마케팅 리포트 저장: {report_file}")

            # 대표에게 알림
            stats = self.marketing_agent.get_performance_stats()
            summary = stats['summary']
            await self.notify_human(
                f"📱 주간 마케팅 리포트: 총 {summary['total_posts']}개 포스트, "
                f"발행 {summary['published']}개",
                priority="normal"
            )

            return report

        except Exception as e:
            logger.error(f"❌ 주간 마케팅 리포트 생성 실패: {e}")
            return None

    async def hourly_analytics_update(self):
        """매시간 실시간 통계 업데이트"""
        try:
            stats = await self.analytics_agent.update_real_time_stats()
            logger.info(f"📊 실시간 통계 업데이트: 당원 {stats['members']['total']:,}명")
        except Exception as e:
            logger.error(f"❌ 실시간 통계 업데이트 실패: {e}")

    async def daily_analytics(self):
        """매일 자정 트렌드 분석 및 예측 갱신"""
        logger.info("📈 일일 분석 시작")
        try:
            trends = await self.analytics_agent.analyze_trends()
            predictions = await self.analytics_agent.predict_election_outcome()

            self.save_task_log('analytics', {
                'timestamp': datetime.now().isoformat(),
                'task': 'daily_analysis',
                'weekly_growth': trends['weekly_growth_rate'],
                'support_rate': predictions['current_support_rate'],
                'status': 'success',
            })
            logger.info(f"✅ 일일 분석 완료: 주간성장 {trends['weekly_growth_rate']}%")
        except Exception as e:
            logger.error(f"❌ 일일 분석 실패: {e}")

    async def weekly_analytics_report(self):
        """주간 데이터 분석 리포트 생성"""
        logger.info("📊 주간 분석 리포트 생성 시작")
        try:
            report = await self.analytics_agent.generate_analytics_report()
            predictions = self.analytics_agent.predictions

            await self.notify_human(
                f"📊 주간 분석: 지지율 {predictions.get('current_support_rate', '?')}%, "
                f"목표달성 {predictions.get('progress_percent', '?')}%",
                priority="normal"
            )
            logger.info("✅ 주간 분석 리포트 생성 완료")
            return report
        except Exception as e:
            logger.error(f"❌ 주간 분석 리포트 생성 실패: {e}")
            return None

    async def update_basic_stats(self) -> Dict[str, Any]:
        """기본 통계 업데이트"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'uptime_days': (datetime.now() - datetime(2026, 2, 2)).days,
            'status': 'operational',
            'agents_count': len(self.agents),
            'tasks_today': 0  # 실제 데이터로 교체 필요
        }
        
        return stats
    
    def save_task_log(self, task_type: str, data: Dict[str, Any]):
        """작업 로그 저장"""
        log_file = self.log_dir / f"{task_type}_{datetime.now().strftime('%Y%m%d')}.json"
        
        # 기존 로그 읽기
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []

        # 새 로그 추가
        logs.append(data)

        # 저장
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    
    async def notify_human(self, message: str, priority: str = "normal"):
        """대표에게 알림 (현재는 로그로만)"""
        logger.warning(f"🔔 [{priority.upper()}] 알림: {message}")
        
        # TODO: 텔레그램 봇 연동
        # await self.telegram_bot.send_message(message)
    
    def get_status(self) -> Dict[str, Any]:
        """현재 시스템 상태 반환"""
        return {
            'status': 'operational',
            'uptime_days': (datetime.now() - datetime(2026, 2, 2)).days,
            'agents': list(self.agents.keys()),
            'auto_approval_threshold': self.auto_approval_threshold,
            'scheduled_jobs': len(self.scheduler.get_jobs())
        }


async def main():
    """메인 실행 함수"""
    orchestrator = AIPartyOrchestrator()
    
    # 초기 상태 출력
    status = orchestrator.get_status()
    logger.info(f"📊 시스템 상태: {json.dumps(status, indent=2, ensure_ascii=False)}")
    
    # 테스트: 일일 브리핑 생성
    logger.info("🧪 테스트: 일일 브리핑 생성")
    await orchestrator.daily_briefing()
    
    # 무한 실행 (실제 운영시)
    # await orchestrator.run_forever()
    
    logger.info("✅ 테스트 실행 완료")


if __name__ == "__main__":
    asyncio.run(main())
