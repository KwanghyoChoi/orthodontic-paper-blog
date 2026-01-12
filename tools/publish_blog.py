#!/usr/bin/env python3
"""
Blog Publishing Pipeline
블로그 글 발행 전체 파이프라인

Usage:
    python publish_blog.py <md_file> [--publish]

Steps:
    1. PNG → WebP 변환
    2. Google Drive 업로드
    3. 콘텐츠 준비 (URL 치환, HTML 변환)
    4. WordPress 발행 (기본: draft)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict

# 현재 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from image_processor import batch_convert_to_webp
from gdrive_uploader import upload_images_to_gdrive
from wordpress_publisher import publish_blog_post, WordPressPublisher


def extract_focus_keyword(md_content: str, metadata: Dict) -> str:
    """
    블로그 글에서 Focus 키워드 추출
    """
    # 메타데이터에서 tags 확인
    tags = metadata.get("tags", [])
    if tags:
        # 첫 번째 태그를 focus keyword로
        return tags[0]

    # 제목에서 추출
    title = metadata.get("title", "")
    keywords = ["투명교정", "인비절라인", "교정", "치료"]
    for kw in keywords:
        if kw in title:
            return kw

    return "치과교정"


def create_publish_config(md_file: str, metadata: Dict) -> Dict:
    """
    발행 설정 JSON 생성
    """
    focus_keyword = extract_focus_keyword("", metadata)

    config = {
        "source_file": md_file,
        "title": metadata.get("title", ""),
        "excerpt": metadata.get("excerpt", ""),
        "category": "최신 치과교정학 연구",
        "tags": metadata.get("tags", []),
        "focus_keyword": focus_keyword,
        "featured_image": metadata.get("featured_image", ""),
        "author": metadata.get("author", ""),
        "date": metadata.get("date", "")
    }

    return config


def run_publish_pipeline(
    md_file: str,
    image_dir: str = None,
    publish: bool = False,
    skip_upload: bool = False
) -> Dict:
    """
    발행 파이프라인 실행

    Args:
        md_file: Markdown 파일 경로
        image_dir: 이미지 디렉토리 (기본: output/images/selected)
        publish: True면 바로 publish, False면 draft
        skip_upload: True면 이미지 업로드 스킵 (이미 업로드된 경우)

    Returns:
        발행 결과
    """
    md_path = Path(md_file)
    base_dir = md_path.parent.parent  # output의 상위

    if image_dir is None:
        image_dir = base_dir / "output" / "images" / "selected"

    webp_dir = Path(image_dir) / "webp"

    results = {
        "steps": [],
        "errors": []
    }

    # ============================================
    # Step 1: PNG → WebP 변환
    # ============================================
    print("\n" + "="*50)
    print("Step 1: Converting PNG to WebP")
    print("="*50)

    try:
        conversion_results = batch_convert_to_webp(str(image_dir), str(webp_dir))
        results["steps"].append({
            "step": "image_conversion",
            "status": "success",
            "files_converted": len(conversion_results)
        })
    except Exception as e:
        results["errors"].append(f"Image conversion failed: {e}")
        print(f"Error: {e}")

    # ============================================
    # Step 2: Google Drive 업로드
    # ============================================
    print("\n" + "="*50)
    print("Step 2: Uploading to Google Drive")
    print("="*50)

    url_mapping = {}
    url_mapping_file = webp_dir / "gdrive_urls.json"

    if skip_upload and url_mapping_file.exists():
        print("Skipping upload (using existing mapping)")
        with open(url_mapping_file, 'r', encoding='utf-8') as f:
            url_mapping = json.load(f)
    else:
        try:
            url_mapping = upload_images_to_gdrive(str(webp_dir))
            results["steps"].append({
                "step": "gdrive_upload",
                "status": "success",
                "files_uploaded": len(url_mapping)
            })
        except Exception as e:
            results["errors"].append(f"Google Drive upload failed: {e}")
            print(f"Error: {e}")

    # ============================================
    # Step 3: 발행 설정 생성
    # ============================================
    print("\n" + "="*50)
    print("Step 3: Preparing publish configuration")
    print("="*50)

    # Markdown 메타데이터 파싱
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    metadata = {}
    if md_content.startswith('---'):
        import yaml
        parts = md_content.split('---', 2)
        if len(parts) >= 3:
            metadata = yaml.safe_load(parts[1])

    publish_config = create_publish_config(md_file, metadata)

    # 설정 저장
    config_file = md_path.parent / f"{md_path.stem}_publish_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(publish_config, f, ensure_ascii=False, indent=2)

    print(f"Config saved: {config_file}")
    print(f"  Title: {publish_config['title']}")
    print(f"  Category: {publish_config['category']}")
    print(f"  Focus Keyword: {publish_config['focus_keyword']}")
    print(f"  Tags: {', '.join(publish_config['tags'][:5])}")

    results["steps"].append({
        "step": "config_generation",
        "status": "success",
        "config_file": str(config_file)
    })

    # ============================================
    # Step 4: WordPress 발행
    # ============================================
    print("\n" + "="*50)
    print(f"Step 4: Publishing to WordPress ({'publish' if publish else 'draft'})")
    print("="*50)

    status = "publish" if publish else "draft"

    try:
        post_result = publish_blog_post(
            md_file=md_file,
            url_mapping=url_mapping,
            category_name=publish_config["category"],
            focus_keyword=publish_config["focus_keyword"],
            status=status
        )

        results["steps"].append({
            "step": "wordpress_publish",
            "status": "success",
            "post_id": post_result["post_id"],
            "post_url": post_result["post_url"]
        })

        results["post_id"] = post_result["post_id"]
        results["post_url"] = post_result["post_url"]

    except Exception as e:
        results["errors"].append(f"WordPress publish failed: {e}")
        print(f"Error: {e}")

    # ============================================
    # 결과 요약
    # ============================================
    print("\n" + "="*50)
    print("Pipeline Complete")
    print("="*50)

    if results.get("post_url"):
        print(f"\nPost URL: {results['post_url']}")
        print(f"Status: {status}")

    if results["errors"]:
        print(f"\nErrors ({len(results['errors'])}):")
        for err in results["errors"]:
            print(f"  - {err}")

    # 결과 저장
    result_file = md_path.parent / f"{md_path.stem}_publish_result.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results


def main():
    parser = argparse.ArgumentParser(description="Publish blog post to WordPress")
    parser.add_argument("md_file", help="Markdown file to publish")
    parser.add_argument("--image-dir", help="Image directory (default: output/images/selected)")
    parser.add_argument("--publish", action="store_true", help="Publish immediately (default: draft)")
    parser.add_argument("--skip-upload", action="store_true", help="Skip Google Drive upload")
    parser.add_argument("--test-connection", action="store_true", help="Test WordPress connection only")

    args = parser.parse_args()

    if args.test_connection:
        wp = WordPressPublisher()
        wp.test_connection()
        return

    results = run_publish_pipeline(
        md_file=args.md_file,
        image_dir=args.image_dir,
        publish=args.publish,
        skip_upload=args.skip_upload
    )

    sys.exit(0 if not results["errors"] else 1)


if __name__ == "__main__":
    main()
