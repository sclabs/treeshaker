from __future__ import absolute_import

import os
import shlex
import shutil
import subprocess

import fire
import requirements
from modulegraph.modulegraph import MissingModule
from modulegraph.find_modules import find_modules
from piptools.scripts.compile import cli as pip_compile

from treeshaker import __version__
from treeshaker.config import load_config
from treeshaker.doc_utils import document_component, document_function
from treeshaker.pypi_names import convert_from_pypi
from treeshaker.setup_utils import write_setup_py


def load_requirements_txt(fname='requirements.txt'):
    with open(fname, 'r') as handle:
        all_lines = handle.readlines()
    header_lines = [
        line.strip()
        for line in [l for l in all_lines if l.startswith('--')]
    ]
    req_lines = [l for l in all_lines if not l.startswith('--')]
    return header_lines, list(requirements.parse(''.join(req_lines)))


def module_is_nonempty(module):
    return bool([x for x in module.globalnames if not x.startswith('_')])


def resolve_names(old_names):
    split_names = [n.split('.') for n in old_names]
    finals = [split_name[-1] for split_name in split_names]

    # short circuite if finals are all unique
    if len(finals) == len(set(finals)):
        return finals

    # create a map from unique finals to their indices
    dup_map = {f: [] for f in set(finals)}
    for i, f in enumerate(finals):
        dup_map[f].append(i)

    # create a map from old names to new, deduplicated names
    dedup_map = {}
    for f, idx in dup_map.items():
        if len(idx) == 1:
            # item is unique, add it to map unmodified
            dedup_map[old_names[idx[0]]] = f
        else:
            # item is not unique, construct alternatives
            for i in idx:
                dedup_map[old_names[i]] = '%s_%s' % (f, split_names[i][-2])

    return [dedup_map[n] for n in old_names]


def resolve_function_name(ref, target_module_name, old_name_to_new_name):
    if '.' in ref:
        module_name, component_name = ref.rsplit('.', 1)
    else:
        module_name = target_module_name
        component_name = ref
    new_name = old_name_to_new_name[module_name]
    return module_name, component_name, new_name


