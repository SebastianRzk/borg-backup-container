#!/bin/bash

# Start the run once job.
echo "Backup container has been started";

declare -p | grep -Ev 'BASHOPTS|BASH_VERSINFO|EUID|PPID|SHELLOPTS|UID' > /container.env;

# Setup a cron schedule
echo "SHELL=/bin/bash
BASH_ENV=/container.env
$BORG_BACKUP_CRON python3 /main.py >> /backup/last.log 2>&1
# This extra line makes it a valid cron" > scheduler.txt;

crontab scheduler.txt;
crond -f;

