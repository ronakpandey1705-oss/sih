import os
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    @classmethod
    def is_cloud_enabled(cls) -> bool:
        return bool(
            settings.CLOUDINARY_URL or (settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY)
        )

    @classmethod
    def upload_image(cls, local_path: str, public_id: Optional[str] = None, folder: str = "packsure/evidence") -> str:
        if not cls.is_cloud_enabled():
            return local_path
        try:
            import cloudinary
            import cloudinary.uploader

            if settings.CLOUDINARY_URL:
                cloudinary.config(cloudinary_url=settings.CLOUDINARY_URL)
            else:
                cloudinary.config(
                    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                    api_key=settings.CLOUDINARY_API_KEY,
                    api_secret=settings.CLOUDINARY_API_SECRET,
                    secure=True
                )
            res = cloudinary.uploader.upload(
                local_path,
                public_id=public_id,
                folder=folder,
                resource_type="image"
            )
            secure_url = res.get("secure_url")
            logger.info("Uploaded image to Cloudinary: %s", secure_url)
            return secure_url or local_path
        except Exception as e:
            logger.error("Cloudinary upload failed: %s. Using local path.", e)
            return local_path

    @classmethod
    def resolve_local_image_path(cls, path_or_url: Optional[str], scan_id: Optional[str] = None) -> Optional[str]:
        """
        Ensure a valid local file path is available for image processing (OCR, OpenCV).
        Checks local filesystem first. If given an HTTP/HTTPS cloud URL, checks local cache
        or downloads to local cache directory.
        """
        if not path_or_url:
            return None

        # 1. Direct local path exists
        if os.path.exists(path_or_url):
            return path_or_url

        # 2. Check in scan_id upload directory if local file exists with matching name
        if scan_id:
            scan_dir = os.path.join(settings.UPLOAD_DIR, scan_id)
            if os.path.isdir(scan_dir):
                files = os.listdir(scan_dir)
                if files:
                    for f in files:
                        fp = os.path.join(scan_dir, f)
                        if os.path.isfile(fp) and not f.endswith("_preprocessed.png"):
                            return fp

        # 3. If path is a remote HTTP/HTTPS URL, download to cache directory
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            try:
                import urllib.request
                import hashlib
                cache_dir = os.path.join(settings.UPLOAD_DIR, "cloud_cache")
                os.makedirs(cache_dir, exist_ok=True)
                url_hash = hashlib.md5(path_or_url.encode("utf-8")).hexdigest()
                ext = os.path.splitext(path_or_url.split("?")[0])[1] or ".jpg"
                local_cache_path = os.path.join(cache_dir, f"{url_hash}{ext}")
                if not os.path.exists(local_cache_path):
                    urllib.request.urlretrieve(path_or_url, local_cache_path)
                return local_cache_path
            except Exception as e:
                logger.error("Failed to download cloud image %s: %s", path_or_url, e)
                return None

        return None
