from setuptools import setup

setup(
    name="snowflake_manager",
    version="0.0.1",
    packages=["snowflake_manager"],
    install_requires=[
        "pyyaml",
        "snowflake-connector-python",
        "python-dotenv",
        "rich",
    ],
    entry_points={
        "console_scripts": ["snowflake_manager=snowflake_manager.main:main"],
    },
)
