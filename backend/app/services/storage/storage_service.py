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
