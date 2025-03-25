from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="blockExplorer",
    version="0.1.9",
    author="Mmdrza",
    author_email="pymmdrza@gmail.com",
    description="A professional blockchain explorer web application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Pymmdrza/pyExplorer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "asyncio>=3.4.3",
        "flask>=3.1.0",
        "pandas>=2.2.3",
        "plotly>=6.0.0",
        "python-dotenv>=1.0.1",
        "requests>=2.32.3",
        "weasyprint>=64.1",
        "websockets>=13.1",
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'blockExplorer=blockExplorer.cli:main',
        ],
    },
)