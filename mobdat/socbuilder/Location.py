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

@file    SocBuilder.py
@author  Mic Bowman
@date    2014-02-04

This file defines routines used to build profiles for people and places.

"""

import os, sys
import logging

# we need to import python modules from the $SUMO_HOME/tools directory
sys.path.append(os.path.join(os.environ.get("OPENSIM","/share/opensim"),"lib","python"))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "lib")))

import random

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
def restrict (val, minval, maxval):
    if val < minval: return minval
    if val > maxval: return maxval
    return val

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class Location :

    # -----------------------------------------------------------------
    def __init__(self) :
        pass

    # -----------------------------------------------------------------
    def Dump(self) :
        result = dict()
        return result

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class BusinessLocationProfile :
    # -----------------------------------------------------------------
    def __init__(self, name, employees = 20, customers = 50, types = {}) :
        self.ProfileName = name
        self.EmployeesPerNode = employees
        self.CustomersPerNode = customers
        self.PreferredBusinessTypes = types

    # -----------------------------------------------------------------
    def Fitness(self, business) :
        btype = business.Profile.BusinessType
        return self.PreferredBusinessTypes[btype] if btype in self.PreferredBusinessTypes else 0.0

    # -----------------------------------------------------------------
    def Dump(self) :
        result = dict()
        result['Profile'] = self.ProfileName
        result['EmployeesPerNode'] = self.EmployeesPerNode
        result['CustomersPerNode'] = self.CustomersPerNode
        result['PreferredBusinessTypes'] = self.PreferredBusinessTypes        

        return result

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class ResidentialLocationProfile :
    # -----------------------------------------------------------------
    def __init__(self, residents = 5) :
        self.ResidentsPerNode = residents
        self.TargetSalary = 0

    # -----------------------------------------------------------------
    def Fitness(self, resident) :
        return 1

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class BusinessLocation(Location) :

    # -----------------------------------------------------------------
    def __init__(self, capsule, profile) :
        Location.__init__(self)

        self.Capsule = capsule
        self.LocationProfile = profile
        self.Residents = []
        self.PeakEmployeeCount = 0
        self.PeakCustomerCount = 0
        self.EmployeeCapacity = len(capsule.Members) * self.LocationProfile.EmployeesPerNode
        self.CustomerCapacity = len(capsule.Members) * self.LocationProfile.CustomersPerNode

    # -----------------------------------------------------------------
    @property
    def SourceName(self) :
        node = random.choice(self.Capsule.Members)
        return node.EndPoint.SourceName

    # -----------------------------------------------------------------
    @property
    def DestinationName(self) :
        node = random.choice(self.Capsule.Members)
        return node.EndPoint.DestinationName

    # -----------------------------------------------------------------
    def Fitness(self, business) :
        ecount = self.PeakEmployeeCount + business.PeakEmployeeCount
        ccount = self.PeakCustomerCount + business.PeakCustomerCount

        if ecount >= self.EmployeeCapacity : return 0
        if ccount >= self.CustomerCapacity : return 0

        invweight = (ecount / self.EmployeeCapacity + ccount / self.CustomerCapacity) / 2.0
        fitness = restrict(random.gauss(1.0 - invweight, 0.1), 0, 1.0) * self.LocationProfile.Fitness(business) 
        return fitness

    # -----------------------------------------------------------------
    def AddBusiness(self, business) :
        self.PeakEmployeeCount += business.PeakEmployeeCount
        self.PeakCustomerCount += business.PeakCustomerCount
        self.Residents.append(business)

    # -----------------------------------------------------------------
    def Dump(self) :
        result = Location.Dump(self)
        result['Capsule'] = self.Capsule.Name
        result['LocationProfile'] = self.LocationProfile.ProfileName
        
        result['Residents'] = []
        for b in self.Residents :
            result['Residents'].append(b.Name)

        return result

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class ResidentialLocation(Location) :

    # -----------------------------------------------------------------
    def __init__(self, capsule, profile) :
        Location.__init__(self)

        self.Capsule = capsule
        self.ResidentialProfile = profile
        self.Residents = {}
        self.Capacity = len(capsule.Members) * self.ResidentialProfile.ResidentsPerNode

    # -----------------------------------------------------------------
    def Fitness(self, business) :
        ecount = self.PeakEmployeeCount + business.PeakEmployeeCount
        ccount = self.PeakCustomerCount + business.PeakCustomerCount

        invweight = (ecount / self.EmployeeCapacity + ccount / self.CustomerCapacity) / 2.0
        return restrict(random.gauss(1.0 - invweight, 0.1), 0, 1.0)

    # -----------------------------------------------------------------
    def AddBusiness(self, business) :
        self.PeakEmployeeCount += business.PeakEmployeeCount
        self.PeakCustomerCount += business.PeakCustomerCount
        self.Residents.append(business)

    
