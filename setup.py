from setuptools import setup, find_packages

setup(
    name='band',
    version='0.1',
    author='Dmitry Rodin',
    author_email='madiedinro@gmail.com',
    license='MIT',
    description='Python microservices for Rockstat analytics plaform',
    long_description="""
About
---
Orchestranion module start services in docker containers, examine and send configuraton to the frontier service.
Includes microserivice framework for easy develop simple services and easy expose by https through frontier.
More at project documentation
    """,
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    url='https://github.com/rockstat',
    include_package_data=True,
    install_requires=[
        'pyyaml', 'inflection', 'jinja2', 'coloredlogs',
        'asyncio', 'uvloop', 'aiohttp', 'aioredis',
        'aiojobs', 'aiodocker', 'aiofiles',
        'jsonrpcserver', 'jsonrpcclient', 'requests',
        'python-dotenv',
        'prodict', 'ujson'
    ],
    dependency_links=[
        'git+https://github.com/bcb/jsonrpcclient.git@master#egg=jsonrpcclient'
    ],
    # extras_require={
    #     'dev': ['check-manifest'],
    #     'test': ['coverage'],
    # },
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    project_urls={  # Optional
        'Homepage': 'https://rockstat.ru',
        'Docs': 'https://rockstat.ru/docs'
    }
)
