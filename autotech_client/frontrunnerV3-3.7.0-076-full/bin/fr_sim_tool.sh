#!/bin/sh

groups | grep -q sudo
if [ $? -ne 0 ]; then
  if [ ! "$USER" = "root" ]; then
    if [ ! "$USER" = "komatsu" ]; then
      if [ ! "$USER" = "mms" ]; then
        if [ ! "$USER" = "dlog" ]; then
          sudo -l -U $USER | grep -q "(ALL : ALL) ALL"
          if [ $? -ne 0 ]; then
            echo "This command may only be run by a user in the super user group"
            exit
          fi
        fi
      fi
    fi
  fi
fi


if [[ -z "${SERVER_ADDR}" ]] ; then
    echo -e "export SERVER_ADDR as IP address of the FrontRunner server to connect."
    SERVER_ADDR="SERVER_ADDR"
fi
if [[ -z "${BCAST_ADDR}" ]] ; then
    echo -e "export BCAST_ADDR as broadcast address of the FrontRunner network."
    BCAST_ADDR="BCAST_ADDR"
fi
if [[ -z "${NETMASK}" ]] ; then
    echo -e "export NETMASK as Netmask of the FrontRunner network."
    NETMASK="NETMASK"
fi

export CMD_START="start"
export CMD_START_AND_WAIT="start_and_wait"
export CMD_CONSOLE="console"
export CMD_DEFAULT=$CMD_START

function usage_fr_start_virtual_equipment() {
    echo -e "USAGE: fr_start_virtual_equipment equipment_name number_of_gnss_antenna [$CMD_START|$CMD_CONSOLE(default:$CMD_DEFAULT)]"
    echo -e "    equipment_name: The name of the equipment, i.e., T1, EMV1, CRUSH1 and so on."
    echo -e "    number_of_gnss_antenna: ONE, TWO or NONE"
}
function fr_start_virtual_equipment() {
    EQMT_NAME=$1
    shift 1
    NUM_GNSS_ANTENNNA=$1
    shift 1
    COMMAND=$*
    case X$COMMAND in
        X$CMD_START|X$CMD_START_AND_WAIT|X$CMD_CONSOLE)
            ;;
        *)
            if [[ ! -z $COMMAND ]] ; then
                echo Unknown command: $COMMAND
            fi
            COMMAND=$CMD_DEFAULT
            echo Launching as default command: $COMMAND
            ;;
    esac

    case X$NUM_GNSS_ANTENNNA in
        XNONE)
            echo Starting equipment without GNSS: $EQMT_NAME
            frontrunner $COMMAND embedded -Dfrontrunner.embedded.id=$EQMT_NAME -Dgps.adapter.type=NONE
            ;;
        XONE)
            echo Starting equipment with Single-GNSS: $EQMT_NAME
            frontrunner $COMMAND embedded -Dfrontrunner.embedded.id=$EQMT_NAME -Dgps.adapter.type=UDP_ADAPTER -Dgps.antenna.count=ONE -Dfrontrunner.crcontrollers.adapter.type=MEM
            ;;
        XTWO)
            echo Starting equipment with Dual-GNSS: $EQMT_NAME
            frontrunner $COMMAND embedded -Dfrontrunner.embedded.id=$EQMT_NAME -Dgps.adapter.type=UDP_ADAPTER -Dgps.antenna.count=TWO -Dfrontrunner.crcontrollers.adapter.type=MEM
            ;;
        *)
            if [[ ! -z $NUM_GNSS_ANTENNNA ]] ; then
                echo No such number of GNSS antenna : $NUM_GNSS_ANTENNNA
            fi
            usage_fr_start_virtual_equipment
    esac
}

function usage_fr_start_virtual_remote_console() {
    echo -e "USAGE: fr_start_virtual_remote_console equipment_name [$CMD_START|$CMD_CONSOLE(default:$CMD_DEFAULT)]"
    echo -e "    equipment_name: The name of the equipment, i.e., SHOV1 and so on."
}
function fr_start_virtual_remote_console() {
    EQMT_NAME=$1
    shift 1
    COMMAND=$*
    case X$COMMAND in
        X$CMD_START|X$CMD_START_AND_WAIT|X$CMD_CONSOLE)
            ;;
        *)
            if [[ ! -z $COMMAND ]] ; then
                echo Unknown command: $COMMAND
            fi
            COMMAND=$CMD_DEFAULT
            echo Launching as default command: $COMMAND
            ;;
    esac

    echo Starting Remote Console: $EQMT_NAME
    frontrunner $COMMAND embedded -Dfrontrunner.embedded.id=$EQMT_NAME -Dgps.adapter.type=NONE -Dfrontrunner.remote.equipment=true
}

# By launcher icon on desktop.
# This won't be necessary.
#function fr_start_server() {
#    COMMAND=$*
#    case X$COMMAND in
#        X$CMD_START|X$CMD_START_AND_WAIT|X$CMD_CONSOLE)
#            ;;
#        *)
#            if [[ ! -z $COMMAND ]] ; then
#                echo Unknown command: $COMMAND
#            fi
#            COMMAND=$CMD_DEFAULT
#            echo Launching as default command: $COMMAND
#            ;;
#    esac
#
#    frontrunner $COMMAND server -Dgps.adapter.type=UDP_ADAPTER -Dgps.antenna.count=ONE
#}
function fr_start_controller() {
    COMMAND=$*
    case X$COMMAND in
        X$CMD_START|X$CMD_START_AND_WAIT|X$CMD_CONSOLE)
            ;;
        *)
            if [[ ! -z $COMMAND ]] ; then
                echo Unknown command: $COMMAND
            fi
            COMMAND=$CMD_DEFAULT
            echo Launching as default command: $COMMAND
            ;;
    esac

    frontrunner $COMMAND controller
}

function fr_print_gnss_sim_examples() {
    echo -e "GNSS Reference Station (with correctly configured MMSDOMAIN)"
    echo -e "\tgpsgssim"
    echo -e "GNSS Reference Station (without MMSDOMAIN)"
    echo -e "\tgpsgssim $BCAST_ADDR $NETMASK"
    echo -e "GNSS Monitor"
    echo -e "\tgpssim -mon"
    echo -e "GNSS for virtual vehicle (refer to frontrunner-sim.properties)"
    echo -e "\tgpssim [vehicle-name]"
}

alias fr_admin="frontrunner admin"


echo -e "################################################################"
echo -e "####  frontrunner commands:"
for f in `alias | grep -e "alias fr_sta" -e "alias fr_admin" | cut -c7- | sed -e "s/=.*//g"`; do
    echo -e "####\t$f"
done
for f in `set | grep -e "^fr" | sed -e "s@\s*()@@g"`; do
    echo -e "####\t$f"
done
echo -e "################################################################"
