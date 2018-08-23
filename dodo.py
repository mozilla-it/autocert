
#!/usr/bin/env python3

import os
import re
import pwd
import sys

from doit import get_var
from ruamel import yaml

REPOROOT = os.path.dirname(os.path.abspath(__file__))
PROJDIR = REPOROOT
APPDIR = PROJDIR + '/api'
TESTDIR = PROJDIR + '/tests'
UTILSDIR = REPOROOT + '/repos/utils'
LOGDIR = REPOROOT + '/oldlogs'

UID = os.getuid()
GID = pwd.getpwuid(UID).pw_gid
USER = pwd.getpwuid(UID).pw_name
ENV=dict(AC_UID=UID, AC_GID=GID, AC_USER=USER)

sys.path.insert(0, APPDIR)
from config import _update_config, CONFIG_YML, DOT_CONFIG_YML
from utils.fmt import *
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

ENVS = ' '.join([
    'PYTHONPATH=.:api:$PYTHONPATH',
])

class UnknownPkgmgrError(Exception):
    def __init__(self):
        super(UnknownPkgmgrError, self).__init__('unknown pkgmgr!')

def get_user_uid_gid():
    return [
        fmt('AC_USER={USER}'),
        fmt('AC_UID={UID}'),
        fmt('AC_GID={GID}'),
    ]

def get_env_vars(regex=None):
    return [key+'='+value for key, value in os.environ.items() if regex == None or regex.search(key)]

def check_hash(program):
    from subprocess import check_call, CalledProcessError, PIPE
    try:
        check_call(fmt('hash {program}'), shell=True, stdout=PIPE, stderr=PIPE)
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
            fmt('cloc {excludes} {scandir}'),
        ],
        'uptodate': [
            lambda: not check_hash('cloc'),
        ],
    }

def task_checkpath():
    '''
    check for required path /data/autocert/certs
    '''
    return {
        'actions': [
            'test -d /data/autocert/certs',
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
    test = '`git diff-index --quiet HEAD --`'
    pull = 'git pull --rebase'
    dirty = fmt('echo "refusing to \'{pull}\' because the tree is dirty"')
    return {
        'actions': [
            fmt('if {test}; then {pull}; else {dirty}; exit 1; fi'),
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
            fmt('venv/bin/pip3 install -r {PROJDIR}/requirements.txt'),
            fmt('venv/bin/pip3 install -r {TESTDIR}/requirements.txt'),
            fmt('{ENVS} venv/bin/pytest -s -vv tests/'),
        ],
    }

def task_version():
    '''
    write git describe to VERSION file
    '''
    return {
        'actions': [
            fmt('git describe --abbrev=7 | xargs echo -n > {APPDIR}/VERSION'),
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
            fmt('mkdir -p {LOGDIR}'),
            fmt('cd {PROJDIR} && docker-compose logs > {LOGDIR}/{timestamp}.log'),
        ]
    }

def task_environment():
    '''
    set the env vars to be used inside of the container
    '''
    def add_env_vars():
        pfmt('{PROJDIR}/docker-compose.yml.wo-envs -> {PROJDIR}/docker-compose.yml')
        print('adding env vars to docker-compose.yml file')
        dcy = yaml.safe_load(open(fmt('{PROJDIR}/docker-compose.yml.wo-envs')))
        for svc in dcy['services'].keys():
            envs = dcy['services'][svc].get('environment', [])
            envs += get_user_uid_gid()
            envs += get_env_vars(re.compile('(no|http|https)_proxy', re.IGNORECASE))
            pfmt('{svc}:')
            for env in envs:
                pfmt('  - {env}')
            dcy['services'][svc]['environment'] = envs
        with open(fmt('{PROJDIR}/docker-compose.yml'), 'w') as f:
            yaml.dump(dcy, f, default_flow_style=False)

    return {
        'task_dep': [
        ],
        'actions': [
            add_env_vars,
        ]
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
            fmt('cd {PROJDIR} && docker-compose build'),
            fmt('cd {PROJDIR} && docker-compose up --remove-orphans -d'),
        ],
    }

def task_rmimages():
    '''
    remove dangling docker images
    '''
    query = '`docker images -q -f dangling=true`'
    return {
        'actions': [
            fmt('docker rmi {query}'),
        ],
        'uptodate': [
            fmt('[ -z "{query}" ] && exit 0 || exit 1'),
        ],
    }

def task_rmvolumes():
    '''
    remove dangling docker volumes
    '''
    query = '`docker volume ls -q -f dangling=true`'
    return {
        'actions': [
            fmt('docker volume rm {query}'),
        ],
        'uptodate': [
            fmt('[ -z "{query}" ] && exit 0 || exit 1'),
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
    filename = REPOROOT + '/LOG_LEVEL'
    if os.path.isfile(filename):
        log_level = open(filename).read().strip()
    log_level = get_var('LOG_LEVEL', log_level)
    if log_level not in LOG_LEVELS:
        raise UnknownLogLevelError(log_level)
    punch = fmt('''
    logging:
        loggers:
            api:
                level: {log_level}
        handlers:
            console:
                level: {log_level}
    ''')
    return {
        'actions': [
            fmt('echo "cp {CONFIG_YML}\n-> {DOT_CONFIG_YML}"'),
            fmt('echo "setting LOG_LEVEL={log_level}"'),
            fmt('cp {CONFIG_YML} {DOT_CONFIG_YML}'),
            lambda: _update_config(DOT_CONFIG_YML, yaml.safe_load(punch)),
        ]
    }


def task_example():
    '''
    cp|strip config.yml -> config.yml.example
    '''
    apikey = '82_CHAR_APIKEY'
    punch = fmt('''
    authorities:
        digicert:
            apikey: {apikey}
    destinations:
        zeus:
            apikey: {apikey}
    ''')
    return {
        'actions': [
            fmt('cp {CONFIG_YML}.example {CONFIG_YML}.bak'),
            fmt('cp {CONFIG_YML} {CONFIG_YML}.example'),
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
    for container in [ fmt('{image}_test{num}') for num in (1, 2)]:
        yield {
            'task_dep': ['prune'],
            'name': container,
            'actions': [fmt('docker run -d --name {container} {image}')],
            'uptodate': [fmt('[ -n "`docker ps -q -f name={container}`" ] && exit 0 || exit 1')]
        }

if __name__ == '__main__':
    print('should be run with doit installed')
    import doit
    doit.run(globals())
