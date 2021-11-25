# SebastianRzk/borg-backup-container

**A simple docker container to create+prune backups with borg, using cron jobs and exposing metrics to a prometheus push gateway.**

A full example can be found in the example-project folder.

## Installing

You can pull the image from `sebastianrzk/borg-backup-container` or build it yourself.

An example can be found in the example-project folder.

## Configuration parameter

The complete configuration can be done via environment variables.

### Backup data

| parameter | default value | explanation |
|-----------|---------------|-------------|
|BORG_BACKUP_CRON| none | cron that triggers the backup+pruning process. E.g. */5 * * * * | 
|BORG_BACKUP_SNAPSHOT_NAME| automatic-{now:%Y-%m-%dT%H:%M:%S} | the name of each snapshot created by the cron |

### Prune data

| parameter | default value | explanation |
|-----------|---------------|-------------|
|BORG_PRUNE_KEEP_DAILY| 7 | daily backups to be kept. See [borg prune documentation](https://borgbackup.readthedocs.io/en/stable/usage/prune.html)| 
|BORG_PRUNE_KEEP_WEEKLY| 4 | weekly backups to be kept. See [borg prune documentation](https://borgbackup.readthedocs.io/en/stable/usage/prune.html)| 

### Push metrics to prometheus push gateway

| parameter | default value | explanation |
|-----------|---------------|-------------|
|BORG_PROMETHEUS_PUSHGATEWAY_ENABLED| yes | Everything else than "yes" switches the metric collection as well as the push to the prometheus gateway off |
|BORG_PROMETHEUS_PUSHGATEWAY| prometheus-pushgateway:9091 | Url of the prometheus push gateway |
|BORG_PROMETHEUS_PUSHGATEWAY_USERNAME| none | username used to push to prometheus  |
|BORG_PROMETHEUS_PUSHGATEWAY_PASSWORD| none | password used to push to prometheus |
|BORG_PROMETHEUS_PUSHGATEWAY_JOBNAME| push-borg | job name that will be pushed to the prometheus gateway |
|BORG_INSTANCE_NAME| hostname | instance name that is pushed to the prometheus gateway |


## Prometheus metrics

| name | type | description |
|------|------|-------------|
|instance|Info|Instance name (provided via env) or hostname|
|borg_number_of_backups|Gauge|Number of snapshots in borg repository.|
|borg_first_backup_timestamp|Gauge|Timestamp of first snapshot in repository.|
|borg_last_backup_timestamp|Gauge|Timestamp of last snapshot in repository|
|borg_backup_folder_size|Gauge|Size of the borg backup repository folder.|
|borg_production_folder_size|Gauge|Size of the production folder|
|borg_create_backup_time|Summary|Seconds used to create the backup.|
|borg_prune_backup_time|Summary|Seconds used to prune the backup.|

Example PromQL for backup monitoring:

Metric on the last of backup. Can alert if no new backups are created anymore:

    time() - (borg_last_backup_timestamp{})


