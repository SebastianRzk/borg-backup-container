#!/bin/bash

# Start the run once job.
echo "Backup container has been started";

declare -p | grep -Ev 'BASHOPTS|BASH_VERSINFO|EUID|PPID|SHELLOPTS|UID' > /container.env;

# Setup a cron schedule
echo "SHELL=/bin/bash
BASH_ENV=/container.env
$BORG_BACKUP_CRON python3 /main.py
# This extra line makes it a valid cron" > scheduler.txt;

python3 /main.py --initial-checkup

crontab scheduler.txt;
crond -f;

