"""
Setup configuration for Aether-Thread.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aether-thread",
    version="0.2.0",
    author="Tousif Anwar",
    author_email="tousif@example.com",
    description="Modern thread-safe Python for the no-GIL era: @atomic decorators, contention monitoring, and more",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tousif-anwar/Aether-Thread",
    package_dir={"": "src"},
    packages=find_packages(where="src", exclude=["tests", "examples", "docs"]),
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
        "Topic :: System :: Threading",
    ],
    python_requires=">=3.9",
)
