#!/usr/bin/env python3

import os

from doit import get_var

DOIT_CONFIG = {
    'default_tasks': ['deploy', 'rmimages', 'logs'],
    'verbosity': 2,
}

USER = os.getenv('USER')
LOGDIR = '/var/tmp/auto-cert'

MINIMUM_DOCKER_COMPOSE_VERSION = '1.6'


class UnknownPkgmgrError(Exception):
    def __init__(self):
        super(UnknownPkgmgrError, self).__init__('unknown pkgmgr!')

def get_pkgmgr():
    def check_hash(program):
        from subprocess import check_call, CalledProcessError
        try:
            check_call('hash {program}'.format(**locals()), shell=True)
            return True
        except CalledProcessError as cpe:
            return False
    if check_hash('dpkg'):
        return 'deb'
    elif check_hash('rpm'):
        return 'rpm'
    raise UnknownPkgmgrError

def task_checkreqs():
    '''
    check for required software
    '''
    DEBS = [
        'docker-engine',
        'libpq-dev',
    ]
    RPMS = [
        'docker-engine',
        'postgresql-devel',
    ]
    return {
        'deb': {
            'actions': ['dpkg -s ' + deb for deb in DEBS],
        },
        'rpm': {
            'actions': ['rpm -q ' + rpm for rpm in RPMS],
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
        pattern = '(docker-compose version) ([0-9.]+)(, build [0-9]+)'
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
        'task_dep': ['noroot', 'logdir'],
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

def task_logdir():
    '''
    setup logging directory
    '''
    return {
        'actions': [
            'mkdir -p {LOGDIR}'.format(**globals()),
            'chown -R {USER}:{USER} {LOGDIR}'.format(**globals()),
            'touch {LOGDIR}/api.log'.format(**globals()),
        ],
    }

def task_deploy():
    '''
    deloy flask app via docker-compose
    '''
    return {
        'task_dep': [
            'noroot',
            'test',
            'version',
            'logdir',
            'checkreqs',
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
    return {
        'actions': [
            'docker rmi $(docker images -q --filter "dangling=true")',
        ],
        'uptodate': [
            '[ -z "`docker images -q --filter "dangling=true"`"] && exit 0 || exit 1',
        ],
    }

def task_logs():
    '''
    run docker-compose logs
    '''

    star80 = 'echo "{0}"'.format('*'*80)
    return {
        'actions': [
            star80,
            'echo "logging from docker-compose"',
            'docker-compose logs',
            star80,
            'echo "logging from /var/tmp/auto-cert/api.log"',
            'cat {LOGDIR}/api.log'.format(**globals()),
            star80,
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
            'rm -rf {LOGDIR}/api.log'.format(**globals()),
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
