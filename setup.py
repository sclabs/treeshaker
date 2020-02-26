from setuptools import setup, find_packages

from treeshaker._version import version_scheme, local_scheme

with open('README.md') as fobj:
    long_description = fobj.read()


setup(
    name='treeshaker',
    use_scm_version={
        'version_scheme': version_scheme,
        'local_scheme': local_scheme,
    },
    description='A tree-shaking tool for Python.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/sclabs/treeshaker',
    author='Thomas Gilgenast',
    author_email='thomasgilgenast@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Archiving :: Packaging',
        'Topic :: System :: Software Distribution'
    ],
    keywords='tree-shaking',
    packages=find_packages(),
    include_package_data=True,
    setup_requires=['setuptools_scm'],
    install_requires=[
        'configparser>=4.0.2;python_version<"3.2"',
        'enum34>=1.1.9;python_version<"3.4"',
        'fire>=0.2.1',
        'importlib_metadata>=1.5.0;python_version<"3.8"',
        'modulegraph>=0.18',
        'pip-tools>=4.5.0',
        'requirements-parser>=0.2.0',
        'six>=1.14.0',
    ],
    entry_points={
        'console_scripts': [
            'treeshaker=treeshaker.treeshaker:main',
        ],
    },
)
