#! /bin/bash

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


########################################################################################################################
# Echo message to stderr and exit the script with failure status code
# exitWithError (message) (error code)
########################################################################################################################
function exit_with_error_code () {
    >&2 echo "$1"
    exit "$2"
}

########################################################################################################################
# Parse arguments passed to the script
# -f flag (required) gives the output filename
# -s and -e flags (optional) require a date to be given (YYYYMMDD format -- Assumes that parameter dates match site timezone)
# -h flag calls help and terminates the script
# parse_args (OPTARG)
########################################################################################################################
function parse_args () {
    # Declare local OPTIND so global OPTIND is not affected by this function
    local OPTIND=1
    while getopts s:e:f:h option
    do
        case "${option}"
        in
            h) IS_SHOW_HELP=true;;
            s) START_DATE_PARAM=${OPTARG};;
            e) END_DATE_PARAM=${OPTARG};;
            f) OUTPUT_FILE_NAME_AND_PATH_PARAM=${OPTARG};;
        esac
    done
}

########################################################################################################################
# Displays help message for script on stdout
# show_help
########################################################################################################################
function show_help () {
    echo "Generates Emergency Inspection report in CSV format. Script requires an output filename. Results can optionally be filtered on a start date and/or an end date."
    echo -e "\tIf FRONTRUNNER_LOG_DIR environment variable has not been set, script assumes execution from /opt/frontrunner//frontrunnerV3/bin/ directory and searches /opt/frontrunner/frontrunnerV3/logs/ directory."
    echo -e "\tRequired flag:"
    echo -e "\t\t-f Filename (for output file)-- Script fails if target filename already exists or if target directory is inaccessible, nonexistent, or matches the FrontRunner logging directory."
    echo -e "\tOptional Flags:"
    echo -e "\t\t-h Help -- Displays this help message. This flag overrides all other flags."
    echo -e "\t\t-s Start Date -- Filters results to only include inspection events after the given date, inclusive. Start date is assumed to be in the same timezone as the log values."
    echo -e "\t\t\tYYYYMMDD format (Ex: 20200120). Start Date must come before End Date. Jan 01, 1970 is used as default if no value is supplied."
    echo -e "\t\t-e End Date -- Filters results to only include inspection events before the given date, inclusive. End date is assumed to be in the same timezone as the log values."
    echo -e "\t\t\tYYYYMMDD format (Ex: 20200125). End Date must come after Start Date. Current system date is used as default if no value is supplied."
    echo "Output filename may include absolute path, relative path, or just the filename."
    echo -e "\tIf a path is given that is inaccessible or cannot be written to, the script will report that it cannot access the path and fail."
    echo -e "\tIf no path is given, the file is output in the same directory where the script is executed."
    echo "Example calls:"
    echo -e "\temergencyInspectionReport.sh -h"
    echo -e "\t\t# Shows this help message."
    echo -e "\temergencyInspectionReport.sh -f outputFilename.csv"
    echo -e "\t\t# Generates report for all available server logs and outputs 'outputFilename.csv' file in current directory."
    echo -e "\temergencyInspectionReport.sh -s 20190425 -f StartReportFilename.csv"
    echo -e "\t\t# Generates report for available server logs after April 25, 2019 and outputs 'StartReportFilename.csv' file in the current directory."
    echo -e "\temergencyInspectionReport.sh -e 20200225 -f EndReportFilename.csv"
    echo -e "\t\t# Generates report for available server logs before February 2, 2020 and outputs 'EndReportFilename.csv' file in the current directory."
    echo -e "\temergencyInspectionReport.sh -s 20190425 -e 20200131 -f RangeReportFilename.csv"
    echo -e "\t\t# Generates report for available server logs between April 25, 2019 to January 31, 2020 and outputs 'RangeReportFilename.csv' file in the current directory."
    echo -e "\temergencyInspectionReport.sh -f ./path/from/outputFilename.csv"
    echo -e "\t\t# Generates report for all available server logs and outputs 'outputFilename.csv' file in the currentDir/path/from/ directory."
    echo -e "\temergencyInspectionReport.sh -f path/from/outputFilename.csv"
    echo -e "\t\t# Generates report for all available server logs and outputs 'outputFilename.csv' file in the currentDir/path/from/ directory."
    echo -e "\temergencyInspectionReport.sh -f /var/log/frontrunner/logs/outputFilename.csv"
    echo -e "\t\t# Generates report for all available server logs and outputs 'outputFilename.csv' file in the /var/log/frontrunner/logs/ directory."
}

