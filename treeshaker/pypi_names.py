from __future__ import absolute_import


with open(__file__.replace('.pyc', '.txt').replace('.py', '.txt'), 'r') as f:
    data = dict(x.strip().replace('-', '_').split(':')[::-1] for x in f)


def convert_from_pypi(pypi_name):
    """
    Converts a PyPI name (as found in requirements.txt) to the actual name of
    the module.

    This function uses the mapping from
    https://github.com/bndr/pipreqs/blob/master/pipreqs/mapping, which should
    exist as ``pypi_names.txt`` next to this file.

    To maximize consistency, we convert all dashes to underscores, both when
    loading the mapping and also when resolving the name. The returned name
    should be a valid Python identifier and therefore should not contain dashes
    anyway.

    Parameters
    ----------
    pypi_name : str
        The PyPI name of the package.

    Examples
    --------
    >>> from treeshaker.pypi_names import convert_from_pypi
    >>> convert_from_pypi('scikit-learn')
    'sklearn'
    >>> convert_from_pypi('requirements-parser')
    'requirements'
    >>> convert_from_pypi('numpy')
    'numpy'
    """
    pypi_name = pypi_name.replace('-', '_')
    return data.get(pypi_name, pypi_name)
