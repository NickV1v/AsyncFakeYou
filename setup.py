from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="asyncfakeyou",
    version="0.1.1",
    description="An asynchronous library for interacting with the FakeYou Text-to-Speech API.",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NickV1v/AsyncFakeYou",
    author="NickV1v",
    author_email="vivchar.nikita@yandex.ru",
    license="MIT",
    classifiers=[
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=[
        "aiohttp>=3.10.3",
        "aiofiles>=24.1.0"
    ],
    extras_require={
        "dev": ["twine>=5.1.1"],
    },
    python_requires=">=3.10",
)
