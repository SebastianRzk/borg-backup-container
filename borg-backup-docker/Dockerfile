FROM ubuntu

ENV BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=yes
RUN apt-get update && apt-get install borgbackup python3 python3-pip cron --yes
COPY requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt
COPY main.py /main.py
ADD entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT bash /entrypoint.sh
