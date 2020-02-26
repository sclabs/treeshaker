"""
Module for managing version naming scheme and supplying version information.

The version naming scheme is specified by defining functions version_scheme()
and local_scheme(). We have written these so that they mimic versioneer's
"pep440" style. These functions are used in this module, and they are also
imported in ``setup.py`` at install time.

When treeshaker is installed, its version can be accessed as
``treeshaker.__version__``. This is the version printed when ``treeshaker -v``
is run on the command line. This is the recommended way to get version
information.
"""
from __future__ import absolute_import


def version_scheme(version):
    return str(version.tag)


def local_scheme(version):
    if version.distance is None:
        return ''
    return '+%s.%s%s' % (version.distance, version.node,
                         '.dirty' if version.dirty else '')
