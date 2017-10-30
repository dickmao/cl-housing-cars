#!/bin/bash -ex


WDIR="/var/lib/scrapyd"
cd $(dirname $0)
COPY=""
for file in $(git ls-files) ; do
    dir=$(dirname $file)
    COPY=$(printf "$COPY\nCOPY ./${file} ${WDIR}/")
done

cat > ./.scrapyd.conf <<EOF
[scrapyd]
eggs_dir          = ${WDIR}/eggs
logs_dir          = ${WDIR}/logs
dbs_dir           = ${WDIR}/dbs
jobs_to_keep      = 5
max_proc          = 0
max_proc_per_cpu  = 4
finished_to_keep  = 100
poll_interval     = 5
bind_address      = 0.0.0.0
http_port         = 6800
debug             = off
runner            = scrapyd.runner
application       = scrapyd.app.application
launcher          = scrapyd.launcher.Launcher

[services]
schedule.json     = scrapyd.webservice.Schedule
cancel.json       = scrapyd.webservice.Cancel
addversion.json   = scrapyd.webservice.AddVersion
listprojects.json = scrapyd.webservice.ListProjects
listversions.json = scrapyd.webservice.ListVersions
listspiders.json  = scrapyd.webservice.ListSpiders
delproject.json   = scrapyd.webservice.DeleteProject
delversion.json   = scrapyd.webservice.DeleteVersion
listjobs.json     = scrapyd.webservice.ListJobs
daemonstatus.json = scrapyd.webservice.DaemonStatus
EOF

cat > Dockerfile.tmp <<EOF
FROM vimagick/scrapyd
MAINTAINER dick <noreply@shunyet.com>
WORKDIR ${WDIR}
$COPY
COPY ./.scrapyd.conf /etc/scrapyd/scrapyd.conf
RUN set -xe \
  && apt-get update \
  && apt-get -yq install gcc python-dev \
  && curl -sSL https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -o ./wait-for-it.sh \
  && chmod u+x ./wait-for-it.sh \
  && pip install pytz python-dateutil redis nbconvert jupyter \
  && rm -rf /var/lib/apt/lists/*
EOF

OLDIMAGE=$(docker images -q scrapyd-deploy)
if [ ! -z $OLDIMAGE ]; then
    docker rmi -f $OLDIMAGE
fi
docker build --file Dockerfile.tmp --force-rm -t scrapyd-deploy .
rm ./.scrapyd.conf
eval `aws ecr get-login --no-include-email`
if ! aws ecr describe-repositories --repository-names scrapyd-deploy 2>/dev/null ; then
    aws ecr create-repository --repository-name  scrapyd-deploy
fi
docker tag scrapyd-deploy:latest 303634175659.dkr.ecr.us-east-2.amazonaws.com/scrapyd-deploy:latest
docker push 303634175659.dkr.ecr.us-east-2.amazonaws.com/scrapyd-deploy:latest

