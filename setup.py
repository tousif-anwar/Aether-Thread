"""
Setup configuration for Aether-Thread.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aether-thread",
    version="0.1.0",
    author="Tousif Anwar",
    author_email="tousif@example.com",
    description="Concurrency-optimization toolkit for Python GIL-free transition",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tousif-anwar/Aether-Thread",
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "aether-audit=aether_thread.audit.cli:main",
            "aether-bench=aether_thread.bench.cli:main",
        ],
    },
)
