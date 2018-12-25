#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import pwd
import sys

from doit import get_var
from ruamel import yaml

REPOROOT = os.path.dirname(os.path.abspath(__file__))
PROJNAME = 'autocert'
PROJDIR = REPOROOT + '/' + PROJNAME
APPDIR = PROJDIR + '/api'
CLIDIR = PROJDIR + '/cli'
TESTDIR = REPOROOT + '/tests' #FIXME: PROJDIR?
UTILSDIR = REPOROOT + '/repos/utils'
LOGDIR = REPOROOT + '/oldlogs'

AC_UID = os.getuid()
AC_GID = pwd.getpwuid(AC_UID).pw_gid
AC_USER = pwd.getpwuid(AC_UID).pw_name
AC_APP_PORT=os.environ.get('AC_APP_PORT', 8000)
AC_APP_TIMEOUT=os.environ.get('AC_APP_TIMEOUT', 120)
AC_APP_WORKERS=os.environ.get('AC_APP_WORKERS', 2)
AC_APP_MODULE=os.environ.get('AC_APP_MODULE', 'main:app')

sys.path.insert(0, APPDIR)
from config import _update_config, CONFIG_YML, DOT_CONFIG_YML
from utils.shell import call
from utils.timestamp import utcnow, datetime2int

MINIMUM_DOCKER_COMPOSE_VERSION = '1.6'

LOG_LEVELS = [
    'DEBUG',
    'INFO',
    'WARNING',
    'ERROR',
    'CRITICAL',
]

DOIT_CONFIG = {
    'default_tasks': ['pull', 'deploy', 'rmimages', 'rmvolumes', 'count'],
    'verbosity': 2,
}

class UnknownPkgmgrError(Exception):
    def __init__(self):
        super(UnknownPkgmgrError, self).__init__('unknown pkgmgr!')

def get_ac_envs():
    return [
        f'AC_UID={AC_UID}',
        f'AC_GID={AC_GID}',
        f'AC_USER={AC_USER}',
        f'AC_APP_PORT={AC_APP_PORT}',
        f'AC_APP_TIMEOUT={AC_APP_TIMEOUT}',
        f'AC_APP_WORKERS={AC_APP_WORKERS}',
        f'AC_APP_MODULE={AC_APP_MODULE}',
    ]

def get_env_vars(regex=None):
    return [key+'='+value for key, value in os.environ.items() if regex == None or regex.search(key)]

def check_hash(program):
    from subprocess import check_call, CalledProcessError, PIPE
    try:
        check_call(f'hash {program}', shell=True, stdout=PIPE, stderr=PIPE)
        return True
    except CalledProcessError:
        return False

def get_pkgmgr():
    if check_hash('dpkg'):
        return 'deb'
    elif check_hash('rpm'):
        return 'rpm'
    elif check_hash('brew'):
        return 'brew'
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
            f'cloc {excludes} {scandir}',
        ],
        'uptodate': [
            lambda: not check_hash('cloc'),
        ],
    }

def task_checkpath():
    '''
    check for required path /data/autocert/bundles
    '''
    return {
        'actions': [
            'test -d /data/autocert/bundles',
        ],
    }

