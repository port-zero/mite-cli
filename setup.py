from setuptools import setup

setup(
    name='mite-cli',
    version='0.1',
    py_modules=['mite_cli'],
    include_package_data=True,
    install_requires=[
        'click',
        'mite',
        'pyyaml',
    ],
    entry_points='''
        [console_scripts]
        mite=mite_cli:cli
    ''',
)
