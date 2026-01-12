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
│       ├─► research_expander   # Sonar API로 관련 연구 검색        │
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

#### 1. 관련 연구 비교 섹션 필수 포함

blog_writer가 생성하는 블로그에 **"다른 연구들은 뭐라고 하나?"** 섹션을 반드시 포함:

```markdown
## 다른 연구들은 뭐라고 하나?

### [기존 연구 1] - [저널명] ([연도])
- 구체적 수치 인용
- 본 논문과의 차이점

### 본 논문 vs 기존 연구 비교
| 항목 | 본 논문 | 기존 연구 | 해석 |
|-----|--------|----------|-----|
| ... | ... | ... | ... |

### 왜 수치가 다른가?
- 측정 방법 차이
- 대상 환자 차이
- 시스템 차이
```

**주의:** 참고문헌에만 나열하고 본문에서 언급하지 않으면 안 됨!

#### 2. 이미지 크롭 검증 루프 필수

image_curator 단계에서 크롭 후 반드시 Vision으로 검증:

```
크롭 실행 → Vision 검증 → 문제 발견 시 좌표 조정 → 재크롭 → 재검증
(최대 3회 반복, 해결 안 되면 페이지 전체 이미지 사용)
```

**검증 항목:**
- [ ] Figure 내용이 모두 포함되었는가?
- [ ] 캡션이 잘리지 않았는가?
- [ ] 다이어그램의 모든 요소(a, b, c...)가 보이는가?

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
5. **⚠️ 블로그에 "다른 연구들은 뭐라고 하나?" 섹션 필수** - Sonar 검색 결과를 본문에 통합
6. **⚠️ 이미지 크롭 후 반드시 Vision 검증** - 잘린 부분 있으면 재크롭 (최대 3회)
