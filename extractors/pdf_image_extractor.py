#!/usr/bin/env python3
"""
PDF Image Extractor
논문 PDF에서 이미지(figures, tables, charts)를 추출
"""

import fitz  # PyMuPDF
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import re


def extract_images_from_pdf(
    pdf_path: str,
    output_dir: str = "output/images",
    min_width: int = 100,
    min_height: int = 100
) -> List[Dict]:
    """
    PDF에서 이미지를 추출하고 메타데이터를 반환
    
    Args:
        pdf_path: PDF 파일 경로
        output_dir: 이미지 저장 디렉토리
        min_width: 최소 너비 (작은 아이콘 제외)
        min_height: 최소 높이
        
    Returns:
        추출된 이미지 정보 리스트
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    pdf_name = Path(pdf_path).stem
    
    images = []
    image_counter = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)
                
                # 최소 크기 필터
                if width < min_width or height < min_height:
                    continue
                
                image_counter += 1
                image_id = f"fig_{image_counter}"
                filename = f"{pdf_name}_{image_id}.{image_ext}"
                filepath = os.path.join(output_dir, filename)
                
                # 이미지 저장
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
                
                # 캡션 추출 시도
                caption = extract_caption_near_image(page, img)
                
                # 이미지 타입 추정
                image_type = guess_image_type(caption, width, height)
                
                images.append({
                    "id": image_id,
                    "filename": filename,
                    "filepath": filepath,
                    "page": page_num + 1,
                    "width": width,
                    "height": height,
                    "format": image_ext,
                    "caption_text": caption,
                    "type": image_type,
                    "xref": xref
                })
                
            except Exception as e:
                print(f"Error extracting image {xref}: {e}")
                continue
    
    doc.close()
    
    # 메타데이터 저장
    metadata_path = os.path.join(output_dir, f"{pdf_name}_images.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(images, f, ensure_ascii=False, indent=2)
    
    return images


def extract_caption_near_image(page, img_info) -> Optional[str]:
    """
    이미지 근처의 캡션 텍스트 추출 시도
    """
    try:
        # 페이지 전체 텍스트에서 Figure/Table 패턴 찾기
        text = page.get_text()
        
        # Figure X. 또는 Table X. 패턴 찾기
        patterns = [
            r'Figure\s+\d+[\.:]\s*[^\n]+',
            r'Fig\.\s*\d+[\.:]\s*[^\n]+',
            r'Table\s+\d+[\.:]\s*[^\n]+',
            r'그림\s+\d+[\.:]\s*[^\n]+',
            r'표\s+\d+[\.:]\s*[^\n]+'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return None
        
    except Exception:
        return None


def guess_image_type(caption: Optional[str], width: int, height: int) -> str:
    """
    이미지 타입 추정 (figure, table, chart, photo)
    """
    if caption:
        caption_lower = caption.lower()
        if 'table' in caption_lower or '표' in caption:
            return 'table'
        if 'chart' in caption_lower or 'graph' in caption_lower:
            return 'chart'
        if 'photo' in caption_lower or 'photograph' in caption_lower:
            return 'photo'
    
    # 가로세로 비율로 추정
    ratio = width / height if height > 0 else 1
    
    if ratio > 2:  # 매우 넓으면 테이블일 가능성
        return 'table'
    elif 0.8 < ratio < 1.2:  # 정사각형에 가까우면 사진일 가능성
        return 'photo'
    else:
        return 'figure'


def get_high_priority_images(images: List[Dict], max_count: int = 5) -> List[Dict]:
    """
    블로그에 포함할 우선순위 높은 이미지 선별
    """
    # 크기와 타입 기반 우선순위
    def priority_score(img):
        score = 0
        
        # 크기 점수 (큰 이미지 선호)
        area = img['width'] * img['height']
        score += min(area / 100000, 5)  # 최대 5점
        
        # 타입 점수
        type_scores = {
            'chart': 4,
            'figure': 3,
            'photo': 3,
            'table': 2
        }
        score += type_scores.get(img['type'], 1)
        
        # 캡션 있으면 가산점
        if img['caption_text']:
            score += 2
        
        return score
    
    sorted_images = sorted(images, key=priority_score, reverse=True)
    return sorted_images[:max_count]


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_image_extractor.py <pdf_path> [output_dir]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output/images"
    
    print(f"Extracting images from: {pdf_path}")
    images = extract_images_from_pdf(pdf_path, output_dir)
    
    print(f"\nExtracted {len(images)} images:")
    for img in images:
        print(f"  - {img['id']}: {img['type']} ({img['width']}x{img['height']})")
        if img['caption_text']:
            print(f"    Caption: {img['caption_text'][:50]}...")
    
    print(f"\nHigh priority images for blog:")
    for img in get_high_priority_images(images):
        print(f"  - {img['id']}: {img['filename']}")
