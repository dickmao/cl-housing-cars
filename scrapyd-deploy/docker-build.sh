#!/bin/bash -ex

while [[ $# -gt 0 ]] ; do
  key="$1"
  case "$key" in
      -s|--scratch)
      scratch=1
      shift
      ;;
      *)
      break
      ;;    
  esac
done

wd=$(realpath $(dirname $0))
cd $wd
if [ -d ".deployer" ]; then
  (cd .deployer ; git pull )  
else
  git clone --depth=1 --single-branch git@github.com:dickmao/deployer.git .deployer
fi

if [ ! -z $(docker ps -aq --filter "name=scrapyd") ]; then
  docker rm -f $(docker ps -aq --filter "name=scrapyd")
fi

COPY=""
mkdir -p $wd/.scrapy
for file in $( cd .. ; git ls-files ) ; do
  ( cd .. ; rsync -aR $file $wd/.scrapy/ )
  dir=$(dirname $file)
  COPY=$(printf "$COPY\nCOPY ./.scrapy/${file} /${dir}/")
done

cat > ./bash_aliases.tmp <<EOF
function schedule {
  SPIDER=\${1:-que}
  OUTPUT=\$(curl -s http://scrapyd:6800/listjobs.json?project=tutorial | jq -r '.status, .running[].spider, .pending[].spider')
  if [ "ok" != \${OUTPUT%%\$'\n'*} ]; then
    (>&2 echo "scrapyd status \${OUTPUT%%\$'\n'*}")
    return 1
  fi
  read -r -a array <<< \${OUTPUT#*\$'\n'}
  if [[ " \${array[@]} " =~ " \$SPIDER " ]]; then
    (>&2 echo "\$SPIDER running or pending")
    return 1
  fi
  scrapyd-client -t http://scrapyd:6800 schedule -p tutorial \$SPIDER
}

alias listspiders='curl http://scrapyd:6800/listspiders.json?project=tutorial'
alias listjobs='curl http://scrapyd:6800/listjobs.json?project=tutorial'
EOF

cat > ./scrapyd.conf.tmp <<EOF
[scrapyd]
eggs_dir          = /var/lib/scrapyd/eggs
logs_dir          = /var/lib/scrapyd/logs
dbs_dir           = /var/lib/scrapyd/dbs
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

cat > ./scrapyd-schedule.tmp <<EOF
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
# m h dom mon dow user   command
# 10   *   *   *   * root   bash -lc 'schedule newyork' '> /proc/1/fd/1 2>/proc/1/fd/2'
EOF

cat > ./Dockerfile.tmp <<EOF
FROM debian:stretch
MAINTAINER kev <noreply@easypi.pro>

RUN set -xe \
    && apt-get -yq update \
    && apt-get install -yq autoconf \
                           build-essential \
                           curl \
                           git \
                           libffi-dev \
                           libssl-dev \
                           libtool \
                           libxml2 \
                           libxml2-dev \
                           libxslt1.1 \
                           libxslt1-dev \
                           python \
                           python-dev \
                           vim-tiny \
    && apt-get install -yq libtiff5 \
                           libtiff5-dev \
                           libfreetype6-dev \
                           libjpeg62-turbo \
                           libjpeg62-turbo-dev \
                           liblcms2-2 \
                           liblcms2-dev \
                           libwebp6 \
                           libwebp-dev \
                           zlib1g \
                           zlib1g-dev \
    && curl -sSL https://bootstrap.pypa.io/get-pip.py | python \
    && pip install git+https://github.com/scrapy/scrapy.git@1.5.0 \
                   git+https://github.com/scrapy/scrapyd.git@1.2.0 \
                   git+https://github.com/scrapy/scrapyd-client.git@v1.2.0a1 \
                   git+https://github.com/scrapinghub/scrapy-splash.git \
                   git+https://github.com/scrapinghub/scrapyrt.git \
                   git+https://github.com/python-pillow/Pillow.git \
    && curl -sSL https://github.com/scrapy/scrapy/raw/master/extras/scrapy_bash_completion -o /etc/bash_completion.d/scrapy_bash_completion \
    && echo 'source /etc/bash_completion.d/scrapy_bash_completion' >> /root/.bashrc \
    && apt-get install -yq cron \
                           jq \
                           netcat-openbsd \
    && curl -sSL https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -o ./wait-for-it.sh \
    && chmod u+x ./wait-for-it.sh \
    && pip install pytz python-dateutil boto3 scrapoxy editdistance GitPython redis \
    && echo "source /root/.bash_aliases" >> /root/.bashrc \
    && apt-get purge -y --auto-remove autoconf \
                                      build-essential \
                                      libffi-dev \
                                      libssl-dev \
                                      libtool \
                                      libxml2-dev \
                                      libxslt1-dev \
                                      python-dev \
    && apt-get purge -y --auto-remove libtiff5-dev \
                                      libfreetype6-dev \
                                      libjpeg62-turbo-dev \
                                      liblcms2-dev \
                                      libwebp-dev \
                                      zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

VOLUME /etc/scrapyd/ /var/lib/scrapyd/
EXPOSE 6800

COPY ./scrapyd-schedule.tmp /etc/cron.d/scrapyd-schedule
RUN chmod 0644 /etc/cron.d/scrapyd-schedule
$COPY
COPY ./scrapyd.conf.tmp /etc/scrapyd/scrapyd.conf
COPY ./bash_aliases.tmp /root/.bash_aliases
EOF

.deployer/ecr-build-and-push.sh ./Dockerfile.tmp scrapyd-deploy:latest

rm ./Dockerfile.tmp
rm ./scrapyd.conf.tmp
rm ./scrapyd-schedule.tmp
rm ./bash_aliases.tmp

if [ ! -z $scratch ] ; then
  SCAFF=$(docker images -q scrapyd-deploy:scaff)
  if [ ! -z $SCAFF ]; then
    SCAFF_PARENT=$(docker inspect --format='{{.Parent}}' $SCAFF | cut -d':' -f2)
    docker rmi -f $SCAFF
    if [ ! -z $SCAFF_PARENT ]; then
      docker rmi -f ${SCAFF_PARENT}
    fi  
  fi
fi

# if [ -z $(docker images -q scrapyd-deploy:scaff) ] ; then
#   RAND=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1)
#   docker run --name=$RAND scrapyd-deploy:latest true
#   TOCOMMIT=$(docker ps -aq --filter="name=$RAND")
#   docker commit -m "need faster" $TOCOMMIT scrapyd-deploy:scaff
#   docker rm $TOCOMMIT
# fi
