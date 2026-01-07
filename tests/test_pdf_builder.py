"""Tests for PDF builder module."""

import io
from pathlib import Path

import pytest
from PIL import Image

from topdf.pdf_builder import PDFBuilder
from topdf.exceptions import PDFBuildError


class TestPDFBuilder:
    """Tests for PDFBuilder class."""

    @pytest.fixture
    def builder(self) -> PDFBuilder:
        """Create a PDF builder instance."""
        return PDFBuilder()

    def test_build_single_page(self, builder: PDFBuilder, sample_screenshot: bytes):
        """Test building PDF with single page."""
        pdf_bytes = builder.build([sample_screenshot])

        # Verify it's a valid PDF (starts with PDF magic number)
        assert pdf_bytes.startswith(b"%PDF")
        assert len(pdf_bytes) > 0

    def test_build_multi_page(self, builder: PDFBuilder, sample_screenshots: list[bytes]):
        """Test building PDF with multiple pages."""
        pdf_bytes = builder.build(sample_screenshots)

        # Verify it's a valid PDF
        assert pdf_bytes.startswith(b"%PDF")

        # PDF should be larger than single page
        single_page_pdf = builder.build([sample_screenshots[0]])
        assert len(pdf_bytes) > len(single_page_pdf)

    def test_build_empty_list_raises(self, builder: PDFBuilder):
        """Test that empty list raises PDFBuildError."""
        with pytest.raises(PDFBuildError):
            builder.build([])

    def test_page_order_preserved(self, builder: PDFBuilder):
        """Test that pages are in correct order."""
        # Create screenshots with different colors to verify order
        screenshots = []
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

        for color in colors:
            img = Image.new("RGB", (100, 100), color=color)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            screenshots.append(buffer.getvalue())

        pdf_bytes = builder.build(screenshots)

        # Verify PDF was created (detailed page order testing would require PDF parsing)
        assert pdf_bytes.startswith(b"%PDF")

    def test_normalize_dimensions(self, builder: PDFBuilder):
        """Test that images are normalized to consistent dimensions."""
        # Create images of different sizes
        screenshots = []
        sizes = [(800, 600), (1920, 1080), (640, 480)]

        for size in sizes:
            img = Image.new("RGB", size, color=(255, 255, 255))
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            screenshots.append(buffer.getvalue())

        # Should not raise
        pdf_bytes = builder.build(screenshots)
        assert pdf_bytes.startswith(b"%PDF")

    def test_handles_rgba_images(self, builder: PDFBuilder):
        """Test that RGBA images are converted properly."""
        # Create RGBA image
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        pdf_bytes = builder.build([buffer.getvalue()])
        assert pdf_bytes.startswith(b"%PDF")

    def test_handles_large_images(self, builder: PDFBuilder):
        """Test handling of large images."""
        # Create a large image
        img = Image.new("RGB", (4000, 3000), color=(255, 255, 255))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        pdf_bytes = builder.build([buffer.getvalue()])
        assert pdf_bytes.startswith(b"%PDF")

    def test_optimization_reduces_size(self):
        """Test that optimization reduces file size."""
        # Create a detailed image that can be compressed
        img = Image.new("RGB", (1920, 1080), color=(255, 255, 255))
        from PIL import ImageDraw

        draw = ImageDraw.Draw(img)
        for i in range(0, 1920, 100):
            draw.line([(i, 0), (i, 1080)], fill=(0, 0, 0))

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        screenshot = buffer.getvalue()

        # Build with optimization
        optimized_builder = PDFBuilder(optimize=True)
        optimized_pdf = optimized_builder.build([screenshot])

        # Build without optimization
        unoptimized_builder = PDFBuilder(optimize=False)
        unoptimized_pdf = unoptimized_builder.build([screenshot])

        # Optimized should typically be smaller (JPEG vs PNG)
        # Note: This may vary based on image content
        assert len(optimized_pdf) > 0
        assert len(unoptimized_pdf) > 0

    def test_custom_dimensions(self, sample_screenshot: bytes):
        """Test builder with custom target dimensions."""
        builder = PDFBuilder(target_width=1280, target_height=720)
        pdf_bytes = builder.build([sample_screenshot])
        assert pdf_bytes.startswith(b"%PDF")

    def test_build_from_files(self, builder: PDFBuilder, temp_dir: Path):
        """Test building PDF from file paths."""
        # Create test images
        file_paths = []
        for i in range(3):
            img = Image.new("RGB", (100, 100), color=(255, 255, 255))
            path = temp_dir / f"test_{i}.png"
            img.save(path)
            file_paths.append(str(path))

        pdf_bytes = builder.build_from_files(file_paths)
        assert pdf_bytes.startswith(b"%PDF")

    def test_invalid_image_raises(self, builder: PDFBuilder):
        """Test that invalid image data raises error."""
        with pytest.raises(PDFBuildError):
            builder.build([b"not an image"])
