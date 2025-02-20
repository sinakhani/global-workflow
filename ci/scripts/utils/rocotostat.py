#!/usr/bin/env python3

import sys
import os

from wxflow import Executable, which, Logger, CommandNotFoundError
from argparse import ArgumentParser, FileType

logger = Logger(level=os.environ.get("LOGGING_LEVEL", "DEBUG"), colored_log=False)


def input_args():
    """
    Parse command-line arguments.

    Returns
    -------
    args : Namespace
        The parsed command-line arguments.
    """

    description = """
        Using rocotostat to get the status of all jobs this scripts
        determines rocoto_state: if all cycles are done, then rocoto_state is Done.
        Assuming rocotorun had just been run, and the rocoto_state is not Done, then
        rocoto_state is Stalled if there are no jobs that are RUNNING, SUBMITTING, or QUEUED.
        """

    parser = ArgumentParser(description=description)

    parser.add_argument('-w', help='workflow_document', type=FileType('r'), required=True)
    parser.add_argument('-d', help='database_file', metavar='Database File', type=FileType('r'), required=True)
    parser.add_argument('--verbose', action='store_true', help='List the states and the number of jobs that are in each', required=False)
    parser.add_argument('-v', action='store_true', help='List the states and the number of jobs that are in each', required=False)
    parser.add_argument('--export', action='store_true', help='create and export list of the status values for bash', required=False)

    args = parser.parse_args()

    return args


def rocoto_statcount():
    """
    Run rocotostat and process its output.
    """

    args = input_args()

    try:
        rocotostat = which("rocotostat")
    except CommandNotFoundError:
        logger.exception("rocotostat not found in PATH")
        raise CommandNotFoundError("rocotostat not found in PATH")

    rocotostat_all = which("rocotostat")
    rocotostat.add_default_arg(['-w', os.path.abspath(args.w.name), '-d', os.path.abspath(args.d.name), '-s'])
    rocotostat_all.add_default_arg(['-w', os.path.abspath(args.w.name), '-d', os.path.abspath(args.d.name), '-a'])

    rocotostat_output = rocotostat(output=str)
    rocotostat_output = rocotostat_output.splitlines()[1:]
    rocotostat_output = [line.split()[0:2] for line in rocotostat_output]

    rocotostat_output_all = rocotostat_all(output=str)
    rocotostat_output_all = rocotostat_output_all.splitlines()[1:]
    rocotostat_output_all = [line.split()[0:4] for line in rocotostat_output_all]
    rocotostat_output_all = [line for line in rocotostat_output_all if len(line) != 1]

    rocoto_status = {
        'CYCLES_TOTAL': len(rocotostat_output),
        'CYCLES_DONE': sum([sublist.count('Done') for sublist in rocotostat_output])
    }

    status_cases = ['SUCCEEDED', 'FAIL', 'DEAD', 'RUNNING', 'SUBMITTING', 'QUEUED']
    for case in status_cases:
        rocoto_status[case] = sum([sublist.count(case) for sublist in rocotostat_output_all])

    return rocoto_status


if __name__ == '__main__':

    args = input_args()

    error_return = 0
    rocoto_status = rocoto_statcount()

    if rocoto_status['CYCLES_TOTAL'] == rocoto_status['CYCLES_DONE']:
        rocoto_state = 'DONE'
    elif rocoto_status['DEAD'] > 0:
        error_return = rocoto_status['FAIL'] + rocoto_status['DEAD']
        rocoto_state = 'FAIL'
    elif 'UNKNOWN' in rocoto_status:
        error_return = rocoto_status['UNKNOWN']
        rocoto_state = 'UNKNOWN'
    elif rocoto_status['RUNNING'] + rocoto_status['SUBMITTING'] + rocoto_status['QUEUED'] == 0:
        #
        #  TODO for now a STALLED state will be just a warning as it can
        #  produce a false negative if there is a timestamp on a file dependency.
        #
        #   error_return = -3
        rocoto_state = 'STALLED'
    else:
        rocoto_state = 'RUNNING'

    rocoto_status['ROCOTO_STATE'] = rocoto_state

    if args.verbose or args.v:
        for status in rocoto_status:
            if args.v:
                print(f'{status}:{rocoto_status[status]}')
            else:
                print(f'Number of {status} : {rocoto_status[status]}')

    if args.export:
        for status in rocoto_status:
            print(f'export {status}={rocoto_status[status]}')
    else:
        print(rocoto_state)

    sys.exit(error_return)
