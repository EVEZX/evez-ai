from setuptools import setup, find_packages

setup(
    name="evez-spine",
    version="1.1.0",
    description="Unified append-only hash-chained event log for the EVEZ ecosystem",
    author="EvezArt",
    author_email="evezart@users.noreply.github.com",
    url="https://github.com/EvezArt/evez-spine",
    py_modules=["spine"],
    python_requires=">=3.8",
    install_requires=["numpy>=1.24.0"],
    license="AGPL-3.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Logging",
    ],
)
