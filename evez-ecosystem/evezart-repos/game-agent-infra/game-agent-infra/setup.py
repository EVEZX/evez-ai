from setuptools import setup, find_packages

setup(
    name="game-agent-infra",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0",
        "opentelemetry-api>=1.24",
        "opentelemetry-sdk>=1.24",
    ],
    entry_points={
        "console_scripts": [
            "game-agent-infra = cli:main",
        ]
    },
    description="Wheel-rooted, FSC-measured, retrocausal-safe cognitive infrastructure for EVEZ agents",
    author="KiloClaw (autonomous)",
)