"""
Package setup configuration.
"""
from pathlib import Path
from setuptools import setup, find_packages

# Read requirements
requirements = []
with open("requirements.txt") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            requirements.append(line)

# Read README
readme = Path("README.md").read_text()

setup(
    name="vhs_processor",
    version="0.1.0",
    description="VHS tape processing and identification tool",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/vhs-processor",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vhs-process=src.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    zip_safe=False,
)
