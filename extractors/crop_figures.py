#!/usr/bin/env python3
"""
Figure Cropper
렌더링된 페이지에서 Figure 영역만 크롭하여 저장
"""

from PIL import Image
import os


def crop_and_save(input_path: str, output_path: str, crop_box: tuple, figure_name: str):
    """
    이미지에서 지정된 영역을 크롭하여 저장

    Args:
        input_path: 원본 이미지 경로
        output_path: 저장할 경로
        crop_box: (left, top, right, bottom) 픽셀 좌표
        figure_name: Figure 이름 (로깅용)
    """
    img = Image.open(input_path)
    cropped = img.crop(crop_box)
    cropped.save(output_path, quality=95)
    print(f"  [OK] {figure_name}: {cropped.size[0]}x{cropped.size[1]}px -> {output_path}")
    return cropped.size


def main():
    base_dir = "output/images/pages"
    output_dir = "output/images/selected"
    os.makedirs(output_dir, exist_ok=True)

    # 파일명 prefix
    prefix = "2020_EJO_Treatment outcome with orthodontic aligners"

    # Figure 크롭 정보 (페이지 분석 결과 기반)
    # 페이지 크기: 1276x1648px (150 DPI)
    # 좌표: (left, top, right, bottom)
    figures = [
        {
            "page": 4,
            "figure_id": "figure_1_prisma",
            "name": "Figure 1 - PRISMA Flow Diagram",
            "crop_box": (130, 80, 1150, 1200),  # PRISMA diagram 영역 (최종 박스까지 포함)
        },
        {
            "page": 7,
            "figure_id": "figure_2_forest_plot_abo",
            "name": "Figure 2 - Forest Plot (ABO-OGS)",
            "crop_box": (70, 1050, 1200, 1450),  # Forest plot 하단
        },
        {
            "page": 8,
            "figure_id": "figure_3_composite_forest",
            "name": "Figure 3 - Composite Forest Plot",
            "crop_box": (70, 70, 1200, 1580),  # 전체 composite plot
        },
        {
            "page": 9,
            "figure_id": "figure_4_treatment_duration",
            "name": "Figure 4 - Forest Plot (Treatment Duration)",
            "crop_box": (70, 60, 1200, 530),  # 상단 forest plot
        },
    ]

    print(f"Cropping {len(figures)} figures...\n")

    for fig in figures:
        input_path = os.path.join(base_dir, f"{prefix}_page_{fig['page']}.png")
        output_path = os.path.join(output_dir, f"{fig['figure_id']}.png")

        if not os.path.exists(input_path):
            print(f"  [FAIL] Page {fig['page']} not found: {input_path}")
            continue

        crop_and_save(input_path, output_path, fig["crop_box"], fig["name"])

    print(f"\nDone! Cropped figures saved to: {output_dir}/")


if __name__ == "__main__":
    main()
