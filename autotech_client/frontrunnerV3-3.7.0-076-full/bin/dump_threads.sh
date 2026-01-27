#!/bin/bash

function full_thread_dump_java_process() {
    THE_PROCESS=$*
    #echo -e "PROCESS: <$THE_PROCESS>"

    # Put back separator to be default.
    IFS="   
"
    local PROCID=0
    local IS_JAVA=false
    local -i INDEX=0
    local COMMAND_LINE=
    for p in $THE_PROCESS; do
        #echo -e "\tDATA[$INDEX]: $p"
        if [[ $INDEX == 0 ]] ; then
            # PID
            PROCID=$p
        elif [[ $INDEX == 1 ]] ; then
            # program name
            COMMAND_LINE=$p
            if [[ "$p" == "java" ]] ; then
                IS_JAVA=true
            fi
        else
            COMMAND_LINE="$COMMAND_LINE $p"
        fi
        INDEX+=1
    done

    if [[ $IS_JAVA == true ]] ; then
        echo -e ""
        echo -e "##########################################"
        echo -e "#### FULL THREAD DUMP (PROC:$PROCID): $COMMAND_LINE"
        echo -e "##########################################"
        jstack $PROCID
#    else
#        echo -e ""
#        echo -e "Non-JAVA process: $COMMAND_LINE"
    fi
}
function full_thread_dump_all() {
    # Only separate with <newline>, and do not separate with <space> or <tab>
    IFS="
"
    for f in `ps axwo pid,args | grep java`; do
        full_thread_dump_java_process "$f"
    done

    # Put back separator to be default.
    IFS="   
"
}

if [[ "$OSTYPE" == "cygwin" ]] ; then
    echo -e "EXECUTING in CYGWIN terminal.....  Invoke dump_threads.bat!!"
    BATFILE=`echo $0 | sed -e s/sh/bat/`
    echo $BATFILE
    $BATFILE
else
    full_thread_dump_all
fi
