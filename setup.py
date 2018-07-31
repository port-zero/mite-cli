from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='mite-cli',
    author='Veit Heller',
    version='0.1.0',
    license='MIT',
    url='https://github.com/port-zero/mite-cli',
    downloadurl='https://github.com/port-zero/mite-cli/tarball/0.1.0',
    description='A mite client for the command line',
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=['mite_cli'],
    include_package_data=True,
    install_requires=[
        'click',
        'mite',
        'pyyaml',
    ],
    entry_points="""
        [console_scripts]
        mite=mite_cli:cli
    """,
)
