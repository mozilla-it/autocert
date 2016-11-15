#!/usr/bin/env python3

import os

DOIT_CONFIG = {
    'default_tasks': ['deploy', 'logs'],
    'verbosity': 2,
}

USER = os.getenv('USER')
LOGDIR = '/var/log/auto-cert'

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
            'sudo mkdir -p /var/log/auto-cert',
            'sudo chown -R {USER}:{USER} {LOGDIR}'.format(**globals()),
            'touch {LOGDIR}/api.log'.format(**globals()),
        ],
    }

def task_deploy():
    '''
    deloy flask app via docker-compose
    '''
    return {
        'task_dep': ['noroot', 'test', 'version', 'logdir'],
        'actions': [
            'docker-compose build',
            'docker-compose up --remove-orphans -d',
        ],
    }

def task_logs():
    '''
    run docker-compose logs
    '''
    return {
        'actions': [
            'docker-compose logs',
            'cat {LOGDIR}/api.log'.format(**globals()),
        ],
    }

def task_tidy():
    '''
    delete cached files
    '''
    TIDY_FILES = [
        '.doit.db/',
        '__pycache__/',
        'venv/',
        'api/VERSION',
    ]
    return {
        'actions': [
            'rm -rf ' + ' '.join(TIDY_FILES),
        ],
    }

def task_nuke():
    '''
    git clean and reset
    '''
    return {
        'task_dep': ['tidy'],
        'actions': [
            'git clean -fd',
            'git reset --hard HEAD',
        ],
    }

if __name__ == '__main__':
    print('should be run with doit installed')
    import doit
    doit.run(globals())
