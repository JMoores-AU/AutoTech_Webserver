#!/bin/bash

validate_frontrunner_server_status(){
    local running_processes_count=$(pgrep -f frontrunner.app.name=_server | wc -l)

    
    if [[ $? -ne 0 ]]; then
        >&2 echo "Error attempting to count active processes"        
        exit 1
    fi
    
    if [[ $running_processes_count -eq 0 ]]; then
        echo "FrontRunner server is not running"
        exit 0
    else
        >&2 echo "Error, $running_processes_count active process(es) of FrontRunner server was found"
        exit 1
    fi
}

validate_frontrunner_server_status
