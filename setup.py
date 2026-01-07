from setuptools import setup, find_packages

setup(
    name="topdf",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "playwright>=1.40.0",
        "Pillow>=10.0.0",
        "img2pdf>=0.5.0",
        "pytesseract>=0.3.10",
        "click>=8.1.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "topdf=topdf.cli:topdf",
        ],
    },
    python_requires=">=3.9",
    author="Aakash",
    description="Convert DocSend links to PDF files locally",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
