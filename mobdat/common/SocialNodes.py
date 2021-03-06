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

@file    LayoutInfo.py
@author  Mic Bowman
@date    2013-12-03

This file defines routines used to build features of a mobdat traffic
network such as building a grid of roads. 

"""

import os, sys
import logging

# we need to import python modules from the $SUMO_HOME/tools directory
sys.path.append(os.path.join(os.environ.get("OPENSIM","/share/opensim"),"lib","python"))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "lib")))

from mobdat.common import Graph, Decoration, SocialDecoration
from mobdat.common.Utilities import GenName

logger = logging.getLogger(__name__)

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class PersonProfile(Graph.Node) :

    # -----------------------------------------------------------------
    def __init__(self, name) :
        """
        Args:
            name -- string name 
        """
        Graph.Node.__init__(self, name = name)
        self.AddDecoration(SocialDecoration.VehicleTypeDecoration())

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class Person(Graph.Node) :

    # -----------------------------------------------------------------
    def __init__(self, name, profile) :
        """
        Args:
            name -- string name 
        """
        Graph.Node.__init__(self, name = name)

        profile.AddMember(self)

    # -----------------------------------------------------------------
    def SetJob(self, job) :
        """
        Args:
            job -- object of type SocialDecoration.JobDescription
        """
        self.AddDecoration(SocialDecoration.JobDescriptionDecoration(job))

    # -----------------------------------------------------------------
    def SetVehicle(self, vehicletype) :
        """
        Args:
            job -- object of type SocialDecoration.JobDescription
        """
        name = GenName('veh' + vehicletype)
        self.AddDecoration(SocialDecoration.VehicleDecoration(name, vehicletype))

        return name

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class BusinessProfile(Graph.Node) :

    # -----------------------------------------------------------------
    def __init__(self, name, biztype, joblist) :
        """
        Args:
            name -- string name of the profile
            biztype -- constant of type SocialDecoration.BusinessType
            joblist -- dictionary mapping type SocialDecoration.JobDescription --> Demand
        """
        Graph.Node.__init__(self, name = name)

        self.AddDecoration(SocialDecoration.BusinessProfileDecoration(biztype))
        self.AddDecoration(SocialDecoration.EmploymentProfileDecoration(joblist))

    # -----------------------------------------------------------------
    def AddServiceProfile(self, bizhours, capacity, servicetime) :
        """
        Args:
            bizhours -- object of type WeeklySchedule
            capacity -- integer maximum customer capacity
            servicetime -- float mean time to service a customer
        """
        self.AddDecoration(SocialDecoration.ServiceProfileDecoration(bizhours, capacity, servicetime))

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class Business(Graph.Node) :

    # -----------------------------------------------------------------
    def __init__(self, name, profile) :
        """
        Args:
            name -- string name of the business
            profile -- object of type SocialNodes.BusinessProfile
        """
        Graph.Node.__init__(self, name = name)

        profile.AddMember(self)


## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Nodes = [ PersonProfile, Person, BusinessProfile, Business ]
