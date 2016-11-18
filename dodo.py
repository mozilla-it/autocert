#!/usr/bin/env python3

import os

DOIT_CONFIG = {
    'default_tasks': ['deploy', 'logs'],
    'verbosity': 2,
}

USER = os.getenv('USER')
LOGDIR = '/var/tmp/auto-cert'
print('LOGDIR:', LOGDIR)

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
            'echo "{0}"'.format('*'*80),
            'echo "logging from docker-compose"',
            'docker-compose logs',
            'echo "{0}"'.format('*'*80),
            'echo "logging from /var/tmp/auto-cert/api.log"',
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

def task_setup():
    '''
    setup venv
    '''
    return {
        'actions': [
            'rm -rf auto_cert_cli.egg-info/ venv/ dist/ __pycache__/',
            'virtualenv --python=python3 venv',
            'venv/bin/pip3 install -r cli/requirements.txt',
            'venv/bin/python3 ./setup.py install',
            #'unzip -l venv/lib/python3.5/site-packages/auto_cert_cli-0.0.dev6+gcd03869-py3.5.egg/',
            'tree venv/lib/python3.5/site-packages/auto_cert_cli-0.0.dev6+gcd03869-py3.5.egg/',
        ],
    }

if __name__ == '__main__':
    print('should be run with doit installed')
    import doit
    doit.run(globals())
