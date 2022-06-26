import subprocess
import os
import json
import socket
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Info, Summary
from prometheus_client.exposition import basic_auth_handler
from datetime import datetime

BORG_BACKUP_BACKUP_PATH_NAME = 'BORG_BACKUP_BACKUP_PATH'
BORG_BACKUP_BACKUP_PATH_DEFAULT = '/backup/borg_backup/'

BORG_BACKUP_AUTO_REPO_INIT_ENABLED = 'BORG_BACKUP_AUTO_REPO_INIT_ENABLED'
BORG_BACKUP_AUTO_REPO_INIT_ENABLED_DEFAULT = 'yes'

BORG_BACKUP_ENCRYPTION_PASSPHRASE = 'BORG_BACKUP_ENCRYPTION_PASSPHRASE'
BORG_BACKUP_ENCRYPTION_PASSPHRASE_DEFAULT = ''

BORG_BACKUP_PROD_PATH_NAME = 'BORG_BACKUP_PROD_PATH'
BORG_BACKUP_PROD_PATH_DEFAULT = '/prod/'

BORG_PRUNE_KEEP_DAILY_NAME = 'BORG_PRUNE_KEEP_DAILY'
BORG_PRUNE_KEEP_DAILY_DEFAULT = 7

BORG_PRUNE_KEEP_WEEKLY_NAME = 'BORG_PRUNE_KEEP_WEEKLY'
BORG_PRUNE_KEEP_WEEKLY_DEFAULT = 4

BORG_BACKUP_SNAPSHOT_NAME_NAME = 'BORG_BACKUP_SNAPSHOT_NAME'
BORG_BACKUP_SNAPSHOT_NAME_DEFAULT = 'automatic-{now:%Y-%m-%dT%H:%M:%S}'

BORG_INSTANCE_NAME_NAME = 'BORG_INSTANCE_NAME'
BORG_INSTANCE_NAME_DEFAULT = socket.gethostname()

BORG_PROMETHEUS_PUSHGATEWAY_ENABLED_NAME = 'BORG_PROMETHEUS_PUSHGATEWAY_ENABLED'
BORG_PROMETHEUS_PUSHGATEWAY_ENABLED_DEFAULT = 'yes'

BORG_PROMETHEUS_PUSHGATEWAY_JOBNAME_NAME = 'BORG_PROMETHEUS_PUSHGATEWAY_JOBNAME'
BORG_PROMETHEUS_PUSHGATEWAY_JOBNAME_DEFAULT = 'push-borg'

BORG_PROMETHEUS_PUSHGATEWAY_NAME = 'BORG_PROMETHEUS_PUSHGATEWAY'
BORG_PROMETHEUS_PUSHGATEWAY_DEFAULT = 'prometheus-pushgateway:9091'

BORG_PROMETHEUS_PUSHGATEWAY_USERNAME_NAME = 'BORG_PROMETHEUS_PUSHGATEWAY_USERNAME'
BORG_PROMETHEUS_PUSHGATEWAY_USERNAME_DEFAULT = None

BORG_PROMETHEUS_PUSHGATEWAY_PASSWORD_NAME = 'BORG_PROMETHEUS_PUSHGATEWAY_PASSWORD'
BORG_PROMETHEUS_PUSHGATEWAY_PASSWORD_DEFAULT = None


def get_or_default(name, default_value):
    value = os.environ.get(name)
    if not value:
        return default_value
    return value


def backup_path():
    return get_or_default(BORG_BACKUP_BACKUP_PATH_NAME, BORG_BACKUP_BACKUP_PATH_DEFAULT)


def prod_path():
    return get_or_default(BORG_BACKUP_PROD_PATH_NAME, BORG_BACKUP_PROD_PATH_DEFAULT)


def backup_name():
    return get_or_default(BORG_BACKUP_SNAPSHOT_NAME_NAME, BORG_BACKUP_SNAPSHOT_NAME_DEFAULT)


def backup_keep_weekly():
    return get_or_default(BORG_PRUNE_KEEP_WEEKLY_NAME, BORG_PRUNE_KEEP_WEEKLY_DEFAULT)


def backup_keep_daily():
    return get_or_default(BORG_PRUNE_KEEP_DAILY_NAME, BORG_PRUNE_KEEP_DAILY_DEFAULT)


def instance_name():
    return get_or_default(BORG_INSTANCE_NAME_NAME, BORG_INSTANCE_NAME_DEFAULT)


def is_push_enabled():
    return get_or_default(BORG_PROMETHEUS_PUSHGATEWAY_ENABLED_NAME, BORG_PROMETHEUS_PUSHGATEWAY_ENABLED_DEFAULT) == 'yes'


def is_init_enabled():
    return get_or_default(BORG_BACKUP_AUTO_REPO_INIT_ENABLED, BORG_BACKUP_AUTO_REPO_INIT_ENABLED_DEFAULT) == 'yes'


