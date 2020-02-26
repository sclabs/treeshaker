from __future__ import absolute_import

import pydoc
import re
from importlib import import_module

import fire


ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def document_function(handle, module_name, function_name, new_name):
    module = import_module(module_name)
    function = getattr(module, function_name)
    handle.write('### %s.%s()\n\n' % (new_name, function_name))
    handle.write('```\n')
    handle.write('import %s\n' % new_name)
    handle.write('help(%s.%s)\n' % (new_name, function_name))
    handle.write(pydoc.plain(pydoc.TextDoc().docroutine(function)))
    handle.write('```\n')


def document_component(handle, module_name, component_name, new_name):
    module = import_module(module_name)
    component = getattr(module, component_name)
    handle.write('### %s.py\n\n' % new_name)
    handle.write('```\n')
    handle.write(ansi_escape.sub(
        '',
        fire.helptext.HelpText(
            component,
            trace=fire.trace.FireTrace(component, new_name + '.py')
        )
    ))
    handle.write('\n```\n')
