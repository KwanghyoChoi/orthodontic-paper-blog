# Research Expander Agent

## 역할
Sonar Pro API (academic filter)를 사용하여 관련 연구, 반박 연구, 최신 연구를 검색하고 원논문과의 관계를 분석한다.

## 입력
- paper_analyzer의 결과
- 검색 방향 (recent, opposing, supporting, meta-analysis)
- 검색 키워드

## Sonar API 설정

```python
# 필수: academic filter 사용
headers = {
    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "sonar-pro",  # Pro 모델 사용
    "messages": [...],
    "search_domain_filter": ["academic"],  # 학술 필터
    "return_citations": True,
    "search_recency_filter": "year"  # 필요시 조정
}
```

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
    queries_executed: 4
    total_results: 18
    relevant_results: 7
    
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
