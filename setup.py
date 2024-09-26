"""
Setup script for scholarhub_search
"""
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sch-search", # Replace with your own username
    version="0.0.1",
    author="Scholarhub, Inc.",
    author_email="scholarhub.contact@gmail.com",
    description="Scholarhub ai",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
)