########################################################################################################################
# Validate argument as a valid YYYYMMDD date
# validate_input_date (input date)
########################################################################################################################
function validate_input_date () {

    local ERROR_MESSAGE="Invalid date parameter ($1). Call 'emergencyInspectionReport.sh -h' for more information."
    local ERROR_CODE=7

    # Validate that input string is the correct general number format (00000000 to 99991939)
    if [[ ! $1 =~ ^[0-9]{4}[0-1][0-9][0-3][0-9]$ ]]; then
         exit_with_error_code "${ERROR_MESSAGE}" ${ERROR_CODE}
    fi

    # Try parsing valid date in YYYYMMDD format
    # Output of command is silently swallowed and $? is populated with the success/failure result of the call
    # $? is set to "0" if date command parses the date successfully
    date "+%Y%m%d" -d "$1" > /dev/null  2>&1
    local IS_INVALID_DATE=$?

    # Report failure and stop script if date is not in the correct format
    if [[ $IS_INVALID_DATE != "0" ]]; then
        exit_with_error_code "${ERROR_MESSAGE}" ${ERROR_CODE}
    fi
}

########################################################################################################################
# Parse start date and end date to Unix epoch seconds.
# parse_start_and_end_date (start date) (end date)
########################################################################################################################
function parse_start_and_end_date () {

    # If start date is empty, set to lowest Unix epoch time
    if [[ ! $1 ]]; then
        LOG_START_DATE=1
    else
        # If given, validate input then parse to current system timezone Unix epoch seconds (Ex: (JST) 20200115 -> 1579014000)
        validate_input_date "$1"
        LOG_START_DATE=$(date -d "$1" +%s)
    fi

    # If end date is empty, set to current system Unix epoch time
    if [[ ! $2 ]]; then
        LOG_END_DATE=$(date +%s)
    else
        # If given, validate input then parse to current system timezone Unix epoch seconds (Ex: (JST) 20200115 -> 1579014000)
        validate_input_date "$2"
        LOG_END_DATE=$(date -d "$2" +%s)
    fi
}
########################################################################################################################
# Get inspection result information from source file and append to target file
# get_and_append_inspection_info (source path and filename)
########################################################################################################################
function get_and_append_inspection_info () {

    # Loop through lines within file containing "Emergency button inspection performed" line
    while read -r matched_line ; do

        # Comma Split:                  $1     |      $2      |      $3       |                  $4                     |                  $5                   |           $6          |
        # standardized_matched_line: Source: T1, OperatorId: 9, Result: PASSED, Start Time: Fri May 15 08:41:36 JST 2020, End Time: Fri May 15 08:41:38 JST 2020, Duration: 00:00:02.203
        # Space Split:                 $1    $2|     $1     $2|   $1      $2  |  $1    $2   $3  $4  $5    $6    $7   $8 | $1   $2   $3  $4  $5    $6    $7   $8 |    $1           $2    |

        # Strip irrelevant data from beginning of matched_line
        local standardized_matched_line=$(echo "$matched_line" | sed -n 's/^.*Emergency button inspection performed: //p')
        # Split on comma (',') to separate fields, then split on space (' ') to get timezone and date from StartTime field
        local LOG_DATE=$(echo "$standardized_matched_line" | awk -F',' '{printf("%s", $4)}' | awk -F' ' '{printf("%s %s %s", $4, $5, $8)}')
        # Convert log entry date to current system timezone Unix epoch seconds for filtering purposes (Ex: (JST) Jan 01 2015 -> 1579014000)
        local FILTER_LOG_DATE=$(date -d "${LOG_DATE}" +%s)
        # Check that logged date is within filtered period
        if [[ "${FILTER_LOG_DATE}" -ge "${LOG_START_DATE}" ]] && [[ "${FILTER_LOG_DATE}" -le "${LOG_END_DATE}" ]] ; then
            # Formats Starting Timestamp (YYYY-MM-DD HH:MM:SS TZ) -- Split by comma (',') then space (' ')
            local FORMATTED_START_DATE=$(echo "$standardized_matched_line" | awk -F',' '{printf("%s", $4)}' | awk -F' ' '{printf("%s %s %s %s %s", $7, $4, $5, $8, $6)}')
            # Formats Start timestamp in site timezone to ISO format for output(YYYY-MM-DDTHH:MM:SS+/-HHMM): Ex: "JST Feb 25 2020 13:05:40" -> "2020-02-25T13:05:40+0900"
            local FORMATTED_START_DATE=$(date -d "$FORMATTED_START_DATE" -Is)
            # Formats Ending Timestamp (YYYY-MM-DD HH:MM:SS TZ) -- Split by comma (',') then space (' ')
            local FORMATTED_END_DATE=$(echo "$standardized_matched_line" | awk -F',' '{printf("%s", $5)}' | awk -F' ' '{printf("%s %s %s %s %s", $7, $4, $5, $8, $6)}')
            # Formats End timestamp in site timezone to ISO format for output (YYYY-MM-DDTHH:MM:SS+/-HHMM): Ex: "JST Feb 25 2020 13:05:40" -> "2020-02-25T13:05:40+0900"
            local FORMATTED_END_DATE=$(date -d "$FORMATTED_END_DATE" -Is)
            # Remaining fields -- Parse everything after first word (Source:, OperatorId:, Result:, Duration:) in fields and trim any leading or trailing whitespace
            # Ex: "Source: SOME EQUIPMENT, OperatorId: SOME OPERATOR ID, ..." -> $SOURCE="SOME EQUIPMENT", $OPERATOR="SOME OPERATOR ID", etc.
            local SOURCE=$(echo "$standardized_matched_line"   | awk -F',' '{print $1}' | awk -F' ' '{$1=""; print $0}' | awk '{$1=$1}1')
            local OPERATOR=$(echo "$standardized_matched_line" | awk -F',' '{print $2}' | awk -F' ' '{$1=""; print $0}' | awk '{$1=$1}1')
            local RESULT=$(echo "$standardized_matched_line"   | awk -F',' '{print $3}' | awk -F' ' '{$1=""; print $0}' | awk '{$1=$1}1')
            local DURATION=$(echo "$standardized_matched_line" | awk -F',' '{print $6}' | awk -F' ' '{$1=""; print $0}' | awk '{$1=$1}1')
            # Output CSV-formatted line to file: Source,OperatorId,Result,StartTime,EndTime,Duration
            echo "$SOURCE,$OPERATOR,$RESULT,$FORMATTED_START_DATE,$FORMATTED_END_DATE,$DURATION" >> ${OUTPUT_FILE_NAME_AND_PATH_PARAM}
            # Increment counter for number of records matched
            ((MATCHED_RECORD_COUNT++))
        fi
    # zgrep with -h flag to output matched line to $matched_line variable for *.dbg.zip or *.dbg files
    done < <(zgrep -h "Emergency button inspection performed" "$1")
}
########################################################################################################################
# Check if given filename falls within filtered range. If it does, filter contents to output CSV.
# filter_on_file_name (source path and filename)
########################################################################################################################
function filter_on_file_name () {

    # Call basename to strip any leading path from argument
    local FILE_FULL_NAME=$(basename "$1")
    # Strip filename to only include the date (YYYY-MM-DD format)
    local FILE_NAME_DATE=$(echo ${FILE_FULL_NAME} | grep -Eo '[[:digit:]]{4}-[[:digit:]]{2}-[[:digit:]]{2}')
    # Convert filename's date to current system timezone Unix epoch seconds for filtering (Ex: (JST) 2020-01-15 -> 1579014000)
    local FILE_DATE=$(date -d "${FILE_NAME_DATE}" +%s)
    # Only parse file if date is within acceptable range
    if [[ "${FILE_DATE}" -ge "${LOG_START_DATE}" ]] && [[ "${FILE_DATE}" -le "${LOG_END_DATE}" ]] ; then
        get_and_append_inspection_info "$1"
    fi
}

