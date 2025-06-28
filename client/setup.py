from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="glyph-media",
    version="0.1.1",
    author="pizzalover125",
    description="A terminal-based social media service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pizzalover125/glyph",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "rich>=13.0.0",
        "questionary>=1.10.0", 
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "glyph=glyph_media.cli:main",
        ],
    },
)