"""
PDF Builder
===========
Converts page screenshots into a single PDF file.

Uses img2pdf for efficient PDF generation while maintaining
image quality with optional JPEG optimization.
"""

import io
from typing import Optional

import img2pdf
from PIL import Image

from topdf.exceptions import PDFBuildError


class PDFBuilder:
    """Converts screenshots to a single PDF file.

    Features:
    - Normalizes image dimensions for consistent output
    - Optional JPEG optimization for smaller file sizes
    - Handles various image formats (PNG, RGBA, etc.)

    Usage:
        builder = PDFBuilder(optimize=True)
        pdf_bytes = builder.build(screenshots)
    """

    # Default dimensions for consistent output
    DEFAULT_WIDTH = 1920
    DEFAULT_HEIGHT = 1080

    # JPEG quality for optimization (0-100)
    JPEG_QUALITY = 85

    # Maximum dimension before resizing (prevents memory issues)
    MAX_DIMENSION = 4096

    def __init__(
        self,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        optimize: bool = True,
    ):
        """Initialize PDF builder.

        Args:
            target_width: Target width for all pages (uses first image if None)
            target_height: Target height for all pages (uses first image if None)
            optimize: Convert to JPEG for smaller file size
        """
        self.target_width = target_width
        self.target_height = target_height
        self.optimize = optimize

    def _load_image(self, image_bytes: bytes) -> Image.Image:
        """Load image from bytes.

        Args:
            image_bytes: PNG image as bytes

        Returns:
            PIL Image object
        """
        return Image.open(io.BytesIO(image_bytes))

    def _normalize_dimensions(
        self, images: list[Image.Image]
    ) -> list[Image.Image]:
        """Resize images to consistent dimensions.

        Uses target dimensions if set, otherwise uses first image's size.

        Args:
            images: List of PIL Image objects

        Returns:
            List of resized images with consistent dimensions
        """
        if not images:
            return images

        # Determine target size
        if self.target_width and self.target_height:
            target_size = (self.target_width, self.target_height)
        else:
            target_size = images[0].size

        # Ensure dimensions don't exceed maximum
        width, height = target_size
        if width > self.MAX_DIMENSION or height > self.MAX_DIMENSION:
            scale = min(self.MAX_DIMENSION / width, self.MAX_DIMENSION / height)
            target_size = (int(width * scale), int(height * scale))

        # Resize images that don't match target
        normalized = []
        for img in images:
            if img.size != target_size:
                resized = img.resize(target_size, Image.Resampling.LANCZOS)
                normalized.append(resized)
            else:
                normalized.append(img)

        return normalized

    def _optimize_image(self, image: Image.Image) -> bytes:
        """Optimize image for smaller file size using JPEG compression.

        Args:
            image: PIL Image object

        Returns:
            Optimized JPEG image as bytes
        """
        # Convert RGBA/P to RGB (JPEG doesn't support alpha)
        if image.mode in ("RGBA", "P"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "RGBA":
                background.paste(image, mask=image.split()[3])
            else:
                background.paste(image)
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # Save as optimized JPEG
        buffer = io.BytesIO()
        image.save(
            buffer,
            format="JPEG",
            quality=self.JPEG_QUALITY,
            optimize=True,
        )
        return buffer.getvalue()

    def _image_to_png_bytes(self, image: Image.Image) -> bytes:
        """Convert image to PNG bytes (no optimization).

        Args:
            image: PIL Image object

        Returns:
            PNG image as bytes
        """
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def build(self, screenshots: list[bytes]) -> bytes:
        """Convert list of screenshots to PDF.

        Args:
            screenshots: List of PNG image bytes

        Returns:
            PDF file as bytes

        Raises:
            PDFBuildError: If PDF generation fails
        """
        if not screenshots:
            raise PDFBuildError("No screenshots provided")

        try:
            # Load all images
            images = [self._load_image(s) for s in screenshots]

            # Normalize to consistent dimensions
            images = self._normalize_dimensions(images)

            # Prepare images for PDF (optimize or keep as PNG)
            if self.optimize:
                image_bytes_list = [self._optimize_image(img) for img in images]
            else:
                image_bytes_list = [self._image_to_png_bytes(img) for img in images]

            # Build PDF using img2pdf
            pdf_bytes = img2pdf.convert(image_bytes_list)

            return pdf_bytes

        except PDFBuildError:
            raise
        except Exception as e:
            raise PDFBuildError(str(e))

    def build_from_files(self, file_paths: list[str]) -> bytes:
        """Build PDF from image file paths.

        Args:
            file_paths: List of paths to image files

        Returns:
            PDF file as bytes

        Raises:
            PDFBuildError: If PDF generation fails
        """
        try:
            screenshots = []
            for path in file_paths:
                with open(path, "rb") as f:
                    screenshots.append(f.read())
            return self.build(screenshots)
        except PDFBuildError:
            raise
        except Exception as e:
            raise PDFBuildError(str(e))