########################################################################################################################
# Script Start
########################################################################################################################
# Parse arguments passed to script.
parse_args "$@"

# Show help and exit if -h flag is present.
if [[ ${IS_SHOW_HELP} ]]; then
    show_help
    exit 0
fi

# Exit with error if only a directory was provided.
if [[ -d "${OUTPUT_FILE_NAME_AND_PATH_PARAM}" ]] ; then
    exit_with_error_code "Output parameter must provide a filename. $OUTPUT_FILE_NAME_AND_PATH_PARAM is a directory. Call 'emergencyInspectionReport.sh -h' for more information." 1
fi

# Exit with error if output filename was not provided.
if [[ ! ${OUTPUT_FILE_NAME_AND_PATH_PARAM} ]] ; then
    exit_with_error_code "Output filename must be provided. Call 'emergencyInspectionReport.sh -h' for more information." 2
fi

# Set FRONTRUNNER_LOG_DIR to default logs/ directory (/var/log/frontrunner/frontrunnerV3/logs/ for ubuntu base image) if FRONTRUNNER_LOG_DIR has not been set.
if [[ ! ${FRONTRUNNER_LOG_DIR} ]]; then
    FRONTRUNNER_LOG_DIR="$(dirname $0)/../logs/"
fi

# Exit with error if target file already exists.
if [[ -f ${OUTPUT_FILE_NAME_AND_PATH_PARAM} ]]; then
    exit_with_error_code "Output filename ${OUTPUT_FILE_NAME_AND_PATH_PARAM} already exists. Call 'emergencyInspectionReport.sh -h' for more information." 3
