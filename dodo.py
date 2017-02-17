#!/usr/bin/env python3

import os

from doit import get_var
from ruamel import yaml

from api.config import _update_config, CONFIG_YML, DOT_CONFIG_YML

DOIT_CONFIG = {
    'default_tasks': ['deploy', 'rmimages', 'rmvolumes', 'count'],
    'verbosity': 2,
}

USER = os.getenv('USER')

MINIMUM_DOCKER_COMPOSE_VERSION = '1.6'

LOG_LEVELS = [
    'DEBUG',
    'INFO',
    'WARNING',
    'ERROR',
    'CRITICAL',
]


class UnknownPkgmgrError(Exception):
    def __init__(self):
        super(UnknownPkgmgrError, self).__init__('unknown pkgmgr!')

def check_hash(program):
    from subprocess import check_call, CalledProcessError, PIPE
    try:
        check_call('hash {program}'.format(**locals()), shell=True, stdout=PIPE, stderr=PIPE)
        return True
    except CalledProcessError:
        return False

def get_pkgmgr():
    if check_hash('dpkg'):
        return 'deb'
    elif check_hash('rpm'):
        return 'rpm'
    raise UnknownPkgmgrError

def task_count():
    '''
    use the cloc utility to count lines of code
    '''
    excludes = [
        'dist',
        'venv',
        '__pycache__',
        'auto_cert_cli.egg-info',
    ]
    excludes = '--exclude-dir=' + ','.join(excludes)
    scandir = os.path.dirname(__file__)
    return {
        'actions': [
            'cloc {excludes} {scandir}'.format(**locals()),
        ],
        'uptodate': [
            lambda: not check_hash('cloc'),
        ],
    }

def task_checkreqs():
    '''
    check for required software
    '''
    DEBS = [
        'docker-engine',
    ]
    RPMS = [
        'docker-engine',
    ]
    return {
        'deb': {
            'actions': ['dpkg -s ' + deb for deb in DEBS],
        },
        'rpm': {
            'actions': ['rpm -q ' + rpm for rpm in RPMS],
        },
        'brew': {
            'actions': ['true'],
        }
    }[get_pkgmgr()]

def task_dockercompose():
    '''
    assert docker-compose version ({0}) or higher
    '''
    from utils.function import format_docstr
    format_docstr(task_dockercompose, MINIMUM_DOCKER_COMPOSE_VERSION)
    def check_docker_compose():
        import re
        from subprocess import check_output
        from packaging.version import parse as version_parse
        pattern = '(docker-compose version) ([0-9.]+)(, build [a-z0-9]+)'
        output = check_output('docker-compose --version', shell=True).decode('utf-8').strip()
        regex = re.compile(pattern)
        match = regex.search(output)
        version = match.groups()[1]
        assert version_parse(version) >= version_parse(MINIMUM_DOCKER_COMPOSE_VERSION)

    return {
        'actions': [
            check_docker_compose,
        ],
    }

def task_noroot():
    '''
    make sure script isn't run as root
    '''
    then = 'echo "   DO NOT RUN AS ROOT!"; echo; exit 1'
    bash = 'if [[ $(id -u) -eq 0 ]]; then {0}; fi'.format(then)
    return {
        'actions': [
            'bash -c \'{0}\''.format(bash),
        ],
    }

def task_test():
    '''
    setup venv and run pytest
    '''
    return {
        'task_dep': [
            'noroot',
            'config',
        ],
        'actions': [
            'virtualenv --python=$(which python3) venv',
            'venv/bin/pip3 install --upgrade pip',
            'venv/bin/pip install -r api/requirements.txt',
            'venv/bin/pip install -r tests/requirements.txt',
            'venv/bin/pytest -v tests/',
        ],
    }

def task_version():
    '''
    write git describe to VERSION file
    '''
    return {
        'actions': [
            'git describe | xargs echo -n > api/VERSION',
        ],
    }

