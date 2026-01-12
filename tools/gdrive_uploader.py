#!/usr/bin/env python3
"""
Google Drive Uploader
이미지를 Google Drive에 업로드하고 공유 URL 반환
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import requests

# .env 파일 로드
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass


class GDriveUploader:
    """Google Drive API를 사용한 파일 업로드"""

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        refresh_token: str = None,
        folder_id: str = None
    ):
        self.client_id = client_id or os.environ.get("GOOGLE_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("GOOGLE_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.environ.get("GOOGLE_REFRESH_TOKEN")
        self.folder_id = folder_id or os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError("Google Drive credentials required")

        self.access_token = None
        self._refresh_access_token()

    def _refresh_access_token(self):
        """Access token 갱신"""
        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token"
            }
        )
        response.raise_for_status()
        self.access_token = response.json()["access_token"]

    def upload_file(
        self,
        file_path: str,
        folder_id: str = None,
        make_public: bool = True
    ) -> Dict:
        """
        파일을 Google Drive에 업로드

        Args:
            file_path: 업로드할 파일 경로
            folder_id: 대상 폴더 ID (None이면 기본 폴더)
            make_public: 공개 링크 생성 여부

        Returns:
            업로드 결과 (file_id, web_view_link, direct_link)
        """
        folder_id = folder_id or self.folder_id
        file_name = Path(file_path).name

        # 파일 메타데이터
        metadata = {
            "name": file_name,
            "parents": [folder_id] if folder_id else []
        }

        # MIME 타입 결정
        ext = Path(file_path).suffix.lower()
        mime_types = {
            ".webp": "image/webp",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg"
        }
        mime_type = mime_types.get(ext, "application/octet-stream")

        # Multipart 업로드
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        # 메타데이터 파트
        files = {
            'metadata': ('metadata', json.dumps(metadata), 'application/json'),
            'file': (file_name, open(file_path, 'rb'), mime_type)
        }

        response = requests.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink",
            headers=headers,
            files=files
        )
        response.raise_for_status()
        result = response.json()

        file_id = result["id"]

        # 공개 권한 설정
        if make_public:
            self._make_public(file_id)

        # 직접 링크 생성 (이미지 임베딩용)
        # lh3.googleusercontent.com 형식이 리다이렉트 없이 직접 이미지 반환
        direct_link = f"https://lh3.googleusercontent.com/d/{file_id}"

        return {
            "file_id": file_id,
            "file_name": file_name,
            "web_view_link": result.get("webViewLink"),
            "direct_link": direct_link,
            "embed_url": direct_link  # WordPress 임베딩용
        }

    def _make_public(self, file_id: str):
        """파일을 공개로 설정"""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
            headers=headers,
            json={
                "role": "reader",
                "type": "anyone"
            }
        )
        response.raise_for_status()

    def batch_upload(
        self,
        file_paths: List[str],
        folder_id: str = None
    ) -> List[Dict]:
        """
        여러 파일 일괄 업로드

        Args:
            file_paths: 파일 경로 목록
            folder_id: 대상 폴더 ID

        Returns:
            업로드 결과 목록
        """
        results = []
        for file_path in file_paths:
            print(f"Uploading: {Path(file_path).name}...")
            result = self.upload_file(file_path, folder_id)
            results.append(result)
            print(f"  -> {result['direct_link']}")

        return results


def upload_images_to_gdrive(
    image_dir: str,
    pattern: str = "*.webp"
) -> Dict[str, str]:
    """
    이미지 디렉토리를 Google Drive에 업로드하고 URL 매핑 반환

    Args:
        image_dir: 이미지 디렉토리
        pattern: 파일 패턴

    Returns:
        {원본파일명: Google Drive URL} 매핑
    """
    uploader = GDriveUploader()
    image_path = Path(image_dir)
    files = list(image_path.glob(pattern))

    print(f"Found {len(files)} files to upload")

    url_mapping = {}
    for file_path in files:
        result = uploader.upload_file(str(file_path))
        # 원본 PNG 이름으로 매핑 (확장자만 다름)
        original_name = file_path.stem + ".png"
        url_mapping[original_name] = result["direct_link"]
        url_mapping[file_path.name] = result["direct_link"]
        print(f"  {file_path.name} -> {result['direct_link']}")

    # 매핑 저장
    mapping_path = image_path / "gdrive_urls.json"
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(url_mapping, f, indent=2, ensure_ascii=False)

    print(f"\nURL mapping saved to: {mapping_path}")
    return url_mapping


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python gdrive_uploader.py <image_dir> [pattern]")
        print("Example: python gdrive_uploader.py output/images/webp '*.webp'")
        sys.exit(1)

    image_dir = sys.argv[1]
    pattern = sys.argv[2] if len(sys.argv) > 2 else "*.webp"

    url_mapping = upload_images_to_gdrive(image_dir, pattern)
    print(f"\nUploaded {len(url_mapping)} files")
