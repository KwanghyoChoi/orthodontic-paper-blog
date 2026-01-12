#!/usr/bin/env python3
"""
Figure Cropper for 2025 IJOS Expert Consensus Paper
렌더링된 페이지에서 Figure 영역만 크롭하여 저장

페이지 크기: 1241x1648px
"""

from PIL import Image
import os


def crop_and_save(input_path: str, output_path: str, crop_box: tuple, figure_name: str):
    """
    이미지에서 지정된 영역을 크롭하여 저장
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

    prefix = "2025. IJOS.  Expert consensus on the clinical strategies for orthodontic treatment with clear aligners"

    # 페이지 크기: 1241x1648px
    # 크롭 좌표: (left, top, right, bottom)
    # Vision 분석 기반 수정된 좌표
    figures = [
        # Page 1: 논문 첫 페이지 (대표이미지)
        {
            "page": 1,
            "figure_id": "paper_first_page",
            "name": "Paper First Page",
            "crop_box": (50, 50, 1190, 950),
        },
        # Page 2: Fig. 1 (Predictability diagram) - 전체 다이어그램 + 캡션
        {
            "page": 2,
            "figure_id": "fig1_predictability",
            "name": "Fig. 1 - Predictability of tooth movements",
            "crop_box": (50, 280, 700, 1150),  # 다이어그램 전체 (Extrusion 30%까지)
        },
        # Page 2: Table 1 (CAT-CAT)
        {
            "page": 2,
            "figure_id": "table1_cat_cat",
            "name": "Table 1 - CAT-CAT Grading",
            "crop_box": (50, 1150, 1190, 1620),
        },
        # Page 3: Fig. 2 (Schematic illustration) - 전체 다이어그램 + 캡션
        {
            "page": 3,
            "figure_id": "fig2_principles",
            "name": "Fig. 2 - Principles of clear aligner therapy",
            "crop_box": (50, 30, 1190, 720),  # 6개 단계 다이어그램 + 캡션
        },
        # Page 4: Fig. 3 (Flowchart) - 9단계 전체 + 캡션
        {
            "page": 4,
            "figure_id": "fig3_procedures",
            "name": "Fig. 3 - Overview procedures flowchart",
            "crop_box": (50, 30, 1190, 900),  # 1-9 단계 전체 + "Fig. 3" 캡션
        },
        # Page 5: Fig. 4 (Arch expansion) - a-e 사진 + 캡션
        {
            "page": 5,
            "figure_id": "fig4_arch_expansion",
            "name": "Fig. 4 - Arch expansion planning",
            "crop_box": (50, 30, 1190, 620),  # a-e 사진 + 전체 캡션
        },
        # Page 5: Fig. 5 (Elastic tractions) - a-b 사진 + 캡션
        {
            "page": 5,
            "figure_id": "fig5_elastic_modes",
            "name": "Fig. 5 - Elastic traction modes",
            "crop_box": (50, 620, 1190, 1050),  # a-b 사진 + 전체 캡션
        },
        # Page 6: Fig. 6 (V pattern) - a-e 전체 다이어그램 + 캡션
        {
            "page": 6,
            "figure_id": "fig6_v_pattern",
            "name": "Fig. 6 - V pattern for molar distalization",
            "crop_box": (50, 30, 1190, 820),  # a-e 모든 다이어그램 + 캡션
        },
        # Page 8: Fig. 7 (Elastic biomechanics) - a-c 사진 + 3D 다이어그램 + 캡션
        {
            "page": 8,
            "figure_id": "fig7_elastic_biomechanics",
            "name": "Fig. 7 - Elastic tractions and biomechanics",
            "crop_box": (50, 30, 1190, 650),  # 사진 + 다이어그램 + 전체 캡션
        },
        # Page 9: Fig. 8 (Frog pattern) - 스테이징 + 사진 + 캡션
        {
            "page": 9,
            "figure_id": "fig8_frog_pattern",
            "name": "Fig. 8 - Frog pattern for anterior intrusion",
            "crop_box": (50, 30, 1190, 750),  # 스테이징 패널 + 치아 다이어그램 + 임상사진 + 캡션
        },
        # Page 11: Fig. 9 (Off-tracking) - a-f 사진 + 캡션
        {
            "page": 11,
            "figure_id": "fig9_offtracking",
            "name": "Fig. 9 - Aligner off-tracking",
            "crop_box": (50, 30, 1190, 560),  # 6개 사진 (a-f) + 캡션
        },
        # Page 11: Fig. 10 (Off-tracking resolution) - a-d 사진 + 캡션
        {
            "page": 11,
            "figure_id": "fig10_offtracking_resolution",
            "name": "Fig. 10 - Off-tracking resolution strategies",
            "crop_box": (50, 530, 1190, 1050),  # 4개 사진 (a-d) + 전체 캡션
        },
    ]

    print(f"Cropping {len(figures)} figures from 2025 IJOS paper...\n")

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
