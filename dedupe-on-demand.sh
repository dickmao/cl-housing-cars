#!/bin/bash -ex

WDIR=$(dirname $0)
PROJECT=tutorial
ITEMDIR=/var/lib/scrapyd/items/${PROJECT}


while [ 1 ] ; do
    for spider in $(scrapyd-client spiders -p ${PROJECT} | tail -n +2) ; do
        if [ -e ${ITEMDIR}/${spider}/digest ] && [[ ! -z $(find -L ${ITEMDIR}/${spider} -name Marker.*\.json -cnewer ${ITEMDIR}/${spider}/digest) ]]; then
            ${WDIR}/dedupe.py ${ITEMDIR}/${spider}
        fi
    done
    sleep 30
done
