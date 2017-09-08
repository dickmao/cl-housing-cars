#!/bin/bash

me=$(whoami)
name=${1:-dmoz}
export PATH=/home/${me}/.local/bin:/home/${me}/.local/bin:/home/${me}/.go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/usr/lib/jvm/java-8-oracle/bin:/usr/lib/jvm/java-8-oracle/db/bin:/usr/lib/jvm/java-8-oracle/jre/bin:/usr/share/idea-IC-145.971.21/bin:/usr/share/idea-IC-141.1532.4/bin:/opt/android-sdk-linux/platforms:/opt/android-sdk-linux/tools:/opt/android-studio/bin:/usr/share/idea-IC-145.971.21/bin:/usr/share/idea-IC-141.1532.4/bin:/opt/android-sdk-linux/platforms:/opt/android-sdk-linux/tools:/opt/android-studio/bin:$PATH
DIR="/home/$me/scrapy/${name}"
MARKER0="$DIR/marker0"
if [ -e "$MARKER0" ] ; then
    file=$(find -L $DIR -regex .*\.json ! -newermt @$(date -d "1970-01-01 UTC +$(stat -Lc %Y ${MARKER0}) seconds - 23 hours" +%s) -printf '%Ts\t%p\n' | sort -nr | cut -f2 | head -1)
    if [ ! -z $file ]; then
	mark=$(cat $file | perl -ne '/\/(\d+)\.html/; print "$1\n"; '|sort -nr | head -1)
	if [ ! -z $mark ]; then
	    cat $MARKER0 | perl -ne "/\/(\d+)\.html/; print \"\$_\n\" if \$1 > $mark"
	fi
    fi
fi
