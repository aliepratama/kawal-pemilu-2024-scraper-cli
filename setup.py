"""Kawal Pemilu 2024 Scraper - Download and extract C1 Plano election forms."""

from setuptools import setup, find_packages

# Read requirements from files
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="kawal-pemilu-scraper",
    version="2.0.0",
    author="Ali Epratama",
    description="CLI tool for downloading and extracting vote numbers from Kawal Pemilu 2024",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aliepratama/kawal-pemilu-2024-scraper-cli",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    python_requires=">=3.9",
    
    # Core dependencies - always installed
    install_requires=[
        "scrapy>=2.8.0",
        "questionary>=1.10.0",
        "tqdm>=4.65.0",
        "playwright>=1.40.0",
    ],
    
    # Optional dependencies groups
    extras_require={
        # For digit extraction features (auto-cropping)
        "extraction": [
            "ultralytics>=8.0.0",
            "opencv-python>=4.8.0",
            "numpy>=1.24.0",
            "torch>=2.0.0",  # Required by ultralytics
        ],
        
        # For development
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        
        # All features
        "all": [
            "ultralytics>=8.0.0",
            "opencv-python>=4.8.0",
            "numpy>=1.24.0",
            "torch>=2.0.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    
    # Entry points for CLI commands
    entry_points={
        "console_scripts": [
            "kawal-pemilu=cli:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
