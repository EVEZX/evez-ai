from setuptools import setup, find_packages

setup(
    name="criticalmind",
    version="1.0.0",
    description="Consciousness-guided autonomous agent system",
    author="Steven Crawford-Maggard (EVEZ)",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "playwright>=1.40.0",
    ],
    extras_require={
        "full": [
            "selenium>=4.15.0",
            "pyautogui>=0.9.54",
            "Appium-Python-Client>=3.1.0",
            "plotly>=5.18.0",
            "streamlit>=1.29.0",
            "qiskit>=0.45.0",
        ]
    },
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "criticalmind=src.demo_quick:main",
        ],
    },
)
