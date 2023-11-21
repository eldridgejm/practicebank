from setuptools import setup, find_packages

setup(
    name="practicebank",
    version="0.1.5",
    packages=find_packages(),
    install_requires=["panprob", "dictconfig", "rich"],
    entry_points={
        "console_scripts": [
            "practicebank = practicebank.__main__:main",
        ]
    }
)
