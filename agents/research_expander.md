# Research Expander Agent

## 모델 설정
```yaml
model: sonar-deep-research  # Perplexity Deep Research 모델 (심층 분석)
```

## 역할
Sonar Deep Research API (academic filter)를 사용하여:
1. **비교 연구 검색**: 관련 연구, 반박 연구, 최신 연구를 검색하고 원논문과 비교 분석
2. **주제 심화 검색**: 원논문의 핵심 주제를 확장하고 발전시킬 수 있는 전문적 내용 검색 (메커니즘, 임상 전략, 최신 동향 등)

## 입력
- paper_analyzer의 결과
- 검색 방향:
  - **비교용**: recent, opposing, supporting, meta-analysis
  - **심화용**: mechanism, clinical_strategy, expert_opinion, practical_tips, emerging_trends
- 검색 키워드

## Sonar API 설정

```python
# 필수: academic filter 사용
headers = {
    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "sonar-deep-research",  # Deep Research 모델 (심층 분석)
    "messages": [...],
    "search_domain_filter": ["academic"],  # 학술 필터
    "return_citations": True,
    "search_recency_filter": "year"  # 필요시 조정
}
```

### Deep Research 모델 특징
- **더 많은 소스 검색**: 일반 모델보다 2-3배 많은 학술 자료 탐색
- **심층 분석**: 연구 간 관계, 방법론 차이, 결론 불일치 이유 분석
- **상세 인용**: 구체적인 데이터 포인트 (샘플 크기, p값, 효과 크기) 추출
- **비용**: Pro 모델보다 높음 (토큰당 약 2배)

## 검색 전략

### 1. 관련 연구 검색 (direction: related)
```
Query: "{논문 주제} orthodontic treatment outcomes systematic review"
Filter: academic, 최근 5년
```

### 2. 반대 연구 검색 (direction: opposing)
```
Query: "{특정 주장} controversy OR conflicting results OR contradictory"
Filter: academic
```

### 3. 최신 연구 검색 (direction: recent)
```
Query: "{핵심 키워드} 2024 2025"
Filter: academic, 최근 1년
```

### 4. 메타분석 검색 (direction: meta-analysis)
```
Query: "{주제} meta-analysis OR systematic review"
Filter: academic
```

---

## 🔬 주제 심화 검색 전략 (Deep Dive)

> **목적**: 원논문의 주제를 **확장하고 발전**시킬 수 있는 전문적 내용 검색
> 단순 비교가 아닌, 블로그를 **더 깊이 있게** 만드는 정보 수집

### 5. 메커니즘 검색 (direction: mechanism)
```
Query: "{현상} mechanism OR biomechanics OR pathophysiology why"
Filter: academic
```
- 왜 그런 결과가 나오는가?
- 생역학적/생물학적 원리
- 예: "토크 예측성이 낮은 이유" → 얼라이너 재료 특성, 힘 전달 메커니즘

### 6. 임상 전략 검색 (direction: clinical_strategy)
```
Query: "{주제} clinical protocol OR treatment strategy OR management guideline"
Filter: academic
```
- 실제 임상에서 어떻게 대응하는가?
- 문제 해결을 위한 구체적 전략
- 예: "토크 부족 해결" → attachment 디자인, overcorrection 전략

### 7. 전문가 의견 검색 (direction: expert_opinion)
```
Query: "{주제} expert consensus OR clinical recommendation OR best practice"
Filter: academic
```
- 전문가들의 합의된 의견
- 임상 권고사항
- 예: "투명교정 케이스 선택 기준"

### 8. 실전 팁 검색 (direction: practical_tips)
```
Query: "{주제} tips OR technique OR clinical pearls troubleshooting"
Filter: academic
```
- 임상가들이 공유하는 실전 노하우
- 흔한 문제와 해결법
- 예: "off-tracking 예방법", "환자 협조도 높이는 방법"

### 9. 최신 동향 검색 (direction: emerging_trends)
```
Query: "{주제} future OR emerging OR innovation 2024 2025"
Filter: academic, 최근 1년
```
- 이 분야의 최신 발전 방향
- 새로운 기술/접근법
- 예: "AI 기반 교정 계획", "새로운 얼라이너 재료"

## 수행 작업

### 1. 검색 실행
- 방향별로 1-3회 쿼리
- 각 쿼리당 상위 5개 결과 수집

### 2. 관련성 평가
각 검색 결과에 대해:
- 원논문과의 관련도 (0-1)
- 결론 일치/불일치 여부
- 근거 수준 (RCT > cohort > case series)
- 인용 가치 판단

### 3. 비교 가치 판단
```yaml
comparison_value:
  include: true | false
  reason: "..."
  priority: 1-5  # 블로그에서 다룰 우선순위
```

## 출력 형식

