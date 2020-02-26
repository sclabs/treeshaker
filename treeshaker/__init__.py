from __future__ import absolute_import


try:
    try:
        # this works in Python 3.8
        from importlib.metadata import version, PackageNotFoundError
    except ImportError:
        try:
            # this works in Python 2 if lib5c is installed, since it depends on
            # importlib_metadata
            from importlib_metadata import version, PackageNotFoundError
        except ImportError:
            raise
    try:
        # we land here if either importlib.metadata or importlib_metadata
        # is available and lib5c is installed
        __version__ = version(__name__)
    except PackageNotFoundError:
        # we will land here if either importlib.metadata or importlib_metadata
        # is available, but lib5c isn't actually installed
        __version__ = 'unknown'
except ImportError:
    # we land here if neither importlib.metadata nor importlib_metadata are
    # available
    __version__ = 'unknown'