fi

# Get target output directory.
OUTPUT_FILE_PATH=$(dirname "${OUTPUT_FILE_NAME_AND_PATH_PARAM}")

# Exit with error if target directory doesn't exist, is inaccessible, or cannot be written to.
if [[ ! -d ${OUTPUT_FILE_PATH} || ! -x ${OUTPUT_FILE_PATH}  || ! -w ${OUTPUT_FILE_PATH} ]]; then
    exit_with_error_code "Directory '${OUTPUT_FILE_PATH}' does not exist, is inaccessible, or cannot be written to. Call 'emergencyInspectionReport.sh -h' for more information." 4
fi

# Get absolute paths of output and FRONTRUNNER_LOG_DIR for comparison
# FRONTRUNNER_LOG_DIR should be an absolute path, but check just to be safe
ABSOLUTE_OUTPUT_FILE_PATH=$(realpath "$OUTPUT_FILE_PATH")
ABSOLUTE_FRONTRUNNER_LOG_DIR=$(realpath "$FRONTRUNNER_LOG_DIR")

# Exit with error if target directory matches FRONTRUNNER_LOG_DIR directory.
# This is to prevent naming the output file *.dbg and causing script to recursively access the output file
# (which has a different format from the input files)
if [[ "${ABSOLUTE_FRONTRUNNER_LOG_DIR}" == "${ABSOLUTE_OUTPUT_FILE_PATH}" ]] ; then
    exit_with_error_code "Target output directory '${OUTPUT_FILE_PATH}' cannot match configured FRONTRUNNER_LOG_DIR (${FRONTRUNNER_LOG_DIR}). Call 'emergencyInspectionReport.sh -h' for more information." 5
fi

# Parse input start and end dates.
parse_start_and_end_date "${START_DATE_PARAM}" "${END_DATE_PARAM}"

# Exit with error if start date is after end date.
if [[ ${LOG_START_DATE} -gt ${LOG_END_DATE} ]]; then
    exit_with_error_code "Start date must come before end date. Call 'emergencyInspectionReport.sh -h' for more information." 6
fi

MATCHED_RECORD_COUNT=0

# Create output file with CSV header
OUTPUT_CSV_HEADER="Source,OperatorId,Result,StartTime,EndTime,Duration"
echo -e "${OUTPUT_CSV_HEADER}" > ${OUTPUT_FILE_NAME_AND_PATH_PARAM}

# Ensure FRONTRUNNER_LOG_DIR variable has tailing '/'
case "${FRONTRUNNER_LOG_DIR}" in
    */)
        # Ends with "/".
        ;;
    *)
        # Not end with "/".  Add "/" at tail.
        FRONTRUNNER_LOG_DIR="${FRONTRUNNER_LOG_DIR}/"
        ;;
esac

# Loop through all *.dbg.zip files in first level of FRONTRUNNER_LOG_DIR (monthly) subdirectories, filter based on
# filename, then parse filtered files for Emergency Inspection log entries.
shopt -s nullglob
for dir in ${FRONTRUNNER_LOG_DIR}*/ ; do
    shopt -s nullglob
    for subdirectory_file in ${dir}/*.dbg.zip ; do
        filter_on_file_name "${subdirectory_file}"
    done
done

# Loop through all *.dbg files in FRONTRUNNER_LOG_DIR directory and parse for Emergency Inspection log entries.
shopt -s nullglob
for directory_file in ${FRONTRUNNER_LOG_DIR}/*.dbg ; do
    get_and_append_inspection_info "${directory_file}"
done

# Remove generated header file and report if no records were output to file
if [[ ${MATCHED_RECORD_COUNT} -eq 0 ]] ; then
    echo "No matching records found."
    rm -f "${OUTPUT_FILE_NAME_AND_PATH_PARAM}"
# Report successful file creation if records were added to file
else
    echo "$MATCHED_RECORD_COUNT records found. CSV file created at ${OUTPUT_FILE_NAME_AND_PATH_PARAM}"
fi

# Exit with success code
exit 0
