#!/bin/bash

me=$(whoami)
BEFORE=20
TOTALKB=$(df -k --total | tail -1 | awk '{print $2}')
ACTKB=$(expr $TOTALKB / 8)
DIR="/home/$me/scrapy"
for name in $(cat $DIR/crontab | egrep -v "^#" | cut -d' ' -f7); do
    MARKER0="$DIR/$name/marker0"
    if [ -e "$MARKER0" ] ; then
	# all files older than marker0 by BEFORE days
        files=$(find -L $DIR/$name/$name.*.json -type f ! -newermt @$(date -d "1970-01-01 UTC +$(stat -Lc %Y ${MARKER0}) seconds - $BEFORE days" +%s | sort))
	KB=$(du -ck $files | tail -1 | cut -f1)
	if [ "$KB" -gt "$ACTKB" ]; then
	    bfiles=$(for f in $files ; do basename $f ; done)
	    first=$(echo $bfiles | cut -d' ' -f1)
	    last=$(echo $bfiles | rev | cut -d' ' -f1 | rev)
	    if tar -C $DIR/$name -zcf $DIR/$name/$first..$last.tgz $bfiles; then
		rm -f $files
	    fi
	fi
    fi
done
