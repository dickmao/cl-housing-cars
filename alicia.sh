#!/bin/bash

me=$(whoami)
name=$1
mailto=${2:-}
export PATH=/home/${me}/.local/bin:/home/${me}/.local/bin:/home/${me}/.go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/usr/lib/jvm/java-8-oracle/bin:/usr/lib/jvm/java-8-oracle/db/bin:/usr/lib/jvm/java-8-oracle/jre/bin:/usr/share/idea-IC-145.971.21/bin:/usr/share/idea-IC-141.1532.4/bin:/opt/android-sdk-linux/platforms:/opt/android-sdk-linux/tools:/opt/android-studio/bin:/usr/share/idea-IC-145.971.21/bin:/usr/share/idea-IC-141.1532.4/bin:/opt/android-sdk-linux/platforms:/opt/android-sdk-linux/tools:/opt/android-studio/bin:$PATH
cd ~/scrapy
scrapy crawl $name 
NAME=$name sh -c "jupyter nbconvert --ExecutePreprocessor.timeout=300 --stdout --execute dedupe.ipynb"
if [ $? == 0 ]; then
    if [ -e $name/marker1 ]; then 
        mv $name/marker1 $name/marker0
    fi
    if [ -s "$name/digest" -a $me == 'ubuntu' ]; then
        DATE=`date '+%Y%m%d'` sh -c "mailx -s \"digest \$DATE\" -r \"Daily Digest <no-reply@shunyet.com>\" -q $name/digest $mailto rchiang@cs.stonybrook.edu </dev/null"
    fi
fi
