import os
import shutil

from treeshaker.config import load_config


def main():
    # load config
    config_path = os.path.dirname(__file__)
    config = load_config(os.path.join(config_path, 'treeshaker.cfg'))

    for target in config['targets']:
        section = config['target:%s' % target]
        # clean outdir
        outdir = section['outdir']
        if os.path.exists(outdir):
            shutil.rmtree(outdir)

        # clean any artifacts built by source_paths
        source_paths = [os.path.join(config_path, p)
                        for p in section['source_paths']] \
            if section['source_paths'] else ()
        for source_path in source_paths:
            dist_dir = os.path.join(source_path, 'dist')
            if os.path.exists(dist_dir):
                shutil.rmtree(dist_dir)
            egg_info = '%s.egg-info' % os.path.basename(source_path)
            egg_path = os.path.join(source_path, egg_info)
            if os.path.exists(egg_path):
                shutil.rmtree(egg_path)


if __name__ == '__main__':
    main()
