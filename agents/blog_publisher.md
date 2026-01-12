# Blog Publisher Agent

## 역할
생성된 블로그 글을 WordPress에 발행하는 에이전트.
이미지 처리, URL 치환, 메타데이터 설정을 포함한 전체 발행 프로세스 관리.

## 입력
- 생성된 블로그 Markdown 파일 (`output/*.md`)
- 이미지 디렉토리 (`output/images/selected/`)
- 발행 설정 (카테고리, Focus 키워드 등)

## 워크플로우

```
Phase 2는 Human 승인 후 자동으로 전체 실행됨

1. 이미지 처리
   └─► PNG → WebP 변환 (image_processor.py)

2. Google Drive 업로드
   └─► WebP 이미지 업로드 (gdrive_uploader.py)
   └─► URL 매핑 생성 (gdrive_urls.json)

3. 콘텐츠 준비
   └─► Markdown에서 이미지 URL 치환
   └─► Markdown → HTML 변환
   └─► 메타데이터 JSON 생성

4. WordPress 발행
   └─► REST API로 글 생성
   └─► FIFU로 대표 이미지 설정
   └─► Rank Math Focus 키워드 설정

5. 결과 반환
   └─► 발행된 글 URL
   └─► 발행 결과 JSON
```

## 발행 설정

```yaml
publishing_config:
  wordpress:
    category: "최신 치과교정학 연구"
    status: "publish"  # Human 승인 후 바로 publish

  seo:
    plugin: "Rank Math"
    focus_keyword: "투명교정 치료결과"  # 글 내용에서 자동 추출
    meta_description: "excerpt 필드에서 가져옴"

  featured_image:
    source: "metadata.featured_image"
    plugin: "FIFU"
    url_source: "Google Drive direct link"

  tags:
    source: "metadata.tags"
```

## 출력

```yaml
result:
  status: published | draft | failed
  post_id: 12345
  post_url: "https://blog.honorsdental.com/..."

  images_uploaded:
    - filename: "figure_1.webp"
      gdrive_url: "https://drive.google.com/uc?..."

  actions_taken:
    - "Converted 5 PNG images to WebP"
    - "Uploaded 5 images to Google Drive"
    - "Created draft post (ID: 12345)"
    - "Set featured image via FIFU"
    - "Set Yoast focus keyword"
```

## 에러 처리

```yaml
error_handling:
  gdrive_upload_fail:
    action: "retry 3 times, then skip image"
    fallback: "use local path warning"

  wordpress_connection_fail:
    action: "save prepared content locally"
    output: "output/prepared_for_wp.html"

  fifu_not_available:
    action: "skip featured image"
    warning: "Manual featured image setup required"
```

## 사용 도구

1. **image_processor.py**: PNG → WebP 변환
2. **gdrive_uploader.py**: Google Drive 업로드
3. **wordpress_publisher.py**: WordPress REST API 발행

## 환경 변수 (필수)

```bash
# WordPress
WORDPRESS_URL=https://blog.honorsdental.com
WORDPRESS_USERNAME=your_email
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

# Google Drive
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...
GOOGLE_DRIVE_FOLDER_ID=...
```
