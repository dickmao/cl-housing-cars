#!/bin/bash

me=$(whoami)
name=${1:-dmoz}
if [ -d $name ]; then
  DIR=$name
  name=$(basename $DIR)
else
  DIR="/home/$me/scrapy/${name}"
fi
MARKER1="$DIR/marker1"
MARKER0="$DIR/marker0"
if [ -h "$MARKER1" ] ; then
    DATA=$(readlink $MARKER1)
    if [ -e $DIR/$DATA ] ; then
	rm -f $DIR/$DATA
    fi
    if [ -e $DIR/Marker.${DATA#$name.} ] ; then
	rm -f $DIR/Marker.${DATA#$name.}
    fi
    rm -f $MARKER1
elif [ -h "$MARKER0" ] ; then
    DATA=$(readlink $MARKER0)
    if [ -e $DIR/$DATA ] ; then
	rm -f $DIR/$DATA
    fi
    if [ -e $DIR/Marker.${DATA#$name.} ] ; then
	rm -f $DIR/Marker.${DATA#$name.}
    fi
    rm -f $MARKER0
    ( cd $DIR ; \
      ln -s $(ls -1t $name.*.json | head -1) ./marker0; \
      )
fi
