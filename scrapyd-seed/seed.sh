#!/bin/bash -ex

IFS=$'\n'
for bf in $(s3cmd ls) ; do
    buck=${bf##* }
    spider=${buck##*.} 
    dir=/var/lib/scrapyd/items/tutorial/$spider
    rm -f $dir/{digest,reject}
    mf=$(s3cmd ls $buck/Marker. | sort | tail -1)
    marker=${mf##* }
    if [ ! -z $marker ] && [ ! -e $dir/$(basename $marker) ] ; then
        mkdir -m 0775 -p $dir
        s3cmd get $marker $dir/
    fi
done
unset IFS
