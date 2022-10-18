from setuptools import find_packages, setup

setup(
    name='solc-json-parser',
    packages=find_packages(include=['solc_json_parser']),
    version='0.1.0',
    description='AST parser from solc json file',
    author='SBIP',
    license='MIT',
    install_requires=['addict>=2.4.0',
                      'py_solc_x>=1.1.1',
                      'semantic_version>=2.9.0',
                      'utils>=1.0.1'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest>-4.4.1'],
    test_suite='tests',    
)
