# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-agent system that transforms orthodontic research papers into professional blog posts, then publishes to WordPress. Takes a PDF paper as input, expands with related research via Perplexity Sonar API, performs comparative analysis, extracts/curates images, generates publication-ready Korean blog content, and publishes to WordPress with image hosting on Google Drive.

## Running the System

```bash
# 1. 블로그 글 생성
claude "논문 분석 시작: input/[논문파일명].pdf"

# 2. WordPress 발행 (draft)
python tools/publish_blog.py output/[블로그파일].md

# 3. WordPress 발행 (publish - 확인 후)
python tools/publish_blog.py output/[블로그파일].md --publish

# 4. 발행 완료 후 임시 파일 정리
rm -rf tmpclaude-*
```

## Full Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: CONTENT GENERATION                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ORCHESTRATOR (this file)                                        │
│       │                                                          │
│       ├─► paper_analyzer      # 논문 핵심 추출 + 복잡도 판단     │
│       ├─► research_expander   # Sonar API: 비교 연구 + 심화 검색   │
│       ├─► comparator          # 연구 간 비교 + 논쟁점 분석        │
│       ├─► image_curator       # Vision으로 Figure 식별            │
│       ├─► blog_writer         # 블로그 초안 생성 (model: sonnet)  │
│       └─► quality_reviewer    # 검토 + score < 0.7 시 재호출      │
│                                                                  │
│                         ▼                                        │
│              [output/*.md + images 생성]                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │          [HUMAN]              │
              │   글 내용 + 이미지 확인       │
              │   수정 요청 또는 승인         │
              └───────────────┬───────────────┘
                              │ 승인
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2: PUBLISHING (자동)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  python tools/publish_blog.py output/blog.md --publish           │
│                                                                  │
│  ┌────────────────┐    ┌────────────────┐                       │
│  │image_processor │───►│gdrive_uploader │                       │
│  │ PNG → WebP     │    │ Drive 업로드   │                       │
│  └────────────────┘    └───────┬────────┘                       │
│                                │                                 │
│                       [이미지 URL 매핑]                          │
│                                │                                 │
│                                ▼                                 │
│                    ┌────────────────────┐                       │
│                    │ content_preparer   │                       │
│                    │ MD→HTML + URL치환  │                       │
│                    │ + 메타데이터 JSON  │                       │
│                    └─────────┬──────────┘                       │
│                              │                                   │
│                              ▼                                   │
│                    ┌────────────────────┐                       │
│                    │wordpress_publisher │                       │
│                    │ REST API 발행      │                       │
│                    │ + FIFU 대표이미지  │                       │
│                    │ + Rank Math KW     │                       │
│                    └────────────────────┘                       │
│                              │                                   │
│                              ▼                                   │
│                    [발행 완료 + URL 반환]                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 모델 설정
- `blog_writer`: **Claude Sonnet 4.5** 사용 (글쓰기 품질 최적화)
- `image_curator`: **Claude Sonnet 4.5** 사용 (Vision 분석 필수)
- `research_expander`: **Sonar Deep Research** 사용 (심층 학술 검색)
- 나머지 에이전트: 기본 모델

### 이미지 추출 방식 (2024 업데이트)
```
기존: PyMuPDF get_images() → 임베디드 비트맵만 추출 (벡터 Figure 누락)
개선: PDF 페이지 렌더링 → Claude Vision 분석 → Figure 식별 → 크롭 → 검증 루프
```

**핵심 도구:**
- `extractors/pdf_page_renderer.py`: PDF → 페이지 이미지 렌더링
- `extractors/crop_figures_[논문ID].py`: Figure 영역 크롭 (논문별 생성)
- `image_curator` 에이전트: Vision으로 Figure 식별, 크롭, **검증 및 재크롭**

### ⚠️ 필수 워크플로우 (2025 업데이트)

#### 1. 블로그 구조: 원논문 내용 → 정리 → 심화 섹션 → 참고문헌

**블로그 순서:**
1. 원논문 핵심 내용 (배경, 방법, 발견, 임상적 의미)
2. **정리** (원논문 내용 마무리)
3. **🔬 한걸음 더 깊이 들여다보기** (심화 섹션 - 마지막에 배치)
4. 참고문헌

#### 2. "한걸음 더 깊이 들여다보기" 섹션 (필수)

blog_writer가 생성하는 블로그 **"정리" 다음, "참고문헌" 앞**에 심화 섹션을 반드시 포함:

> **목적**: 비교 분석 + 심화 확장을 **하나의 밀도 있는 섹션**으로 통합

```markdown
## 🔬 한걸음 더 깊이 들여다보기

> 💡 이 섹션은 논문 내용을 넘어선 심화 분석입니다

### 최신 연구들은 어떻게 보나?
- 관련 연구 2-3개 인용 (저자/저널/연도/수치)
- 비교 테이블 (본 논문 vs 최신 연구)
- 왜 결과가 다른가 분석

### 왜 [현상]인가? - [메커니즘]
- 핵심 현상의 생역학적/생물학적 원리

### [주제]는 왜 필요한가? - [문제점]
- 문제에 대한 구체적 해결책/임상 전략

### [논쟁점] - [쟁점] 논쟁
- 전문가 합의, 가이드라인 인용

### 앞으로의 방향
- 새로운 기술, 재료, 방법
```

**research_expander의 검색 결과를 통합:**
- comparison_data: 최신 연구들과의 비교
- deep_dive_content: 메커니즘, 임상전략, 전문가의견, 최신동향

**주의:** 비교 분석과 심화 분석을 **별도 섹션으로 분리하지 말 것!**

#### 3. 이미지 처리 필수 워크플로우 ⚠️

**필수 이미지 목록:**
1. **논문 커버 (Page 1)** - 대표이미지 + "원논문 소개" 섹션에 삽입
2. **핵심 Figure들** - 본문에 삽입 (차트, 다이어그램, 테이블 등)

**전체 이미지 처리 흐름:**
```
1. PDF 페이지 렌더링 (pdf_page_renderer.py)
2. Vision으로 각 페이지 분석 → Figure 식별
3. 크롭 스크립트 생성 (crop_figures_[논문ID].py)
   - Page 1: 논문 커버 (제목, 저널, 저자, 초록 상단)
   - 핵심 Figure들: 차트, 다이어그램 등
4. 크롭 실행
5. Vision 검증 → 문제 발견 시 좌표 조정 → 재크롭 (최대 3회)
6. WebP 변환 (image_processor.py)
7. Google Drive 업로드 (gdrive_uploader.py)
8. 블로그 마크다운에 URL 삽입:
   - featured_image: 논문 커버 URL
   - "원논문 소개" 섹션: 논문 커버 이미지
   - 본문: 각 Figure 이미지
9. WordPress 발행
```

**검증 체크리스트:**
- [ ] 논문 커버 (Page 1)가 크롭되었는가?
- [ ] 논문 커버가 대표이미지(featured_image)로 설정되었는가?
- [ ] 논문 커버가 "원논문 소개" 섹션에 삽입되었는가?
- [ ] 모든 Figure 내용이 완전히 포함되었는가?
- [ ] 캡션이 잘리지 않았는가?
- [ ] 다이어그램의 모든 요소(a, b, c...)가 보이는가?
- [ ] 모든 이미지가 WebP로 변환되었는가?
- [ ] 모든 이미지가 Google Drive에 업로드되었는가?

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

Required in `.env`:
```bash
# Perplexity Sonar API
PERPLEXITY_API_KEY=pplx-...

# WordPress 발행
WORDPRESS_URL=https://your-blog.com
WORDPRESS_USERNAME=your_email
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

# Google Drive 이미지 저장
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...
GOOGLE_DRIVE_FOLDER_ID=...
```

Python dependencies:
```bash
pip install PyMuPDF requests python-dotenv Pillow markdown pyyaml
```

## Directory Structure

```
├── agents/                 # 에이전트 지침서 (md)
│   ├── paper_analyzer.md   # 논문 분석
│   ├── research_expander.md # Sonar 검색 + 심화
│   ├── comparator.md       # 연구 비교
│   ├── image_curator.md    # 이미지 크롭/검증
│   ├── blog_writer.md      # 블로그 작성
│   └── quality_reviewer.md # 품질 검토
├── extractors/             # PDF/이미지 처리
│   ├── pdf_page_renderer.py
│   └── crop_figures_*.py   # 논문별 크롭 스크립트
├── tools/                  # 유틸리티
│   ├── sonar_api.py        # Perplexity Sonar API
│   ├── image_processor.py  # PNG→WebP 변환
│   ├── gdrive_uploader.py  # Google Drive 업로드
│   └── publish_blog.py     # WordPress 발행
├── templates/              # 템플릿
│   └── blog_format.md      # 블로그 포맷 + 체크리스트
├── input/                  # 입력 PDF
├── output/                 # 생성된 블로그 + 이미지
│   ├── images/pages/       # 렌더링된 페이지
│   ├── images/cropped/     # 크롭된 Figure
│   └── images/selected/webp/ # WebP 변환본
└── state/                  # 세션 상태
```

## Key Commands

```bash
# PDF 페이지 렌더링
python extractors/pdf_page_renderer.py input/paper.pdf output/images/pages/

# Figure 크롭
python extractors/crop_figures.py

# 학술 문헌 검색
python tools/sonar_api.py "IPR timing pediatric Invisalign"

# 이미지 WebP 변환
python tools/image_processor.py output/images/selected/

# Google Drive 업로드
python tools/gdrive_uploader.py output/images/selected/webp/

# WordPress 발행 (draft)
python tools/publish_blog.py output/blog.md

# WordPress 발행 (publish)
python tools/publish_blog.py output/blog.md --publish

# WordPress 연결 테스트
python tools/publish_blog.py --test-connection
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
5. **⚠️ 블로그 구조: 원논문 내용 → 정리 → 심화 섹션 → 참고문헌** (순서 준수)
6. **⚠️ "한걸음 더 깊이 들여다보기" 섹션 필수** - "정리" 다음, "참고문헌" 앞에 배치
7. **⚠️ 심화 섹션에 비교 분석 + 메커니즘 + 임상전략 + 전문가의견 통합** (별도 섹션으로 분리 금지)
8. **⚠️ 논문 커버 (Page 1) 필수** - 대표이미지 + "원논문 소개" 섹션에 삽입
9. **⚠️ 이미지 크롭 후 반드시 Vision 검증** - 잘린 부분 있으면 재크롭 (최대 3회)
10. **⚠️ 발행 전 이미지 체크** - 모든 이미지 WebP 변환 + Google Drive 업로드 + URL 삽입 확인
