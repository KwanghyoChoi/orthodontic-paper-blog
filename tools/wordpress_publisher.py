#!/usr/bin/env python3
"""
WordPress Publisher
WordPress REST API를 사용한 블로그 글 발행
"""

import os
import re
import json
import base64
from pathlib import Path
from typing import Dict, Optional, List
import requests
import markdown

# .env 파일 로드
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass


class WordPressPublisher:
    """WordPress REST API 클라이언트"""

    def __init__(
        self,
        site_url: str = None,
        username: str = None,
        app_password: str = None
    ):
        self.site_url = (site_url or os.environ.get("WORDPRESS_URL")).rstrip('/')
        self.username = username or os.environ.get("WORDPRESS_USERNAME")
        self.app_password = app_password or os.environ.get("WORDPRESS_APP_PASSWORD")

        if not all([self.site_url, self.username, self.app_password]):
            raise ValueError("WordPress credentials required")

        # Basic Auth 헤더
        credentials = f"{self.username}:{self.app_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json"
        }

        self.api_url = f"{self.site_url}/wp-json/wp/v2"

    def test_connection(self) -> bool:
        """연결 테스트"""
        try:
            response = requests.get(
                f"{self.api_url}/users/me",
                headers=self.headers
            )
            response.raise_for_status()
            user = response.json()
            print(f"Connected as: {user['name']} ({user['slug']})")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def get_categories(self) -> List[Dict]:
        """카테고리 목록 조회"""
        response = requests.get(
            f"{self.api_url}/categories",
            headers=self.headers,
            params={"per_page": 100}
        )
        response.raise_for_status()
        return response.json()

    def get_or_create_category(self, name: str) -> int:
        """카테고리 ID 조회 또는 생성"""
        categories = self.get_categories()

        for cat in categories:
            if cat["name"] == name:
                return cat["id"]

        # 카테고리 생성
        response = requests.post(
            f"{self.api_url}/categories",
            headers=self.headers,
            json={"name": name}
        )
        response.raise_for_status()
        return response.json()["id"]

    def get_tags(self) -> List[Dict]:
        """태그 목록 조회"""
        response = requests.get(
            f"{self.api_url}/tags",
            headers=self.headers,
            params={"per_page": 100}
        )
        response.raise_for_status()
        return response.json()

    def get_or_create_tags(self, tag_names: List[str]) -> List[int]:
        """태그 ID 목록 조회 또는 생성"""
        existing_tags = self.get_tags()
        tag_map = {t["name"]: t["id"] for t in existing_tags}

        tag_ids = []
        for name in tag_names:
            if name in tag_map:
                tag_ids.append(tag_map[name])
            else:
                # 태그 생성
                response = requests.post(
                    f"{self.api_url}/tags",
                    headers=self.headers,
                    json={"name": name}
                )
                if response.status_code == 201:
                    tag_ids.append(response.json()["id"])

        return tag_ids

    def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        categories: List[int] = None,
        tags: List[int] = None,
        excerpt: str = None,
        meta: Dict = None
    ) -> Dict:
        """
        새 글 생성

        Args:
            title: 글 제목
            content: HTML 본문
            status: publish, draft, pending
            categories: 카테고리 ID 목록
            tags: 태그 ID 목록
            excerpt: 요약문
            meta: 메타 필드 (Yoast SEO 등)

        Returns:
            생성된 글 정보
        """
        post_data = {
            "title": title,
            "content": content,
            "status": status
        }

        if categories:
            post_data["categories"] = categories
        if tags:
            post_data["tags"] = tags
        if excerpt:
            post_data["excerpt"] = excerpt
        if meta:
            post_data["meta"] = meta

        response = requests.post(
            f"{self.api_url}/posts",
            headers=self.headers,
            json=post_data
        )
        response.raise_for_status()
        return response.json()

    def set_featured_image_fifu(
        self,
        post_id: int,
        image_url: str
    ) -> bool:
        """
        FIFU 플러그인을 사용하여 대표 이미지 설정

        Note: FIFU 플러그인이 REST API 지원하는 경우 사용
        그렇지 않으면 post meta로 직접 설정
        """
        # FIFU는 보통 fifu_image_url 메타 필드 사용
        response = requests.post(
            f"{self.api_url}/posts/{post_id}",
            headers=self.headers,
            json={
                "meta": {
                    "fifu_image_url": image_url,
                    "_thumbnail_ext_url": image_url  # 일부 FIFU 버전
                }
            }
        )

        if response.status_code == 200:
            print(f"Featured image set: {image_url}")
            return True
        else:
            print(f"Failed to set featured image: {response.text}")
            return False

    def set_rankmath_meta(
        self,
        post_id: int,
        focus_keyword: str,
        meta_description: str = None
    ) -> bool:
        """
        Rank Math SEO 메타 설정
        """
        meta_data = {
            "rank_math_focus_keyword": focus_keyword
        }

        if meta_description:
            meta_data["rank_math_description"] = meta_description

        response = requests.post(
            f"{self.api_url}/posts/{post_id}",
            headers=self.headers,
            json={"meta": meta_data}
        )

        if response.status_code == 200:
            print(f"Rank Math focus keyword set: {focus_keyword}")
            return True
        else:
            print(f"Failed to set Rank Math meta: {response.text}")
            return False


