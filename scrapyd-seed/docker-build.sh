#!/bin/bash -ex

cd $(dirname $0)

if [ -d ".deployer" ]; then
  (cd .deployer ; git pull )  
else
  git clone --depth=1 --single-branch git@github.com:dickmao/deployer.git .deployer
fi

if [ ! -z $(docker ps -aq --filter "name=scrapyd-seed") ]; then
  docker rm -f $(docker ps -aq --filter "name=scrapyd-seed")
fi

cat > ./Dockerfile.tmp <<EOF
FROM cgswong/aws:s3cmd
MAINTAINER dick <noreply@shunyet.com>
COPY ./seed.sh /
ENTRYPOINT /seed.sh
EOF

.deployer/ecr-build-and-push.sh ./Dockerfile.tmp scrapyd-seed:latest

rm ./Dockerfile.tmp