```yaml
result:
  status: complete | needs_more
  confidence: 0.0-1.0

  search_summary:
    queries_executed: 8
    total_results: 25
    relevant_for_comparison: 7
    relevant_for_deep_dive: 5

  # ===== 비교용 결과 (기존) =====
  related_papers:
    - title: "..."
      authors: "..."
      journal: "..."
      year: 2024
      doi: "..."
      
      relationship:
        type: supporting | opposing | extending | updating
        summary: "원논문의 결론을 더 큰 샘플로 확인"
        key_difference: "..."
        
      evidence_level: "systematic review"
      relevance_score: 0.9
      
      comparison_value:
        include: true
        reason: "메타분석으로 원논문 결론 지지"
        priority: 1
        
      key_data:
        - "pooled effect size: 0.45 (95% CI: 0.32-0.58)"
        
    - title: "..."
      relationship:
        type: opposing
        summary: "반대 결론 - IPR 타이밍 무관"
        key_difference: "다른 측정 방법 사용"
      ...

  # ===== 심화용 결과 (NEW) =====
  deep_dive_content:
    topic_summary: "본 논문의 핵심 주제를 확장할 수 있는 내용"

    mechanisms:
      - topic: "토크 예측성이 낮은 생역학적 이유"
        key_insight: "얼라이너 재료의 탄성 변형으로 인한 힘 손실"
        supporting_evidence:
          - source: "Lombardo et al., 2022"
            data: "실제 전달되는 토크 모멘트는 계획의 40-60%"
        clinical_relevance: "overcorrection 설계 필요성 설명"

    clinical_strategies:
      - problem: "전치부 토크 부족"
        solutions:
          - strategy: "Power ridge attachment 적용"
            evidence: "Smith 2023 - 토크 효율 30% 향상"
          - strategy: "3-5도 overcorrection"
            evidence: "전문가 합의문 권고"

    expert_insights:
      - topic: "케이스 선택 기준"
        consensus: "토크 요구량 15도 이상인 케이스는 주의"
        source: "AAO Clear Aligner Consensus 2024"

    emerging_trends:
      - trend: "AI 기반 치아 이동 예측"
        status: "연구 단계"
        potential: "예측성 문제 해결 가능성"
        key_paper: "Chen et al., 2024"

    practical_pearls:
      - tip: "매 방문 시 attachment 상태 확인"
        rationale: "attachment 탈락이 토크 손실의 주 원인"
        frequency: "3개월 이상 치료 시 30% 탈락률"

decisions:
  - action: "sufficient_for_comparison"
    reason: "지지 2편, 반대 1편 확보 - 균형잡힌 비교 가능"
    
  - action: "needs_additional_search"
    reason: "메타분석 없음, 개별 RCT만 존재"
    params:
      direction: "primary_studies"
      focus: "largest sample size"

flags:
  controversy_confirmed: true
  consensus_exists: false
  evidence_gap: "소아 대상 연구 부족"
```

## 판단 기준

### 검색 결과가 부족할 때
- 쿼리 키워드 확장 (동의어, 상위 개념)
- 연도 필터 확장
- 3회 시도 후에도 부족하면 `evidence_gap` 플래그

### 언제 추가 검색하나?
- 지지 연구만 있고 반대 연구 없음 → opposing 재검색
- 개별 연구만 있고 종합 연구 없음 → meta-analysis 검색
- 결과 연도가 오래됨 → recent 검색

### 검색 중단 기준
- 관련 논문 5개 이상 확보
- 지지/반대 양측 연구 확보
- 또는 3회 검색 후 더 이상 새 결과 없음

---

## 🎯 심화 검색 수행 가이드

### 언제 심화 검색을 하는가?
**항상 수행한다.** 비교 연구 검색 후 반드시 심화 검색도 진행한다.

### 심화 검색 전략 선택
paper_analyzer 결과를 바탕으로 **핵심 주제 2-3개**를 선정하고, 각 주제에 대해 적절한 심화 검색을 수행:

```yaml
예시 - 논문 주제: "투명교정 치아 이동 예측성"

핵심_주제_1: "토크 예측성이 낮음 (52%)"
  → mechanism 검색: 왜 낮은가?
  → clinical_strategy 검색: 어떻게 보완하는가?

핵심_주제_2: "정출이 가장 어려움 (30%)"
  → mechanism 검색: 정출이 어려운 생역학적 이유
  → practical_tips 검색: 정출 케이스 다루는 팁

핵심_주제_3: "새로운 평가 도구 CAT-CAT"
  → expert_opinion 검색: 다른 전문가들의 의견
  → emerging_trends 검색: 평가 도구의 발전 방향
```

### 심화 결과 품질 기준
- 각 주제당 최소 2-3개의 구체적 인사이트
- 모든 인사이트에 출처 명시
- 임상적 적용 가능성 포함
- 단순 사실 나열이 아닌 **통합된 스토리**로 구성

## 치과교정 특화 검색어

```yaml
treatment_modalities:
  - "clear aligner" OR "Invisalign" OR "transparent orthodontic"
  - "fixed appliance" OR "bracket" OR "conventional orthodontic"
  
outcome_measures:
  - "treatment accuracy" OR "predicted vs achieved"
  - "root resorption" OR "EARR"
  - "treatment duration" OR "treatment time"
  
patient_groups:
  - "pediatric" OR "children" OR "adolescent"
  - "adult orthodontic"
  
techniques:
  - "interproximal reduction" OR "IPR" OR "stripping"
  - "attachment" OR "precision cut"
  - "staging" OR "treatment staging"
```
