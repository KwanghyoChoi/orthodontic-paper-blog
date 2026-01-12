#!/usr/bin/env python3
"""
Sonar Pro API Tool
Perplexity Sonar Pro를 사용한 학술 논문 검색
"""

import os
import json
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# .env 파일 로드
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv 없으면 환경변수에서 직접 로드


@dataclass
class SearchResult:
    """검색 결과 단일 항목"""
    title: str
    url: str
    snippet: str
    source: str
    relevance_score: float = 0.0


@dataclass
class SonarResponse:
    """Sonar API 응답"""
    answer: str
    citations: List[Dict]
    search_results: List[SearchResult]
    model: str
    query: str


class SonarAPI:
    """Sonar Pro API 래퍼"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY 환경변수 또는 api_key 필요")
        
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar-deep-research"  # Deep Research 모델 사용 (심층 분석)
        
    def _make_request(
        self,
        query: str,
        system_prompt: str = "",
        domain_filter: List[str] = None,
        recency_filter: str = None
    ) -> Dict:
        """API 요청 실행"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "return_citations": True
        }
        
        # 학술 필터
        if domain_filter:
            payload["search_domain_filter"] = domain_filter
            
        # 최신성 필터
        if recency_filter:
            payload["search_recency_filter"] = recency_filter
        
        response = requests.post(self.base_url, headers=headers, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def search_academic(
        self,
        query: str,
        recency: str = "year",  # year, month, week, day
        system_context: str = ""
    ) -> SonarResponse:
        """
        학술 논문 검색
        
        Args:
            query: 검색 쿼리
            recency: 최신성 필터 (year, month, week, day)
            system_context: 추가 컨텍스트 (예: 도메인 정보)
        """
        
        system_prompt = """You are a research assistant specializing in orthodontics 
and dental literature. Provide accurate, well-cited information from peer-reviewed sources.
Focus on:
- Randomized controlled trials (RCTs)
- Systematic reviews and meta-analyses
- Recent publications from reputable journals

Always include specific data points (sample sizes, p-values, effect sizes) when available."""

        if system_context:
            system_prompt += f"\n\nAdditional context: {system_context}"
        
        raw_response = self._make_request(
            query=query,
            system_prompt=system_prompt,
            domain_filter=["academic"],
            recency_filter=recency
        )
        
        # 응답 파싱
        content = raw_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        citations = raw_response.get("citations", [])
        
        return SonarResponse(
            answer=content,
            citations=citations,
            search_results=[],  # API v2에서 별도 제공
            model=self.model,
            query=query
        )
    
    def find_related_research(
        self,
        paper_title: str,
        paper_findings: str,
        direction: str = "related"
    ) -> SonarResponse:
        """
        관련 연구 검색
        
        Args:
            paper_title: 원논문 제목
            paper_findings: 원논문 핵심 발견
            direction: related, opposing, supporting, recent, meta-analysis
        """
        
        query_templates = {
            "related": f'Find research papers related to: "{paper_title}". '
                      f'The paper found: {paper_findings}. '
                      f'List similar studies with their findings.',
            
            "opposing": f'Find research that contradicts or presents different conclusions from: '
                       f'"{paper_findings}". Include studies with conflicting results.',
            
            "supporting": f'Find research that supports the finding: "{paper_findings}". '
                         f'Include studies with similar conclusions and their sample sizes.',
            
            "recent": f'Find the most recent research (2023-2025) on: {paper_title}. '
                     f'Focus on new developments and updated findings.',
            
            "meta-analysis": f'Find systematic reviews and meta-analyses on the topic: {paper_title}. '
                            f'Include pooled effect sizes if available.'
        }
        
        query = query_templates.get(direction, query_templates["related"])
        
        return self.search_academic(
            query=query,
            recency="year" if direction == "recent" else None
        )
    
    def compare_studies(
        self,
        original_paper: Dict,
        comparison_papers: List[Dict]
    ) -> SonarResponse:
        """
        연구들 간 비교 분석 요청
        
        Args:
            original_paper: {"title": str, "findings": str, "methods": str}
            comparison_papers: [{"title": str, "findings": str}, ...]
        """
        
        papers_text = "\n".join([
            f"- {p['title']}: {p['findings']}" 
            for p in comparison_papers
        ])
        
        query = f"""Compare these orthodontic studies:

Original study: {original_paper['title']}
Findings: {original_paper['findings']}
Methods: {original_paper.get('methods', 'Not specified')}

Comparison studies:
{papers_text}

Analyze:
1. Key similarities and differences in findings
2. Methodological differences that might explain different results
3. Which study has stronger evidence (sample size, study design)
4. Clinical implications of the differences"""

        return self.search_academic(query)


def search_orthodontic_literature(
    topic: str,
    specific_question: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    치과교정 문헌 검색 편의 함수
    
    Args:
        topic: 검색 주제 (예: "IPR timing clear aligner")
        specific_question: 구체적 질문 (선택)
        api_key: API 키 (환경변수 대체 가능)
        
    Returns:
        검색 결과 딕셔너리
    """
    
    api = SonarAPI(api_key)
    
    query = f"orthodontic {topic}"
    if specific_question:
        query += f" {specific_question}"
    
    response = api.search_academic(query)
    
    return {
        "query": query,
        "answer": response.answer,
        "citations": response.citations,
        "model": response.model
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python sonar_api.py <search_query>")
        print("Example: python sonar_api.py 'IPR timing pediatric Invisalign'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    try:
        result = search_orthodontic_literature(query)
        print(f"\n=== Search: {result['query']} ===\n")
        print(result['answer'])
        print(f"\n=== Citations ({len(result['citations'])}) ===")
        for i, cite in enumerate(result['citations'], 1):
            print(f"{i}. {cite}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