def process_module(target_module_name, target_packages, dest_dir,
                   requirements_file='requirements.txt', add_init_py=False,
                   add_setup_py=False, package_data=(), source_paths=(),
                   readme=None, functions=(), fire_components=(),
                   post_build_commands=(), verbose=False):
    # determine package name
    pkg_name = os.path.split(dest_dir)[1]

    # parse root requirements.txt
    header_lines, all_reqs = load_requirements_txt(fname=requirements_file)
    print('parsed %i requirements from requirements.txt' % len(all_reqs))

    # run modulegraph to get modules
    print('constructing module import graph')
    mg = find_modules(
        includes=(target_module_name,),
        excludes=set(r.name for r in all_reqs)-set(target_packages)
    )
    print('found %i nodes in the module import graph' % len(list(mg.flatten())))

    # analyze the graph
    target_node = mg.findNode(target_module_name)
    if target_node is None or isinstance(target_node, MissingModule):
        raise ImportError('could not import target module %s'
                          % target_module_name)
    visited = set()
    our_mods = {target_node}
    external_mods = set()
    external_reqs = set()
    stack = [target_node]
    while stack:
        current_node = stack.pop()
        refs = list(mg.getReferences(current_node))
        for ref in refs:
            if ref.identifier in visited:
                continue
            visited.add(ref.identifier)
            if any(x in ref.identifier for x in target_packages):
                if module_is_nonempty(ref):
                    our_mods.add(ref)
                    stack.append(ref)
                continue
            for req in all_reqs:
                if convert_from_pypi(req.name) in ref.identifier:
                    external_mods.add(ref)
                    external_reqs.add(req)
                    break
    print('found %i modules imported from target packages'
          % len(our_mods))
    print('found %i modules imported from %i external requirements'
          % (len(external_mods), len(external_reqs)))
    if verbose:
        for m in sorted(external_mods):
            print(m.identifier)

    # fill in new names and new paths
    old_names = [x.identifier for x in our_mods]
    new_names = resolve_names(old_names)
    old_name_to_new_name = {}
    old_name_to_new_path = {}
    for old_name, new_name in zip(old_names, new_names):
        old_name_to_new_name[old_name] = new_name
        old_name_to_new_path[old_name] = \
            os.path.join(dest_dir, pkg_name, new_name + '.py') \
            if add_setup_py else os.path.join(dest_dir, new_name + '.py')

    # make dest_dir
    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)
    if add_setup_py and not os.path.exists(os.path.join(dest_dir, pkg_name)):
        os.mkdir(os.path.join(dest_dir, pkg_name))

    # touch __init__.py
    if add_init_py:
        if add_setup_py:
            print('both add_init_py and add_setup_py are set to True')
            print('__init__.py will be written, but only once '
                  '(inside the package folder)')
        else:
            open(os.path.join(dest_dir, '__init__.py'), 'w').close()
    if add_setup_py:
        open(os.path.join(dest_dir, pkg_name, '__init__.py'), 'w').close()

    # copy modules, rewriting imports
    for m in our_mods:
        with open(m.filename, 'r') as handle:
            data = handle.read()
        for other in our_mods:
            data = data.replace(
                other.identifier,
                '.' + old_name_to_new_name[other.identifier])
        with open(old_name_to_new_path[m.identifier], 'w') as handle:
            handle.write(data)

    # handle package_data
    for f in package_data:
        package_name, f_path = f.split('/', 1)
        package_path = mg.findNode(package_name).packagepath[0]
        complete_path = os.path.join(package_path, f_path)
        shutil.copy(complete_path, dest_dir)

    # write requirements.in
    req_in_fname = os.path.join(dest_dir, 'requirements.in')
    with open(req_in_fname, 'w') as handle:
        handle.write('\n'.join(header_lines +
                               list(sorted([e.line for e in external_reqs]))))
        handle.write('\n')

    # handle source_paths
    find_links = []
    for source_path in source_paths:
        print('building sdist for %s' % source_path)
        cmd = 'python setup.py --quiet sdist'
        subprocess.Popen(shlex.split(cmd), cwd=source_path).wait()
        # backslash pathsep breaks pip_comple() in py2
        find_link = os.path.join(source_path, 'dist').replace('\\', '/')
        assert os.path.exists(find_link)
        find_links.append(find_link)

    # compile requirements.txt
    print('writing requirements.txt')
    req_txt_fname = os.path.join(dest_dir, 'requirements.txt')
    pip_compile_args = [req_in_fname, '--output-file', req_txt_fname,
                        '--no-header', '--no-annotate']
    for f in find_links:
        pip_compile_args.extend(['--find-links', f])
    if not verbose:
        pip_compile_args.append('--quiet')
    print('compiling requirements: %s %s' %
          ('pip-compile', ' '.join(pip_compile_args)))
    pip_compile(args=pip_compile_args, standalone_mode=False)
    os.remove(req_in_fname)

    # load readme content
    readme_content = None
    if readme and os.path.exists(readme):
        with open(readme, 'r') as handle:
            readme_content = handle.read()

    # write README
    if readme_content or fire_components or functions:
        new_name = old_name_to_new_name[target_module_name]
        with open(os.path.join(dest_dir, 'README.md'), 'w') as handle:
            handle.write('%s\n' % dest_dir)
            handle.write(('=' * len(dest_dir)) + '\n\n')
            if readme_content:
                handle.write(readme_content + '\n')
            if fire_components:
                handle.write('Command line tools\n')
                handle.write('------------------\n\n')
            for f in fire_components:
                document_component(handle, *resolve_function_name(
                    f, target_module_name, old_name_to_new_name))
            if fire_components and functions:
                handle.write('\n')
            if functions:
                handle.write('Python API\n')
                handle.write('----------\n\n')
            for f in functions:
                document_function(handle, *resolve_function_name(
                    f, target_module_name, old_name_to_new_name),
                    pkg_name=pkg_name if add_setup_py else None)

    # write setup.py
    if add_setup_py:
        print('writing setup.py')
        write_setup_py(dest_dir, pkg_name, external_reqs)

    # post build commands
    for cmd in post_build_commands:
        print('running post_build_command: %s' % cmd)
        subprocess.Popen(shlex.split(cmd), cwd=dest_dir, shell=True).wait()


def run_from_config(target=None, config='treeshaker.cfg', version=False):
    # short circuit for version
    if version:
        print('treeshaker version %s' % __version__)
        return

    # load config
    if not os.path.exists(config):
        raise IOError('could not find config file %s' % config)
    config_path = os.path.dirname(config)
    config = load_config(fname=config)

    # resolve targets
    if target is None:
        targets = list(config['targets'].keys())
    else:
        targets = [target]

    # process targets
    for target in targets:
        section = config['target:%s' % target]
        process_module(
            target,
            section['target_packages'],
            section['outdir'],
            requirements_file=os.path.join(
                config_path, section['requirements_file']),
            add_init_py=section['add_init_py'],
            add_setup_py=section['add_setup_py'],
            package_data=section['package_data']
            if section['package_data'] else (),
            source_paths=[os.path.join(config_path, p)
                          for p in section['source_paths']]
            if section['source_paths'] else (),
            post_build_commands=section['post_build_commands']
            if section['post_build_commands'] else (),
            readme=os.path.join(config_path, section['readme']),
            functions=section['functions']
            if section['functions'] else (),
            fire_components=section['fire_components']
            if section['fire_components'] else (),
        )


def main():
    fire.Fire(run_from_config)


if __name__ == '__main__':
    main()
