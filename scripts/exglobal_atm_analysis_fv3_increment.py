#!/usr/bin/env python3
# exglobal_atm_analysis_fv3_increment.py
# This script creates an AtmAnalysis object
# and runs the increment method
# which converts the JEDI increment into an FV3 increment
import os

from wxflow import Logger, cast_strdict_as_dtypedict
from pygfs.task.atm_analysis import AtmAnalysis

# Initialize root logger
logger = Logger(level='DEBUG', colored_log=True)


if __name__ == '__main__':

    # Take configuration from environment and cast it as python dictionary
    config = cast_strdict_as_dtypedict(os.environ)

    # Instantiate the atm analysis task
    AtmAnl = AtmAnalysis(config)
    AtmAnl.init_fv3_increment()
    AtmAnl.fv3_increment()
