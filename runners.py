# Copyright The Linux Foundation
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
import os
import shutil

from config import saveConfig
from datatypes import ProjectRepoType, Status, Subproject
from repolisting import doRepoListingForProject, doRepoListingForGerritProject, doRepoListingForSubproject
from getcode import doGetRepoCodeForSubproject, doGetRepoCodeForGerritSubproject
from uploadcode import doUploadCodeForProject, doUploadCodeForSubproject
from runagents import doRunAgentsForSubproject

def doNextThing(scaffold_home, cfg, fdServer, prj_only, sp_only):
    for prj in cfg._projects.values():
        if prj_only == "" or prj_only == prj._name:
            retval = True
            while retval:
                retval = doNextThingForProject(scaffold_home, cfg, fdServer, prj, sp_only)

def updateProjectStatusToSubprojectMin(cfg, prj):
    minStatus = Status.MAX
    for sp in prj._subprojects.values():
        if sp._status.value < minStatus.value:
            minStatus = sp._status
    prj._status = minStatus

# Tries to do the next thing for this project. Returns True if
# accomplished something (meaning that we could call this again
# and possibly do the next-next thing), or False if accomplished
# nothing (meaning that we probably need to intervene).
def doNextThingForProject(scaffold_home, cfg, fdServer, prj, sp_only):
    # if GitHub project, go to subprojects
    if prj._repotype == ProjectRepoType.GITHUB:
        did_something = False
        for sp in prj._subprojects.values():
            if sp_only == "" or sp_only == sp._name:
                retval = True
                while retval:
                    retval = doNextThingForSubproject(scaffold_home, cfg, fdServer, prj, sp)
                    updateProjectStatusToSubprojectMin(cfg, prj)
                    saveConfig(scaffold_home, cfg)
                    if retval:
                        did_something = True
        return did_something

    # if GITHUB_SHARED project, check state to decide when to go to subprojects
    elif prj._repotype == ProjectRepoType.GITHUB_SHARED:
        did_something = False
        retval_prj = True
        while retval_prj:
            if prj._status == Status.START:
                # get repo listing at project level and see if we're good
                retval_prj = doRepoListingForProject(cfg, prj)
                saveConfig(scaffold_home, cfg)
                if retval_prj:
                    did_something = True
            # elif prj._status == Status.GOTCODE:
            #     # upload code to Fossology server
            #     retval_prj = doUploadCodeForProject(cfg, fdServer, prj)
            #     updateProjectStatusToSubprojectMin(cfg, prj)
            #     saveConfig(scaffold_home, cfg)
            #     if retval_prj:
            #         did_something = True
            else:
                retval_sp_all = False
                for sp in prj._subprojects.values():
                    if sp_only == "" or sp_only == sp._name:
                        retval = True
                        while retval:
                            retval = doNextThingForSubproject(scaffold_home, cfg, fdServer, prj, sp)
                            updateProjectStatusToSubprojectMin(cfg, prj)
                            saveConfig(scaffold_home, cfg)
                            if retval:
                                did_something = True
                                retval_sp_all = True
                if not retval_sp_all:
                    break
        return did_something

    elif prj._repotype == ProjectRepoType.GERRIT:
        did_something = False
        retval_prj = True
        while retval_prj:
            if prj._status == Status.START:
                # get repo listing at project level and see if we're good
                retval_prj = doRepoListingForGerritProject(cfg, prj)
                updateProjectStatusToSubprojectMin(cfg, prj)
                saveConfig(scaffold_home, cfg)
                if retval_prj:
                    did_something = True
            # elif prj._status == Status.GOTCODE:
            #     # upload code to Fossology server
            #     retval_prj = doUploadCodeForProject(cfg, fdServer, prj)
            #     updateProjectStatusToSubprojectMin(cfg, prj)
            #     saveConfig(scaffold_home, cfg)
            #     if retval_prj:
            #         did_something = True
            else:
                retval_sp_all = False
                for sp in prj._subprojects.values():
                    if sp_only == "" or sp_only == sp._name:
                        retval = True
                        while retval:
                            retval = doNextThingForGerritSubproject(scaffold_home, cfg, fdServer, prj, sp)
                            updateProjectStatusToSubprojectMin(cfg, prj)
                            saveConfig(scaffold_home, cfg)
                            if retval:
                                did_something = True
                                retval_sp_all = True
                if not retval_sp_all:
                    break
        return did_something

    else:
        print(f"Invalid project repotype for {prj._name}: {prj._repotype}")
        return False

# Tries to do the next thing for this subproject. Returns True if
# accomplished something (meaning that we could call this again
# and possibly do the next-next thing), or False if accomplished
# nothing (meaning that we probably need to intervene).
def doNextThingForSubproject(scaffold_home, cfg, fdServer, prj, sp):
    status = sp._status
    if status == Status.START:
        # get repo listing and see if we're good
        return doRepoListingForSubproject(cfg, prj, sp)
    elif status == Status.GOTLISTING:
        # get code and see if we're good
        return doGetRepoCodeForSubproject(cfg, prj, sp)
    elif status == Status.GOTCODE:
        # upload code and see if we're good
        return doUploadCodeForSubproject(cfg, fdServer, prj, sp)
    elif status == Status.UPLOADEDCODE:
        # upload code and see if we're good
        return doRunAgentsForSubproject(cfg, fdServer, prj, sp)

    else:
        print(f"Invalid status for {sp._name}: {sp._status}")
        return False


# Tries to do the next thing for this Gerrit subproject. Returns True if
# accomplished something (meaning that we could call this again and possibly do
# the next-next thing), or False if accomplished nothing (meaning that we
# probably need to intervene). Does not handle START case because that is
# handled at the project level.
def doNextThingForGerritSubproject(scaffold_home, cfg, fdServer, prj, sp):
    status = sp._status
    if status == Status.GOTLISTING:
        # get code and see if we're good
        return doGetRepoCodeForGerritSubproject(cfg, prj, sp)
    elif status == Status.GOTCODE:
        # upload code and see if we're good
        return doUploadCodeForSubproject(cfg, fdServer, prj, sp)
    elif status == Status.UPLOADEDCODE:
        # upload code and see if we're good
        return doRunAgentsForSubproject(cfg, fdServer, prj, sp)

    else:
        print(f"Invalid status for {sp._name}: {sp._status}")
        return False


