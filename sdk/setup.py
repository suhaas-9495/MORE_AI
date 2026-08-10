from setuptools import setup, find_packages

setup(
    name="moreai-sdk",
    version="0.1.0",
    description="Python SDK for the MoreAI Multi-Agent SDLC Platform",
    author="Suhaas",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.24.0",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)