def jobname():
    return get_or_default(BORG_PROMETHEUS_PUSHGATEWAY_JOBNAME_NAME, BORG_PROMETHEUS_PUSHGATEWAY_JOBNAME_DEFAULT)


def pushgateway():
    return get_or_default(BORG_PROMETHEUS_PUSHGATEWAY_NAME, BORG_PROMETHEUS_PUSHGATEWAY_DEFAULT)


def username():
    return get_or_default(BORG_PROMETHEUS_PUSHGATEWAY_USERNAME_NAME, BORG_PROMETHEUS_PUSHGATEWAY_USERNAME_DEFAULT)


def password():
    return get_or_default(BORG_PROMETHEUS_PUSHGATEWAY_PASSWORD_NAME, BORG_PROMETHEUS_PUSHGATEWAY_PASSWORD_DEFAULT)


def encryption_passphrase():
    return get_or_default(BORG_BACKUP_ENCRYPTION_PASSPHRASE, BORG_BACKUP_ENCRYPTION_PASSPHRASE_DEFAULT)


def call_in_borg_env(command):
    if encryption_enabled():
        print("call with BORG_PASSPHRASE set")
        return subprocess.call(command, env=dict(os.environ, BORG_PASSPHRASE=encryption_passphrase()))
    return subprocess.call(command)


def create_backup():
    param_backup_destination = '{}::{}'.format(backup_path(), backup_name())
    command = ['borg', 'create', param_backup_destination,  prod_path()]
    print(command)
    result = call_in_borg_env(command)
    return result == 0


def keep_daily_param():
    return '--keep-daily={}'.format(backup_keep_daily())


def keep_weekly_param():
    return '--keep-weekly={}'.format(backup_keep_weekly())


def prune_backup():
    command = ['borg', 'prune', '-v', '--list', keep_daily_param(), keep_weekly_param(), backup_path()]
    print(command)
    result = call_in_borg_env(command)
    return result == 0


def encryption_enabled():
    print('encryption enabled', (not not encryption_passphrase()) and encryption_passphrase() != '')
    return (not not encryption_passphrase()) and encryption_passphrase() != ''


def init_backup():
    if encryption_enabled():
        init_backup_encrypted()
        return
    init_backup_cleartext()


def init_backup_encrypted():
    print('try to init encrypted repo')
    command = ['borg', 'init', '--encryption=repokey', backup_path()]
    print(command)
    subprocess.call(command, env=dict(os.environ, BORG_PASSPHRASE=encryption_passphrase()))


def init_backup_cleartext():
    print('try to init cleartext repo')
    command = ['borg', 'init', '--encryption=none', backup_path()]
    print(command)
    subprocess.call(command)


def get_info():
    command = ['borg list ' + backup_path() + ' --json']
    print(command)
    if encryption_enabled():
        borg_info = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            env=dict(os.environ, BORG_PASSPHRASE=encryption_passphrase()))
    else:
        borg_info = subprocess.run(command, shell=True, stdout=subprocess.PIPE)

    return json.loads(borg_info.stdout)


def auth_handler(url, method, timeout, headers, data):
    return basic_auth_handler(url, method, timeout, headers, data, username(), password())


def get_folder_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size


def create_info(registry):
    borg_info = get_info()

    number_of_backups = Gauge('borg_number_of_backups', 'Number of snapshots in borg repository.', registry=registry)
    number_of_backups.set(len(borg_info['archives']))

    first_backup = Gauge('borg_first_backup_timestamp', 'Timestamp of first snapshot in repository.', registry=registry)
    first_backup.set( datetime.fromisoformat(borg_info['archives'][0]['time']).timestamp())

    last_backup = Gauge('borg_last_backup_timestamp', 'Timestamp of last snapshot in repository.', registry=registry)
    last_backup.set(datetime.fromisoformat(borg_info['archives'][-1]['time']).timestamp())

    backup_size = Gauge('borg_backup_folder_size', 'Size of the borg backup repository folder.', registry=registry)
    backup_size.set(get_folder_size(backup_path()))

    prodcution_size = Gauge('borg_production_folder_size', 'Size of the production folder.', registry=registry)
    prodcution_size.set(get_folder_size(prod_path()))


def time_command(name, description, command, registry):
    summary = Summary(name,description, registry=registry)
    before = datetime.now()
    result = command()
    if not result:
        raise Exception('command failed', name, command)
    after = datetime.now()
    time_used = after.timestamp() - before.timestamp()
    summary.observe(time_used)


if __name__ == "__main__":
    print('triggered by cron')
    if is_init_enabled():
        init_backup()
    registry = CollectorRegistry()
    i = Info('instance', instance_name(), registry=registry)

    time_command('borg_create_backup_time', 'Seconds used to create the backup.', create_backup, registry)
    time_command('borg_prune_backup_time', 'Seconds used to prune the backup.', prune_backup, registry)

    if is_push_enabled():
        create_info(registry)
        push_to_gateway(pushgateway(), job=jobname(), registry=registry, handler=auth_handler)
    print('done')
