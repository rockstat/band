__VERSION__ = '0.20.6'

from setuptools import setup, find_packages

setup(
    name='band',
    version='0.20.6',
    author='Dmitry Rodin',
    author_email='madiedinro@gmail.com',
    license='MIT',
    description='Python microservices for Rockstat analytics plaform',
    long_description="""
About
---
Orchestranion module start services in docker containers, examine and send configuraton to the front service.
Includes microserivice framework for easy develop simple services and easy expose by https through front.
More at project documentation
    """,
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    url='https://github.com/rockstat/band-framework',
    include_package_data=True,
    install_requires=[
        'pyyaml>=4.2b1', 'inflection', 'jinja2', 'python-dotenv',
        'structlog', 'colorama', 'python-json-logger', 'coloredlogs',
        'cryptography', 'base58', 'xxhash',
        'asyncio', 'uvloop', 'async_lru', 'aioconsole',
        'aiohttp<4', 'aioredis', 'aiojobs', 'aiocache',
        'aiofiles', 'aiocron>=1.3,<2', 'yarl',
        'simplech>=0.16',
        'jsonrpcserver==3.5.6', 'jsonrpcclient==2.6.0', 
        'requests', # for jsonrpc client
        'prodict', 'pydantic', 'ujson', 'arrow'
    ],
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    project_urls={  # Optional
        'Homepage': 'https://rock.st',
        'Docs': 'https://rock.st/docs'
    })