def task_checkreqs():
    '''
    check for required software
    '''
    DEBS = [
        'docker-ce',
    ]
    RPMS = [
        'docker-ce',
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
    from utils.function import docstr
    docstr(MINIMUM_DOCKER_COMPOSE_VERSION)
    def check_docker_compose():
        import re
        from subprocess import check_output
        from packaging.version import parse as version_parse
        pattern = '(docker-compose version) ([0-9.]+(-rc[0-9])?)(, build [a-z0-9]+)'
        output = call('docker-compose --version')[1].strip()
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

def task_pull():
    '''
    do a safe git pull
    '''
    submods = call("git submodule status | awk '{print $2}'")[1].split()
    test = '`git diff-index --quiet HEAD --`'
    pull = 'git pull --rebase'
    update = 'git submodule update --remote'
    dirty = 'echo "refusing to \'{cmd}\' because the tree is dirty"'
    dirty_pull = dirty.format(cmd=pull)
    dirty_update = dirty.format(cmd=update)



    yield {
        'name': 'mozilla-it/autocert',
        'actions': [
            f'if {test}; then {pull}; else {dirty_pull}; exit 1; fi',
        ],
    }

    for submod in submods:
        yield {
            'name': submod,
            'actions': [
                f'cd {submod} && if {test}; then {update}; else {dirty_update}; exit 1; fi',
            ],
        }

def task_test():
    '''
    setup venv and run pytest
    '''
    PYTHONPATH = 'PYTHONPATH=.:autocert:autocert/api:$PYTHONPATH'
    return {
        'task_dep': [
            'noroot',
            'config',
        ],
        'actions': [
            'virtualenv --python=$(which python3) venv',
            'venv/bin/pip3 install --upgrade pip',
            f'venv/bin/pip3 install -r {REPOROOT}/requirements.txt',
            f'venv/bin/pip3 install -r {TESTDIR}/requirements.txt',
            f'{PYTHONPATH} venv/bin/python3 -m pytest -s -vv tests/api',
        ],
    }

def task_version():
    '''
    write git describe to VERSION file
    '''
    return {
        'actions': [
            f'git describe --abbrev=7 | xargs echo -n > {APPDIR}/VERSION',
        ],
    }

def task_savelogs():
    '''
    save the logs to a timestamped file
    '''
    timestamp = datetime2int(utcnow())

    return {
        'task_dep': [
            'checkreqs',
            'dockercompose'
        ],
        'actions': [
            f'mkdir -p {LOGDIR}',
            f'cd {PROJDIR} && docker-compose logs > {LOGDIR}/{timestamp}.log',
        ]
    }

def task_environment():
    '''
    set the env vars to be used inside of the container
    '''
    def add_env_vars():
        print(f'{PROJDIR}/docker-compose.yml.wo-envs -> {PROJDIR}/docker-compose.yml')
        print('adding env vars to docker-compose.yml file')
        dcy = yaml.safe_load(open(f'{PROJDIR}/docker-compose.yml.wo-envs'))
        for svc in dcy['services'].keys():
            envs = dcy['services'][svc].get('environment', [])
            envs += get_ac_envs()
            envs += get_env_vars(re.compile('(no|http|https)_proxy', re.IGNORECASE))
            print(f'{svc}:')
            for env in envs:
                print(f'  - {env}')
            dcy['services'][svc]['environment'] = envs
        with open(f'{PROJDIR}/docker-compose.yml', 'w') as f:
            yaml.dump(dcy, f, default_flow_style=False)

    return {
        'task_dep': [
        ],
        'actions': [
            add_env_vars,
        ]
    }

def task_tls():
    '''
    create server key, csr and crt files
    '''
    name = 'server'
    tls = '/data/autocert/tls'
    env = 'PASS=TEST'
    envp = 'env:PASS'
    targets = [
        f'{tls}/{name}.key',
        f'{tls}/{name}.crt',
    ]
    subject = '/C=US/ST=Oregon/L=Portland/O=Autocert Server/OU=Server/CN=0.0.0.0'
    def uptodate():
        return all([os.path.isfile(t) for t in targets])
    return {
        'actions': [
            f'mkdir -p {tls}',
            f'{env} openssl genrsa -aes256 -passout {envp} -out {tls}/{name}.key 2048',
            f'{env} openssl req -new -passin {envp} -subj "{subject}" -key {tls}/{name}.key -out {tls}/{name}.csr',
            f'{env} openssl x509 -req -days 365 -in {tls}/{name}.csr -signkey {tls}/{name}.key -passin {envp} -out {tls}/{name}.crt',
            f'{env} openssl rsa -passin {envp} -in {tls}/{name}.key -out {tls}/{name}.key',
        ],
        'targets': targets,
        'uptodate': [uptodate],
    }

def task_deploy():
    '''
    deloy flask app via docker-compose
    '''
    return {
        'task_dep': [
            'noroot',
            'checkpath',
            'checkreqs',
            'version',
            'test',
            'config',
            'dockercompose',
            'environment',
            'savelogs',
        ],
        'actions': [
            f'cd {PROJDIR} && docker-compose build',
            f'cd {PROJDIR} && docker-compose up --remove-orphans -d',
        ],
    }

def task_rmimages():
    '''
    remove dangling docker images
    '''
    query = '`docker images -q -f dangling=true`'
    return {
        'actions': [
            f'docker rmi {query}',
        ],
        'uptodate': [
            f'[ -z "{query}" ] && exit 0 || exit 1',
        ],
    }

def task_rmvolumes():
    '''
    remove dangling docker volumes
    '''
    query = '`docker volume ls -q -f dangling=true`'
    return {
        'actions': [
            f'docker volume rm {query}',
        ],
        'uptodate': [
            f'[ -z "{query}" ] && exit 0 || exit 1',
        ],
    }

def task_logs():
    '''
    simple wrapper that calls 'docker-compose logs'
    '''
    return {
        'actions': [
            f'cd {PROJDIR} && docker-compose logs',
        ],
    }

def task_config():
    '''
    write config.yml -> .config.yml
    '''
    log_level = 'WARNING'
    filename = PROJDIR + '/LOG_LEVEL'
    if os.path.isfile(filename):
        log_level = open(filename).read().strip()
    log_level = get_var('LOG_LEVEL', log_level)
    if log_level not in LOG_LEVELS:
        raise UnknownLogLevelError(log_level)
    punch = f'''
    logging:
        loggers:
            api:
                level: {log_level}
        handlers:
            console:
                level: {log_level}
    '''
    return {
        'actions': [
            f'echo "cp {CONFIG_YML}\n-> {DOT_CONFIG_YML}"',
            f'echo "setting LOG_LEVEL={log_level}"',
            f'cp {CONFIG_YML} {DOT_CONFIG_YML}',
            lambda: _update_config(DOT_CONFIG_YML, yaml.safe_load(punch)),
        ]
    }


def task_example():
    '''
    cp|strip config.yml -> config.yml.example
    '''
    apikey = '82_CHAR_APIKEY'
    punch = f'''
    authorities:
        digicert:
            apikey: {apikey}
    destinations:
        zeus:
            apikey: {apikey}
    '''
    return {
        'actions': [
            f'cp {CONFIG_YML}.example {CONFIG_YML}.bak',
            f'cp {CONFIG_YML} {CONFIG_YML}.example',
            lambda: _update_config(CONFIG_YML+'.example', yaml.safe_load(punch)),
        ],
    }

def task_rmcache():
    '''
    recursively delete python cache files
    '''
    return dict(
        actions=[
            'find cli/ -depth -name __pycache__ -type d -exec rm -r "{}" \;',
            'find cli/ -depth -name "*.pyc" -type f -exec rm -r "{}" \;',
            'find api/ -depth -name __pycache__ -type d -exec rm -r "{}" \;',
            'find api/ -depth -name "*.pyc" -type f -exec rm -r "{}" \;',
            'find tests/ -depth -name __pycache__ -type d -exec rm -r "{}" \;',
            'find tests/ -depth -name "*.pyc" -type f -exec rm -r "{}" \;',
        ]
    )

def task_tidy():
    '''
    delete cached files
    '''
    TIDY_FILES = [
        '.doit.db/',
        'venv/',
        '{APPDIR}/VERSION',
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
    from utils.version import get_version
    return {
        'actions': [
            'rm -rf auto_cert_cli.egg-info/ venv/ dist/ __pycache__/',
            'virtualenv --python=python3 venv',
            'venv/bin/pip3 install --upgrade pip',
            'venv/bin/pip3 install -r cli/requirements.txt',
            'venv/bin/python3 ./setup.py install',
            'unzip -l venv/lib/python3.5/site-packages/auto_cert_cli-{0}-py3.5.egg'.format(get_version()),
        ],
    }

def task_prune():
    '''
    prune stopped containers
    '''
    return {
        'actions': ['docker rm `docker ps -q -f "status=exited"`'],
        'uptodate': ['[ -n "`docker ps -q -f status=exited`" ] && exit 1 || exit 0']
    }

def task_zeus():
    '''
    launch zeus containers
    '''
    image = 'zeus17.3'
    for num in (1, 2):
        container = f'{image}_test{num}'
        yield {
            'task_dep': ['prune'],
            'name': container,
            'actions': [f'docker run -d -p 909{num}:9090 --name {container} {image}'],
            'uptodate': [f'[ -n "`docker ps -q -f name={container}`" ] && exit 0 || exit 1']
        }

def task_stop():
    '''
    stop running autocert containers
    '''
    def check_docker_ps():
        cmd = 'docker ps --format "{{.Names}}" | grep ' + PROJNAME + ' | { grep -v grep || true; }'
        out = call(cmd, throw=True)[1]
        return out.split('\n') if out else []
    containers = ' '.join(check_docker_ps())
    return {
        'actions': [
            f'docker rm -f {containers}',
        ],
        'uptodate': [
            lambda: len(check_docker_ps()) == 0,
        ],
    }

if __name__ == '__main__':
    print('should be run with doit installed')
    import doit
    doit.run(globals())
