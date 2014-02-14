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

@file    BaseConnector.py
@author  Mic Bowman
@date    2013-12-03

BaseConnector is the base class for the connectors. It implements
world time and other functions common to all connectors.

"""

import os, sys
import logging

sys.path.append(os.path.join(os.environ.get("SUMO_HOME"), "tools"))
sys.path.append(os.path.join(os.environ.get("OPENSIM","/share/opensim"),"lib","python"))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "lib")))

import platform, time

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class BaseConnector :
           
    # -----------------------------------------------------------------
    def __init__(self, settings) :

        self.__Logger = logging.getLogger(__name__)

        # Get world time
        self.Interval =  float(settings["General"].get("Interval", 0.150))
        self.SecondsPerStep = float(settings["General"].get("SecondsPerStep", 2.0))
        self.StartTimeOfDay = float(settings["General"].get("StartTimeOfDay", 8.0))

        self.RealDayLength = 24.0 * self.Interval / self.SecondsPerStep

        self.Clock = time.time

        ## this is an ugly hack because the cygwin and linux
        ## versions of time.clock seem seriously broken
        if platform.system() == 'Windows' :
            self.Clock = time.clock

    # -----------------------------------------------------------------
    def GetWorldTime(self, currentstep) :
        return self.StartTimeOfDay + (currentstep * self.SecondsPerStep) / (24.0 * 60.0 * 60.0)

    # -----------------------------------------------------------------
    def GetWorldTimeOfDay(self, currentstep) :
        return self.GetWorldTime(currentstep) % 24.0

    # -----------------------------------------------------------------
    def GetWorldDay(self, currentstep) :
        return int(self.GetWorldTime(currentstep) / 24.0)
