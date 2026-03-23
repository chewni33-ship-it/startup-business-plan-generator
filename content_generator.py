"""Claude API를 사용한 섹션별 콘텐츠 생성"""

import json
import logging
from dataclasses import asdict

import anthropic

from models import UserInput, SectionContent
from section_config import SYSTEM_PROMPT, SECTION_PROMPTS

logger = logging.getLogger(__name__)


def _build_prompt(section_id: str, user_input: UserInput) -> str:
    """섹션별 프롬프트 생성"""
    template = SECTION_PROMPTS.get(section_id)
    if not template:
        raise ValueError(f"Unknown section: {section_id}")

    # 팀원 정보를 문자열로 변환
    team_info = ""
    if user_input.team_members:
        parts = []
        for tm in user_input.team_members:
            parts.append(f"- {tm.position}: {tm.role} ({tm.capability}, {tm.status})")
        team_info = "\n".join(parts)
    else:
        team_info = "팀원 정보 미입력 (예시 생성 필요)"

    # 키워드를 문자열로
    keywords_str = ", ".join(user_input.keywords) if user_input.keywords else "없음"

    return template.format(
        company_name=user_input.company_name or "미입력",
        item_name=user_input.item_name or "미입력",
        category=user_input.category or user_input.item_name,
        core_technology=user_input.core_technology or "미입력",
        target_market=user_input.target_market or "미입력",
        target_customers=user_input.target_customers or "미입력",
        problem_description=user_input.problem_description or "미입력",
        competitive_advantage=user_input.competitive_advantage or "미입력",
        business_type=user_input.business_type or "지식서비스",
        output_type=user_input.output_type or "미정",
        total_budget=user_input.total_budget,
        government_fund=user_input.government_fund,
        self_fund_cash=user_input.self_fund_cash,
        self_fund_inkind=user_input.self_fund_inkind,
        team_info=team_info,
        keywords=keywords_str,
    )


def generate_section(section_id: str, user_input: UserInput, api_key: str) -> SectionContent:
    """단일 섹션의 콘텐츠를 Claude API로 생성"""
    client = anthropic.Anthropic(api_key=api_key)
    prompt = _build_prompt(section_id, user_input)

    for attempt in range(3):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()
            # JSON 블록 추출 (```json ... ``` 형태 처리)
            if text.startswith("```"):
                lines = text.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.startswith("```") and not in_block:
                        in_block = True
                        continue
                    elif line.startswith("```") and in_block:
                        break
                    elif in_block:
                        json_lines.append(line)
                text = "\n".join(json_lines)

            data = json.loads(text)
            return SectionContent(section_id=section_id, generated_text=data)

        except json.JSONDecodeError as e:
            logger.warning(f"JSON 파싱 실패 (시도 {attempt+1}/3): {e}")
            if attempt == 2:
                # 최종 실패 시 원본 텍스트를 그대로 사용
                return SectionContent(
                    section_id=section_id,
                    generated_text={"raw_text": response.content[0].text if response else "생성 실패"}
                )
        except anthropic.APIError as e:
            logger.error(f"API 오류 (시도 {attempt+1}/3): {e}")
            if attempt == 2:
                raise


def generate_all_sections(user_input: UserInput, api_key: str, progress_callback=None):
    """모든 섹션의 콘텐츠를 순차 생성"""
    section_ids = [
        "overview_summary",
        "problem_recognition",
        "solution_plan",
        "schedule_agreement",
        "budget_plan",
        "growth_strategy",
        "schedule_full",
        "team_intro",
        "team_composition",
        "partnerships",
    ]

    results = {}
    total = len(section_ids)

    for i, section_id in enumerate(section_ids):
        if progress_callback:
            progress_callback(i / total, f"생성 중: {section_id} ({i+1}/{total})")

        try:
            content = generate_section(section_id, user_input, api_key)
            results[section_id] = content
            logger.info(f"섹션 생성 완료: {section_id}")
        except Exception as e:
            logger.error(f"섹션 생성 실패: {section_id} - {e}")
            results[section_id] = SectionContent(
                section_id=section_id,
                generated_text={"error": str(e)}
            )

    if progress_callback:
        progress_callback(1.0, "모든 섹션 생성 완료!")

    return results
