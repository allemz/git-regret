from setuptools import setup, find_packages

setup(
    name="git-regret",
    version="0.1.0",
    description="Repo geçmişindeki secret'ları bul ve temizle.",
    author="git-regret contributors",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "click>=8.0",
        "gitpython>=3.1",
        "rich>=13.0",
        "questionary>=2.0",
    ],
    extras_require={
        "dev": ["pytest", "pytest-cov"],
    },
    entry_points={
        "console_scripts": [
            "git-regret=git_regret.cli:main",
            "git-regret-ui=git_regret.tui:run",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Security",
        "Topic :: Software Development :: Version Control :: Git",
    ],
)
