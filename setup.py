from setuptools import setup, find_packages

setup(
    name="fifa_scraper",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4',
        'selenium',
        'pandas',
        'webdriver-manager',
        'ratelimit'
    ]
)