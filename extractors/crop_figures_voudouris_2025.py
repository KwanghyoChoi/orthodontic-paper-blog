"""
Figure Cropper for Voudouris et al. 2025 - Aligner MA Guidelines
"""
from PIL import Image
import os

# 크롭할 Figure 정의
figures = [
    {
        "page": 1,
        "figure_id": "paper_cover",
        "name": "Paper Cover - Title & Abstract",
        "crop_box": (50, 50, 1190, 850),  # 상단 제목/저자/초록 일부
    },
    {
        "page": 4,
        "figure_id": "fig1a_checklist_1_6",
        "name": "Fig. 1A - Aligner MA Checklist (1-6)",
        "crop_box": (50, 75, 1190, 1220),  # 하단 더 확장 (캡션 포함)
    },
    {
        "page": 5,
        "figure_id": "fig1b_checklist_7_12",
        "name": "Fig. 1B - Aligner MA Checklist (7-12)",
        "crop_box": (50, 75, 1190, 1220),  # 하단 더 확장 (캡션 포함)
    },
    {
        "page": 6,
        "figure_id": "fig3c_peak_vs_prepeak",
        "name": "Fig. 3C - Peak vs Pre-Peak Growth",
        "crop_box": (50, 50, 1190, 550),  # 좌측 확장 (Y축), 하단 확장 (캡션)
    },
    {
        "page": 7,
        "figure_id": "fig2_supercorrection",
        "name": "Fig. 2 - Supercorrection Prescribed (SCRx)",
        "crop_box": (50, 50, 1190, 680),  # 하단 더 확장 (X축 라벨 포함)
    },
]

def crop_figures():
    input_dir = "output/images/pages"
    output_dir = "output/images/cropped"
    os.makedirs(output_dir, exist_ok=True)

    for fig in figures:
        page_file = f"paper_gdrive_page_{fig['page']}.png"
        input_path = os.path.join(input_dir, page_file)
        output_path = os.path.join(output_dir, f"{fig['figure_id']}.png")

        if not os.path.exists(input_path):
            print(f"File not found: {input_path}")
            continue

        img = Image.open(input_path)
        cropped = img.crop(fig['crop_box'])
        cropped.save(output_path, quality=95)

        print(f"Cropped: {fig['name']}")
        print(f"  Input: {input_path}")
        print(f"  Output: {output_path}")
        print(f"  Crop box: {fig['crop_box']}")
        print(f"  Size: {cropped.size}")
        print()

if __name__ == "__main__":
    crop_figures()
    print("Done!")
