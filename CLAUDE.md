# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-agent system that transforms orthodontic research papers into professional blog posts. Takes a PDF paper as input, expands with related research via Perplexity Sonar API, performs comparative analysis, extracts/curates images, and generates publication-ready Korean blog content.

## Running the System

```bash
claude "논문 분석 시작: input/[논문파일명].pdf"
```

## Agent Pipeline

```
ORCHESTRATOR (this file)
     │
     ├─► paper_analyzer      # Extract paper core + assess complexity
     ├─► research_expander   # Find related/opposing studies via Sonar API
     ├─► comparator          # Cross-study comparison + controversy analysis
     ├─► image_curator       # Extract images + decide placement
     ├─► blog_writer         # Generate blog draft (model: sonnet)
     └─► quality_reviewer    # Review + re-invoke agents if score < 0.7
```

### 모델 설정
- `blog_writer`: **Sonnet 4.5** 사용 (글쓰기 품질 최적화)
- `image_curator`: **Sonnet 4.5** 사용 (Vision 분석 필수)
- 나머지 에이전트: 기본 모델

### 이미지 추출 방식 (2024 업데이트)
```
기존: PyMuPDF get_images() → 임베디드 비트맵만 추출 (벡터 Figure 누락)
개선: PDF 페이지 렌더링 → Claude Vision 분석 → Figure 식별
```

**핵심 도구:**
- `extractors/pdf_page_renderer.py`: PDF → 페이지 이미지 렌더링
- `image_curator` 에이전트: Vision으로 Figure 식별 및 선별

Each agent returns structured YAML with `status`, `confidence`, and `decisions`. Quality reviewer can re-invoke any agent up to 2 times (loop prevention).

## Agent Communication Protocol

```yaml
result:
  status: complete | needs_more | escalate
  confidence: 0.0-1.0
  content: "..."

decisions:
  - action: "request_related_research"
    target_agent: "research_expander"
    params: {key: value}

flags:
  complexity: low | medium | high
  controversy: true | false
```

## Environment Setup

Required:
```bash
export PERPLEXITY_API_KEY="pplx-..."  # Sonar Pro API
```

Python dependencies for extractors/tools:
- `PyMuPDF` (fitz) - PDF image extraction
- `requests` - API calls
- `python-dotenv` (optional) - .env loading

## Key Commands

```bash
# Extract images from PDF
python extractors/pdf_image_extractor.py input/paper.pdf output/images/

# Search orthodontic literature
python tools/sonar_api.py "IPR timing pediatric Invisalign"
```

## Session State

All progress tracked in `state/session.yaml`. On failure, resume from last successful checkpoint.

## Domain Context

- **Target audience**: Dentists, orthodontic residents, Invisalign practitioners
- **Tone**: Academic but accessible
- **Required content**: Clinical implications, practical application methods
- **Language**: Korean blog output
- **Platforms**: Naver Blog / WordPress compatible markdown

## Critical Rules

1. Always include image citation when using paper figures
2. Sonar API must use academic filter (`search_domain_filter: ["academic"]`)
3. Quality gate: sections scoring < 0.7 trigger agent re-invocation
4. Max 2 rework iterations per section to prevent infinite loops
