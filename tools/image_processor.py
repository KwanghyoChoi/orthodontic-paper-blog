#!/usr/bin/env python3
"""
Image Processor
PNG 이미지를 WebP로 변환하고 최적화
"""

import os
from pathlib import Path
from typing import List, Dict
from PIL import Image


def convert_png_to_webp(
    input_path: str,
    output_path: str = None,
    quality: int = 85
) -> Dict:
    """
    PNG 이미지를 WebP로 변환

    Args:
        input_path: 입력 PNG 파일 경로
        output_path: 출력 WebP 파일 경로 (None이면 자동 생성)
        quality: WebP 품질 (0-100, 기본 85)

    Returns:
        변환 결과 정보
    """
    if output_path is None:
        output_path = str(Path(input_path).with_suffix('.webp'))

    img = Image.open(input_path)
    original_size = os.path.getsize(input_path)

    # WebP로 저장
    img.save(output_path, 'WEBP', quality=quality, method=6)

    new_size = os.path.getsize(output_path)
    reduction = (1 - new_size / original_size) * 100

    return {
        "input": input_path,
        "output": output_path,
        "original_size_kb": round(original_size / 1024, 1),
        "new_size_kb": round(new_size / 1024, 1),
        "reduction_percent": round(reduction, 1),
        "width": img.width,
        "height": img.height
    }


def batch_convert_to_webp(
    input_dir: str,
    output_dir: str = None,
    quality: int = 85
) -> List[Dict]:
    """
    디렉토리의 모든 PNG를 WebP로 일괄 변환

    Args:
        input_dir: 입력 디렉토리
        output_dir: 출력 디렉토리 (None이면 input_dir/webp)
        quality: WebP 품질

    Returns:
        변환 결과 목록
    """
    input_path = Path(input_dir)

    if output_dir is None:
        output_path = input_path / "webp"
    else:
        output_path = Path(output_dir)

    output_path.mkdir(parents=True, exist_ok=True)

    results = []
    png_files = list(input_path.glob("*.png"))

    print(f"Converting {len(png_files)} PNG files to WebP...")

    for png_file in png_files:
        webp_file = output_path / f"{png_file.stem}.webp"
        result = convert_png_to_webp(str(png_file), str(webp_file), quality)
        results.append(result)
        print(f"  {png_file.name} -> {webp_file.name} ({result['reduction_percent']}% smaller)")

    total_original = sum(r['original_size_kb'] for r in results)
    total_new = sum(r['new_size_kb'] for r in results)

    print(f"\nTotal: {total_original:.1f}KB -> {total_new:.1f}KB ({(1-total_new/total_original)*100:.1f}% reduction)")

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python image_processor.py <input_dir> [output_dir] [quality]")
        print("Example: python image_processor.py output/images/selected output/images/webp 85")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    quality = int(sys.argv[3]) if len(sys.argv) > 3 else 85

    results = batch_convert_to_webp(input_dir, output_dir, quality)
    print(f"\nConverted {len(results)} images")
