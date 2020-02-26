from __future__ import absolute_import

import six
from configparser import ConfigParser, SectionProxy, NoOptionError


class CustomSectionProxy(SectionProxy):
    def __getitem__(self, key):
        # support for default outdir, parser[][]-style
        if key == 'outdir' and not self._parser.has_option(self._name, key) \
                and ':' in self._name:
            return self._name.rsplit(':', 1)[1].split('.')[-1]

        # support for inheriting default values from parent sections
        # parser[][]-style, inner __getitem__()
        if not self._parser.has_option(self._name, key):
            if ':' in self._name:
                return self._parser.get(self._name.rsplit(':', 1)[0], key,
                                        original_section=self._name)
            return None
        return self._parser.get(self._name, key)


class CustomConfigParser(ConfigParser):
    def __getitem__(self, key):
        # support for inheriting default values from parent sections
        # parser[][]-style, outer __getitem__()
        # (ensure the second __getitem__ is called on CustomSectionProxy)
        original_proxy = super(CustomConfigParser, self).__getitem__(key)
        return CustomSectionProxy(original_proxy._parser, original_proxy._name)

    def get(self, section, option, **kwargs):
        # support for default outdir, parser.get()-style
        if option == 'outdir' and not self.has_option(section, option) \
                and ':' in section:
            return section.rsplit(':', 1)[1].split('.')[-1]

        # support for inheriting default values from parent sections
        # parser.get()-style
        if not self.has_option(section, option):
            if ':' in section:
                kwargs['original_section'] = section
                return self.get(section.rsplit(':', 1)[0], option, **kwargs)

        # the superclass's implementation of get() does not allow arbitrary
        # kwargs in Python 3, so we "hide" that value here
        original_section = None
        if 'original_section' in kwargs:
            original_section = kwargs['original_section']
            del kwargs['original_section']

        # call superclass's implementation
        try:
            value = super(CustomConfigParser, self)\
                .get(section, option, **kwargs)
        except (KeyError, NoOptionError):
            return None

        # support for interpolating <outdir>
        if '<outdir>' in value:
            # within a child section
            if ':' in section:
                outdir = self.get(section, 'outdir', **kwargs)
            # in a parent section
            elif original_section is not None:
                outdir = self.get(original_section, 'outdir', **kwargs)
            # neither?
            else:
                outdir = '<outdir>'
            value = value.replace('<outdir>', outdir)

        # support for lists
        if '\n' in value:
            value = value.strip('\n').split('\n')

        # support for boolean
        if isinstance(value, six.text_type):
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False

        return value


def load_config(fname='treeshaker.cfg'):
    """
    Loads a treeshaker config file.

    Uses the CustomConfigParser implementation in this module to provide extra
    features.

    Parameters
    ----------
    fname : str
        The path to the config file to load.

    Returns
    -------
    CustomConfigParser
        The loaded config file.

    Examples
    --------
    >>> from treeshaker.config import load_config
    >>> config = load_config('examples/treeshaker.cfg')
    >>> config['target']['requirements_file']  # basic access
    'requirements.txt'
    >>> list(config['targets'].keys())  # allow_no_value
    ['mypkg.target']
    >>> config['target']['functions'] is None  # None when key doesn't exist
    True
    >>> config['target:mypkg.target']['fire_components'] is None  # ditto
    True
    >>> config['target']['add_init_py']  # bool conversion
    True
    >>> config['target']['target_packages']  # list conversion
    ['mypkg', 'otherpkg']
    >>> config['target:mypkg.target']['target_packages']  # inheritance
    ['mypkg', 'otherpkg']
    >>> config['target:mypkg.target']['post_build_commands']  # interp
    ['ls', 'echo "built output in build_target/"']
    >>> config['target:mypkg.target']['readme']  # inheritance + interp
    'build_target.md'
    """
    config = CustomConfigParser(allow_no_value=True)
    config.read(fname)
    return config
