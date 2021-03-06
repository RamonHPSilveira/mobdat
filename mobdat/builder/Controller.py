#!/usr/bin/env python
"""
Copyright (c) 2014, Intel Corporation

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer. 

* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution. 

* Neither the name of Intel Corporation nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission. 

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 

@file    Controller.py
@author  Mic Bowman
@date    2013-12-03

This module defines routines for controling the mobdat simulator. The controller
sets up the connectors and then drives the simulation through the periodic
clock ticks.

"""

import os, sys, traceback
import logging

sys.path.append(os.path.join(os.environ.get("OPENSIM","/share/opensim"),"lib","python"))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "lib")))

import json

from mobdat.common import LayoutSettings
from mobdat.builder import WorldBuilder, OpenSimBuilder, SumoBuilder

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------
# -----------------------------------------------------------------
def Controller(settings, pushlist) :
    """
    Controller is the main entry point for driving the network building process.

    Arguments:
    settings -- nested dictionary with variables for configuring the connectors
    """

    laysettings = LayoutSettings.LayoutSettings(settings)
    world = WorldBuilder.WorldBuilder()

    dbbindings = {"laysettings" : laysettings, "world" : world}

    for cf in settings["Builder"].get("ExtensionFiles",[]) :
        try :
            execfile(cf, dbbindings)
            logger.info('loaded extension file %s', cf)
        except :
            logger.warn('unhandled error processing extension file %s\n%s', cf, traceback.format_exc(10))
            sys.exit(-1)

    for push in pushlist :
        if push == 'opensim' :
            os = OpenSimBuilder.OpenSimBuilder(settings, world, laysettings)
            os.PushNetworkToOpenSim()
        elif push == 'sumo' :
            sc = SumoBuilder.SumoBuilder(settings, world, laysettings)
            sc.PushNetworkToSumo()

    # write the network information back out to the layinfo file
    infofile = settings["General"].get("WorldInfoFile","info.js")
    logger.info('saving world data to %s',infofile)

    with open(infofile, "w") as fp :
        json.dump(world.Dump(), fp, indent=2, ensure_ascii=True)
