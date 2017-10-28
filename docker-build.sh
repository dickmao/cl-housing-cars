#!/bin/bash -ex

cd $(dirname $0)
COPY=""
for file in $(git ls-files) ; do
    dir=$(dirname $file)
    COPY=$(printf "$COPY\nCOPY ./${file} /${dir}/")
done

cat > Dockerfile.tmp <<EOF
FROM vimagick/scrapyd
MAINTAINER dick <noreply@shunyet.com>
$COPY

RUN set -xe \
  && curl -sSL https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -o ./wait-for-it.sh \
  && chmod u+x ./wait-for-it.sh \
  && pip install pytz \
  && rm -rf /var/lib/apt/lists/*
EOF

OLDIMAGE=$(docker images -q scrapyd-deploy)
if [ ! -z $OLDIMAGE ]; then
    docker rmi -f $OLDIMAGE
fi
docker build --file Dockerfile.tmp --force-rm -t scrapyd-deploy .
eval `aws ecr get-login --no-include-email`
if ! aws ecr describe-repositories --repository-names scrapyd-deploy 2>/dev/null ; then
    aws ecr create-repository --repository-name  scrapyd-deploy
fi
docker tag scrapyd-deploy:latest 303634175659.dkr.ecr.us-east-2.amazonaws.com/scrapyd-deploy:latest
docker push 303634175659.dkr.ecr.us-east-2.amazonaws.com/scrapyd-deploy:latest
