#!/usr/bin/env python3
"""
PDF Page Renderer
PDF 페이지를 고해상도 이미지로 렌더링하여 저장
- 기존 get_images() 방식의 한계 극복
- 벡터 그래픽 Figure도 캡처 가능
"""

import fitz  # PyMuPDF
import os
import json
from pathlib import Path
from typing import List, Dict


def render_pdf_pages(
    pdf_path: str,
    output_dir: str = "output/images",
    dpi: int = 150,
    skip_first_page: bool = False
) -> List[Dict]:
    """
    PDF의 각 페이지를 고해상도 이미지로 렌더링

    Args:
        pdf_path: PDF 파일 경로
        output_dir: 출력 디렉토리
        dpi: 해상도 (150 권장 - 품질과 파일 크기 균형)
        skip_first_page: 첫 페이지(표지) 스킵 여부

    Returns:
        렌더링된 페이지 정보 리스트
    """

    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    pdf_name = Path(pdf_path).stem

    # DPI를 zoom factor로 변환 (72 DPI 기준)
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    pages = []
    start_page = 1 if skip_first_page else 0

    for page_num in range(start_page, len(doc)):
        page = doc[page_num]

        # 페이지를 이미지로 렌더링
        pix = page.get_pixmap(matrix=matrix)

        # 파일명 생성
        filename = f"{pdf_name}_page_{page_num + 1}.png"
        filepath = os.path.join(output_dir, filename)

        # 이미지 저장
        pix.save(filepath)

        # 페이지 텍스트에서 Figure/Table 언급 찾기
        text = page.get_text()
        figure_mentions = find_figure_mentions(text)

        pages.append({
            "page_number": page_num + 1,
            "filename": filename,
            "filepath": filepath,
            "width": pix.width,
            "height": pix.height,
            "has_figures": len(figure_mentions) > 0,
            "figure_mentions": figure_mentions,
            "text_preview": text[:500] if text else ""
        })

        print(f"  Rendered page {page_num + 1}/{len(doc)}: {filename}")

    doc.close()

    # 메타데이터 저장
    metadata_path = os.path.join(output_dir, f"{pdf_name}_pages.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)

    return pages


def find_figure_mentions(text: str) -> List[str]:
    """
    텍스트에서 Figure/Table 언급 찾기
    """
    import re

    mentions = []
    patterns = [
        r'Figure\s+\d+[\.:]?\s*[^\n]{0,100}',
        r'Fig\.\s*\d+[\.:]?\s*[^\n]{0,100}',
        r'Table\s+\d+[\.:]?\s*[^\n]{0,100}',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        mentions.extend([m.strip() for m in matches])

    # 중복 제거
    return list(set(mentions))


def get_pages_with_figures(pages: List[Dict]) -> List[Dict]:
    """
    Figure가 포함된 페이지만 필터링
    """
    return [p for p in pages if p["has_figures"]]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_page_renderer.py <pdf_path> [output_dir] [dpi]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output/images"
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 150

    print(f"Rendering PDF pages: {pdf_path}")
    print(f"Output directory: {output_dir}")
    print(f"DPI: {dpi}")
    print()

    pages = render_pdf_pages(pdf_path, output_dir, dpi)

    print(f"\nRendered {len(pages)} pages")

    figure_pages = get_pages_with_figures(pages)
    print(f"Pages with figure mentions: {len(figure_pages)}")
    for p in figure_pages:
        print(f"  - Page {p['page_number']}: {p['figure_mentions']}")
