# SebastianRzk/borg-backup-container

**A simple docker container to create+prune backups with borg, using cron jobs and exposing metrics to a prometheus push
gateway.**

A full example can be found in the example-project folder.

## Installing

### Pulling the image

You can pull the image from `sebastianrzk/borg-backup-container` or `sebastianrzk/borg-backup-container-with-ssh` or build it yourself.

* `sebastianrzk/borg-backup-container` this container is for local backups, openssh is not installed.
* `sebastianrzk/borg-backup-container-with-ssh` is for remote backups. Set your `BORG_BACKUP_PROD_PATH` to the ssh-location and wire your private key with a volume into the container.

An example can be found in the example-project folder.

### Doing a local backup 

A full example can be found in the example-project folder.

Example paragraph in your docker-compose.yml:

    backup:
      image: sebastianrzk/borg-backup-container
      volumes:
        - your-data-volume-or-bind-mount:/prod/:ro
        - ./backup_folder:/backup
      environment:
        - BORG_BACKUP_CRON=0 * * * *
      restart: unless-stopped

### Doing a remote (ssh) backup

    backup:
      image: sebastianrzk/borg-backup-container-with-ssh
      volumes:
        - your-data-volume-or-bind-mount:/prod/:ro
        - your-private-key:/root/.ssh/id_rsa:ro
        - your-known_hosts:/root/.ssh/known_hosts:ro
      environment:
        - BORG_BACKUP_CRON=0 * * * *
        - BORG_BACKUP_BACKUP_PATH=ssh://your-ssh-server/your-path-on-server
      restart: unless-stopped

## Configuration parameter

The complete configuration can be done via environment variables.

An example can be found in the example-project folder.

### Initial repository creation

| parameter                          | default value | explanation                                                                                                                                                                                                                                                                                                                 |
|------------------------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| BORG_BACKUP_AUTO_REPO_INIT_ENABLED | yes           | If the "yes" parameter is set, the backup container tries to create a new repository each time it is run. If a repository already exists, nothing happens. If you want an error if the repository doesn't exist (e.g. on an external mount that isn't currently available), set this to something other than yes, e.g. "no" |
| BORG_BACKUP_ENCRYPTION_PASSPHRASE  |               | If some passphrase is set, the repository gets created with encryption `repokey` and the provided passphrase                                                                                                                                                                                                                |
| BORG_BACKUP_PROD_PATH              | `/prod/`      | The location where borg is expecting borg repository. If you want to use the container for a remote backup, use  `sebastianrzk/borg-backup-container-with-ssh` container and set this to your ssh location (e.g. `ssh://username@yourserver/backuppath`)                                                                    | 


### Backup data

| parameter                         | default value                     | explanation                                                                                                                               |
|-----------------------------------|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| BORG_BACKUP_CRON                  | none                              | cron that triggers the backup+pruning process. E.g. */5 * * * *                                                                           | 
| BORG_BACKUP_SNAPSHOT_NAME         | automatic-{now:%Y-%m-%dT%H:%M:%S} | the name of each snapshot created by the cron                                                                                             |
| BORG_BACKUP_ENCRYPTION_PASSPHRASE |                                   | The passphrase for accessing the repository (encrpytion mode `repokey`). If nothing set (default), the repo is acessed without encryption |

### Prune data

| parameter                         | default value | explanation                                                                                                                               |
|-----------------------------------|---------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| BORG_PRUNE_KEEP_HOURLY            | <empty>       | hourly backups to be kept. See [borg prune documentation](https://borgbackup.readthedocs.io/en/stable/usage/prune.html)                   | 
| BORG_PRUNE_KEEP_DAILY             | 7             | daily backups to be kept. See [borg prune documentation](https://borgbackup.readthedocs.io/en/stable/usage/prune.html)                    | 
| BORG_PRUNE_KEEP_WEEKLY            | 4             | weekly backups to be kept. See [borg prune documentation](https://borgbackup.readthedocs.io/en/stable/usage/prune.html)                   | 
| BORG_PRUNE_KEEP_MONTHLY           | <empty>       | monthly backups to be kept. See [borg prune documentation](https://borgbackup.readthedocs.io/en/stable/usage/prune.html)                  | 
| BORG_BACKUP_ENCRYPTION_PASSPHRASE |               | The passphrase for accessing the repository (encrpytion mode `repokey`). If nothing set (default), the repo is acessed without encryption |


### Push metrics to prometheus push gateway

| parameter                               | default value                 | explanation                                                                                                                                                    |
|-----------------------------------------|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| BORG_PROMETHEUS_PUSHGATEWAY_ENABLED     | yes                           | Everything else than "yes" switches the metric collection as well as the push to the prometheus gateway off                                                    |
| BORG_PROMETHEUS_INITIAL_CHECKUP_ENABLED | yes                           | Everything else than "yes" switches initial checkup. Initial checkup pushes initial metrics to push gateway on container startup. If the host machine reboots. |
| BORG_PROMETHEUS_PUSHGATEWAY             | prometheus-pushgateway:9091   | Url of the prometheus push gateway                                                                                                                             |
| BORG_PROMETHEUS_PUSHGATEWAY_USERNAME    | none                          | username used to push to prometheus                                                                                                                            |
| BORG_PROMETHEUS_PUSHGATEWAY_PASSWORD    | none                          | password used to push to prometheus                                                                                                                            |
| BORG_PROMETHEUS_PUSHGATEWAY_JOBNAME     | push-borg                     | job name that will be pushed to the prometheus gateway                                                                                                         |
| BORG_INSTANCE_NAME                      | hostname                      | instance name that is pushed to the prometheus gateway                                                                                                         |

## Prometheus metrics

| name                        | type    | description                                  |
|-----------------------------|---------|----------------------------------------------|
| instance                    | Info    | Instance name (provided via env) or hostname |
| borg_number_of_backups      | Gauge   | Number of snapshots in borg repository.      |
| borg_first_backup_timestamp | Gauge   | Timestamp of first snapshot in repository.   |
| borg_last_backup_timestamp  | Gauge   | Timestamp of last snapshot in repository     |
| borg_backup_folder_size     | Gauge   | Size of the borg backup repository folder.   |
| borg_production_folder_size | Gauge   | Size of the production folder                |
| borg_create_backup_time     | Summary | Seconds used to create the backup.           |
| borg_prune_backup_time      | Summary | Seconds used to prune the backup.            |

Example PromQL for backup monitoring:

Metric on the last of backup. Can alert if no new backups are created anymore:

    time() - (borg_last_backup_timestamp{})


