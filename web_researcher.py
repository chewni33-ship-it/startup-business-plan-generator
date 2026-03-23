"""Firecrawl 기반 웹 리서치 모듈

사업계획서 작성에 필요한 시장 조사 데이터를 자동으로 수집합니다.
- 시장 규모 및 동향
- 경쟁사 분석
- 산업 트렌드
"""

import logging
from firecrawl import Firecrawl

logger = logging.getLogger(__name__)


def create_client(api_key: str) -> Firecrawl:
    """Firecrawl 클라이언트 생성"""
    return Firecrawl(api_key=api_key)


def search_market_data(client: Firecrawl, item_name: str, target_market: str, keywords: list) -> list[dict]:
    """시장 규모 및 동향 데이터 검색"""
    queries = [
        f"{target_market} 시장 규모 전망 2025 2026",
        f"{item_name} 시장 동향 트렌드",
    ]
    if keywords:
        queries.append(f"{' '.join(keywords[:3])} 시장 분석")

    results = []
    for query in queries:
        try:
            resp = client.search(query, limit=3)
            data = resp if isinstance(resp, list) else resp.get("data", resp.get("web", []))
            for item in data:
                if isinstance(item, dict):
                    results.append({
                        "query": query,
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("markdown", item.get("description", ""))[:1000],
                    })
            logger.info(f"검색 완료: {query} -> {len(data)}건")
        except Exception as e:
            logger.warning(f"검색 실패: {query} - {e}")

    return results


def search_competitors(client: Firecrawl, item_name: str, core_technology: str) -> list[dict]:
    """경쟁사/경쟁 제품 분석 데이터 검색"""
    queries = [
        f"{item_name} 경쟁사 분석 비교",
        f"{core_technology} 스타트업 기업 현황",
    ]

    results = []
    for query in queries:
        try:
            resp = client.search(query, limit=3)
            data = resp if isinstance(resp, list) else resp.get("data", resp.get("web", []))
            for item in data:
                if isinstance(item, dict):
                    results.append({
                        "query": query,
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("markdown", item.get("description", ""))[:1000],
                    })
            logger.info(f"경쟁사 검색 완료: {query} -> {len(data)}건")
        except Exception as e:
            logger.warning(f"경쟁사 검색 실패: {query} - {e}")

    return results


def search_industry_trends(client: Firecrawl, core_technology: str, business_type: str) -> list[dict]:
    """산업 트렌드 및 정책 데이터 검색"""
    queries = [
        f"{core_technology} 기술 트렌드 전망 2026",
        f"초기창업패키지 {business_type} 정부지원사업 동향",
    ]

    results = []
    for query in queries:
        try:
            resp = client.search(query, limit=3)
            data = resp if isinstance(resp, list) else resp.get("data", resp.get("web", []))
            for item in data:
                if isinstance(item, dict):
                    results.append({
                        "query": query,
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("markdown", item.get("description", ""))[:1000],
                    })
            logger.info(f"트렌드 검색 완료: {query} -> {len(data)}건")
        except Exception as e:
            logger.warning(f"트렌드 검색 실패: {query} - {e}")

    return results


def scrape_url(client: Firecrawl, url: str) -> str:
    """특정 URL의 콘텐츠를 마크다운으로 스크랩"""
    try:
        result = client.scrape(url, formats=["markdown"])
        if isinstance(result, dict):
            return result.get("markdown", "")[:3000]
        return ""
    except Exception as e:
        logger.warning(f"스크랩 실패: {url} - {e}")
        return ""


def run_full_research(firecrawl_api_key: str, item_name: str, core_technology: str,
                      target_market: str, business_type: str, keywords: list,
                      progress_callback=None) -> dict:
    """전체 웹 리서치 실행 후 결과를 구조화하여 반환"""
    client = create_client(firecrawl_api_key)
    research = {"market": [], "competitors": [], "trends": []}

    if progress_callback:
        progress_callback(0.0, "시장 데이터 검색 중...")
    research["market"] = search_market_data(client, item_name, target_market, keywords)

    if progress_callback:
        progress_callback(0.33, "경쟁사 분석 데이터 검색 중...")
    research["competitors"] = search_competitors(client, item_name, core_technology)

    if progress_callback:
        progress_callback(0.66, "산업 트렌드 검색 중...")
    research["trends"] = search_industry_trends(client, core_technology, business_type)

    if progress_callback:
        progress_callback(1.0, "웹 리서치 완료!")

    logger.info(
        f"리서치 완료: 시장 {len(research['market'])}건, "
        f"경쟁사 {len(research['competitors'])}건, "
        f"트렌드 {len(research['trends'])}건"
    )
    return research


def format_research_for_prompt(research: dict) -> str:
    """리서치 결과를 Claude 프롬프트에 삽입할 텍스트로 변환"""
    parts = []

    if research.get("market"):
        parts.append("【시장 조사 데이터】")
        for item in research["market"][:6]:
            parts.append(f"- [{item['title']}] {item['content'][:300]}")

    if research.get("competitors"):
        parts.append("\n【경쟁사 분석 데이터】")
        for item in research["competitors"][:4]:
            parts.append(f"- [{item['title']}] {item['content'][:300]}")

    if research.get("trends"):
        parts.append("\n【산업 트렌드 데이터】")
        for item in research["trends"][:4]:
            parts.append(f"- [{item['title']}] {item['content'][:300]}")

    return "\n".join(parts) if parts else ""
