import os


TEMPLATE = """
import os
from setuptools import setup, find_packages

if os.path.exists('README.md'):
    with open('README.md') as fobj:
        long_description = fobj.read()
else:
    long_description='<name>'

setup(
    name='<name>',
    version='0.0.0',
    description='<name>',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
<install_requires>
    ],
)
"""


def format_requirements(reqs):
    return ',\n'.join('        \'%s\'' % r.line.replace('==', '>=')
                      for r in reqs)


def write_setup_py(dest_dir, name, reqs):
    content = TEMPLATE.replace('<name>', name)\
        .replace('<install_requires>', format_requirements(reqs))
    with open(os.path.join(dest_dir, 'setup.py'), 'w') as handle:
        handle.write(content)
