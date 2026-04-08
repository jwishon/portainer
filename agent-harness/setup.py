"""Setup for cli-anything-portainer."""

from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-portainer",
    version="0.1.0",
    description="CLI harness for Portainer container management platform",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=[
        "click>=8.0",
        "requests>=2.28",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-mock>=3.0",
            "responses>=0.23",
        ]
    },
    entry_points={
        "console_scripts": [
            "cli-anything-portainer=cli_anything.portainer.portainer_cli:main",
        ],
    },
    python_requires=">=3.9",
)