def task_deploy():
    '''
    deloy flask app via docker-compose
    '''
    return {
        'task_dep': [
            'noroot',
            'checkreqs',
            'version',
            'test',
            'config',
            'dockercompose'
        ],
        'actions': [
            'docker-compose build',
            'docker-compose up --remove-orphans -d',
        ],
    }

def task_rmimages():
    '''
    remove dangling docker images
    '''
    query = '`docker images -q -f dangling=true`'
    return {
        'actions': [
            'docker rmi {query}'.format(**locals()),
        ],
        'uptodate': [
            '[ -z "{query}" ] && exit 0 || exit 1'.format(**locals()),
        ],
    }

def task_rmvolumes():
    '''
    remove dangling docker volumes
    '''
    query = '`docker volume ls -q -f dangling=true`'
    return {
        'actions': [
            'docker volume rm {query}'.format(**locals()),
        ],
        'uptodate': [
            '[ -z "{query}" ] && exit 0 || exit 1'.format(**locals()),
        ],
    }

def task_logs():
    '''
    simple wrapper that calls 'docker-compose logs'
    '''
    return {
        'actions': [
            'docker-compose logs',
        ],
    }

def task_config():
    '''
    write config.yml -> .config.yml
    '''
    log_level = 'WARNING'
    filename = '{0}/LOG_LEVEL'.format(os.path.dirname(__file__))
    if os.path.isfile(filename):
        log_level = open(filename).read().strip()
    log_level = get_var('LOG_LEVEL', log_level)
    if log_level not in LOG_LEVELS:
        raise UnknownLogLevelError(log_level)
    punch = '''
    logging:
        loggers:
            api:
                level: {log_level}
        handlers:
            console:
                level: {log_level}
    '''.format(**locals())
    return {
        'actions': [
            'echo "cp {CONFIG_YML}\n-> {DOT_CONFIG_YML}"'.format(**globals()),
            'echo "setting LOG_LEVEL={log_level}"'.format(**locals()),
            'cp {CONFIG_YML} {DOT_CONFIG_YML}'.format(**globals()),
            lambda: _update_config(DOT_CONFIG_YML, yaml.safe_load(punch)),
        ]
    }


def task_example():
    '''
    cp|strip config.yml -> config.yml.example
    '''
    apikey = '82_CHAR_APIKEY'
    punch = '''
    authorities:
        digicert:
            apikey: {apikey}
    destinations:
        zeus:
            apikey: {apikey}
    '''.format(**locals())
    return {
        'actions': [
            'cp {CONFIG_YML}.example {CONFIG_YML}.bak'.format(**globals()),
            'cp {CONFIG_YML} {CONFIG_YML}.example'.format(**globals()),
            lambda: _update_config(CONFIG_YML+'.example', yaml.safe_load(punch)),
        ],
    }

def task_tidy():
    '''
    delete cached files
    '''
    TIDY_FILES = [
        '.doit.db/',
        'venv/',
        'api/VERSION',
    ]
    return {
        'actions': [
            'rm -rf ' + ' '.join(TIDY_FILES),
            'find . | grep -E "(__pycache__|\.pyc$)" | xargs rm -rf',
        ],
    }

def task_nuke():
    '''
    git clean and reset
    '''
    return {
        'task_dep': ['tidy'],
        'actions': [
            'docker-compose kill',
            'docker-compose rm -f',
            'git clean -fd',
            'git reset --hard HEAD',
        ],
    }

def task_setup():
    '''
    setup venv
    '''
    from utils.version import version
    return {
        'actions': [
            'rm -rf auto_cert_cli.egg-info/ venv/ dist/ __pycache__/',
            'virtualenv --python=python3 venv',
            'venv/bin/pip3 install --upgrade pip',
            'venv/bin/pip3 install -r cli/requirements.txt',
            'venv/bin/python3 ./setup.py install',
            'unzip -l venv/lib/python3.5/site-packages/auto_cert_cli-{0}-py3.5.egg'.format(version()),
        ],
    }

if __name__ == '__main__':
    print('should be run with doit installed')
    import doit
    doit.run(globals())
