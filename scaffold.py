# Copyright The Linux Foundation
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path
from operator import itemgetter
import os
import sys

from tabulate import tabulate

from config import loadConfig, saveBackupConfig, saveConfig
import datefuncs
from runners import doNextThing

def printUsage():
    print(f"")
    print(f"Usage: {sys.argv[0]} <month> <command> [<project>] [<subproject>]")
    print(f"Month: in format YYYY-MM")
    print(f"Commands:")
    print(f"  status:  Print status for all subprojects")
    print(f"  run:     Run next steps for all subprojects")
    print(f"  cleared: Flag cleared in Fossology for [sub]project")
    print(f"")

def status(projects, prj_only, sp_only):
    headers = ["Project", "Subproject", "Status"]
    table = []

    for prj in projects.values():
        if prj_only == "" or prj_only == prj._name:
            for sp in prj._subprojects.values():
                if sp_only == "" or sp_only == sp._name:
                    row = [prj._name, sp._name, sp._status.name]
                    table.append(row)

    table = sorted(table, key=itemgetter(0, 1))
    print(tabulate(table, headers=headers))

if __name__ == "__main__":
    # check and parse year-month
    if len(sys.argv) < 2:
        printUsage()
        sys.exit(1)
    year, month = datefuncs.parseYM(sys.argv[1])
    if year == 0 and month == 0:
        printUsage()
        sys.exit(1)

    # get scaffold home directory
    SCAFFOLD_HOME = os.getenv('SCAFFOLD_HOME')
    if SCAFFOLD_HOME == None:
        SCAFFOLD_HOME = os.path.join(Path.home(), "scaffold")
    MONTH_DIR = os.path.join(SCAFFOLD_HOME, f"{year}-{month}")

    ran_command = False

    # load configuration file for this month
    cfg_file = os.path.join(MONTH_DIR, "config.json")
    cfg = loadConfig(cfg_file)

    # we'll check if added optional args limit to one prj / sp
    prj_only = ""
    sp_only = ""

    if len(sys.argv) >= 3:
        month = sys.argv[1]
        command = sys.argv[2]
        if len(sys.argv) >= 4:
            prj_only = sys.argv[3]
            if len(sys.argv) >= 5:
                sp_only = sys.argv[4]

        if command == "status":
            ran_command = True
            status(cfg._projects, prj_only, sp_only)

        elif command == "run":
            ran_command = True
            saveBackupConfig(SCAFFOLD_HOME, cfg)

            # run commands
            doNextThing(SCAFFOLD_HOME, cfg, prj_only, sp_only)

            # save modified config file
            saveConfig(SCAFFOLD_HOME, cfg)

    if ran_command == False:
        printUsage()
        sys.exit(1)

