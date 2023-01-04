from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='solc-json-parser',
    packages=find_packages(include=['solc_json_parser']),
    version='0.1.5',
    description='AST parser from solc json file',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='SBIP',
    license='MIT',
    install_requires=['addict>=2.4.0',
                      'py_solc_x>=1.1.1',
                      'semantic_version>=2.9.0',
                      'pycryptodome>=3.16.0',
                      'utils>=1.0.1'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest>-4.4.1'],
    test_suite='tests',
)