def md_to_html(md_content: str) -> str:
    """
    Markdown을 WordPress 호환 HTML로 변환

    Args:
        md_content: Markdown 문자열

    Returns:
        HTML 문자열
    """
    # YAML front matter 제거
    if md_content.startswith('---'):
        parts = md_content.split('---', 2)
        if len(parts) >= 3:
            md_content = parts[2].strip()

    # Markdown -> HTML 변환
    html = markdown.markdown(
        md_content,
        extensions=[
            'tables',
            'fenced_code',
            'nl2br',
            'sane_lists'
        ]
    )

    return html


def replace_image_urls(
    content: str,
    url_mapping: Dict[str, str]
) -> str:
    """
    로컬 이미지 경로를 Google Drive URL로 치환

    Args:
        content: HTML 또는 Markdown 본문
        url_mapping: {로컬파일명: GDrive URL} 매핑

    Returns:
        URL이 치환된 본문
    """
    for local_path, gdrive_url in url_mapping.items():
        # Markdown 이미지 문법
        content = re.sub(
            rf'!\[([^\]]*)\]\([^)]*{re.escape(Path(local_path).stem)}[^)]*\)',
            rf'![\1]({gdrive_url})',
            content
        )
        # HTML img 태그
        content = re.sub(
            rf'src="[^"]*{re.escape(Path(local_path).stem)}[^"]*"',
            f'src="{gdrive_url}"',
            content
        )

    return content


def publish_blog_post(
    md_file: str,
    url_mapping: Dict[str, str],
    category_name: str = "최신 치과교정학 연구",
    focus_keyword: str = None,
    status: str = "draft"
) -> Dict:
    """
    블로그 글 발행 통합 함수

    Args:
        md_file: Markdown 파일 경로
        url_mapping: 이미지 URL 매핑
        category_name: 카테고리 이름
        focus_keyword: Yoast Focus 키워드
        status: publish 또는 draft

    Returns:
        발행 결과
    """
    # Markdown 파일 읽기
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # YAML front matter 파싱
    metadata = {}
    if md_content.startswith('---'):
        import yaml
        parts = md_content.split('---', 2)
        if len(parts) >= 3:
            metadata = yaml.safe_load(parts[1])

    # 이미지 URL 치환
    md_content = replace_image_urls(md_content, url_mapping)

    # HTML 변환
    html_content = md_to_html(md_content)

    # WordPress 발행
    wp = WordPressPublisher()

    # 연결 테스트
    if not wp.test_connection():
        raise Exception("WordPress connection failed")

    # 카테고리 설정
    category_id = wp.get_or_create_category(category_name)

    # 태그 설정
    tag_ids = []
    if "tags" in metadata:
        tag_ids = wp.get_or_create_tags(metadata["tags"])

    # 글 생성
    title = metadata.get("title", Path(md_file).stem)
    excerpt = metadata.get("excerpt", "")

    post = wp.create_post(
        title=title,
        content=html_content,
        status=status,
        categories=[category_id],
        tags=tag_ids,
        excerpt=excerpt
    )

    post_id = post["id"]
    print(f"Post created: {post['link']} (ID: {post_id})")

    # 대표 이미지 설정 (FIFU)
    # 우선순위: 1) 논문 첫 페이지 2) metadata의 featured_image
    featured_url = None

    # 논문 첫 페이지 이미지 찾기
    for key in url_mapping:
        if 'paper_first_page' in key or 'first_page' in key:
            featured_url = url_mapping[key]
            break

    # 없으면 metadata에서 가져오기
    if not featured_url:
        featured_image = metadata.get("featured_image")
        if featured_image:
            featured_name = Path(featured_image).name
            webp_name = Path(featured_image).stem + ".webp"
            featured_url = url_mapping.get(webp_name) or url_mapping.get(featured_name)

    if featured_url:
        wp.set_featured_image_fifu(post_id, featured_url)

    # Rank Math SEO Focus 키워드
    if focus_keyword:
        wp.set_rankmath_meta(post_id, focus_keyword, excerpt[:160] if excerpt else None)

    return {
        "post_id": post_id,
        "post_url": post["link"],
        "status": status,
        "title": title
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python wordpress_publisher.py <md_file> [url_mapping.json] [status]")
        print("Example: python wordpress_publisher.py output/blog.md output/images/webp/gdrive_urls.json draft")
        sys.exit(1)

    md_file = sys.argv[1]

    # URL 매핑 로드
    url_mapping = {}
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            url_mapping = json.load(f)

    status = sys.argv[3] if len(sys.argv) > 3 else "draft"

    result = publish_blog_post(md_file, url_mapping, status=status)
    print(f"\nPublished: {result['post_url']}")
