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

@file    LayoutDecoration.py
@author  Mic Bowman
@date    2013-12-03

This file defines routines used to build features of a mobdat traffic
network such as building a grid of roads. 

"""

import os, sys

# we need to import python modules from the $SUMO_HOME/tools directory
sys.path.append(os.path.join(os.environ.get("OPENSIM","/share/opensim"),"lib","python"))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "lib")))

import random

from mobdat.common.Decoration import Decoration, CommonDecorations

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
def restrict(value, vmax, vmin) :
    return vmin if value < vmin else (vmax if value > vmax else value)

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class CoordDecoration(Decoration) :
    """ Class -- CoordDecoration

    Decorate a node with an <X, Y> coordinate.
    """
    DecorationName = 'Coord'

    # -----------------------------------------------------------------
    @staticmethod
    def Load(graph, info) :
        return CoordDecoration(info['X'], info['Y'])

    # -----------------------------------------------------------------
    def __init__(self, x, y) :
        Decoration.__init__(self)

        self.X = x
        self.Y = y

    # -----------------------------------------------------------------
    def Dump(self) : 
        result = Decoration.Dump(self)

        result['X'] = self.X
        result['Y'] = self.Y

        return result

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class IntersectionTypeDecoration(Decoration) :
    DecorationName = 'IntersectionType'

    # -----------------------------------------------------------------
    @staticmethod
    def Load(graph, info) :
        return IntersectionTypeDecoration(info['Name'], info['IntersectionType'], info['Render'])

    # -----------------------------------------------------------------
    def __init__(self, name, itype = 'priority', render = True) :
        Decoration.__init__(self)

        self.Name = name
        self.IntersectionType = itype
        self.Render = render

    # -----------------------------------------------------------------
    def Dump(self) :
        result = Decoration.Dump(self)
        result['Name'] = self.Name
        result['IntersectionType'] = self.IntersectionType
        result['Render'] = self.Render

        return result

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class RoadTypeDecoration(Decoration) :
    DecorationName = 'RoadType'

    # -----------------------------------------------------------------
    @staticmethod
    def Load(graph, info) :
        etype = RoadTypeDecoration(info['Name'])

        etype.Lanes = info['Lanes']
        etype.Priority = info['Priority']
        etype.Speed = info['Speed']
        etype.Width = info['Width']
        etype.Signature = info['Signature']
        etype.Render = info['Render']
        etype.Center = info['Center']

        return etype

    # -----------------------------------------------------------------
    def __init__(self, name, lanes = 1, pri = 70, speed = 2.0, wid = 2.5, sig = '1L', render = True, center = False) :
        Decoration.__init__(self)
        self.Name = name
        self.Lanes = lanes
        self.Priority = pri
        self.Speed = speed
        self.Width = wid
        self.Signature = sig
        self.Render = render
        self.Center = center

    # -----------------------------------------------------------------
    def Dump(self) :
        result = Decoration.Dump(self)
        
        result['Name'] = self.Name
        result['Lanes'] = self.Lanes
        result['Priority'] = self.Priority
        result['Speed'] = self.Speed
        result['Width'] = self.Width
        result['Signature'] = self.Signature
        result['Render'] = self.Render
        result['Center'] = self.Center

        return result

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class EndPointDecoration(Decoration) :
    DecorationName = 'EndPoint'

    # -----------------------------------------------------------------
    @staticmethod
    def Load(graph, info) :
        return EndPointDecoration()

    # -----------------------------------------------------------------
    def __init__(self) :
        Decoration.__init__(self)

        # self.SourceName = sname
        # self.DestinationName = dname

    # -----------------------------------------------------------------
    @property
    def SourceName(self) :
        """Generate the name to be used when vehicles leave this node"""
        edges = self.HostObject.FindInputEdges('Road')

        return edges[0].Name

    # -----------------------------------------------------------------
    @property
    def DestinationName(self) :
        """Generate the name to be used for vehicles headed to this node"""
        return 'r' + self.HostObject.Name

    # -----------------------------------------------------------------
    def Dump(self) :
        return Decoration.Dump(self)

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class CapsuleDecoration(Decoration) :
    DecorationName = 'Capsule'

    # -----------------------------------------------------------------
    @staticmethod
    def Load(graph, info) :
        return CapsuleDecoration()

    # -----------------------------------------------------------------
    def __init__(self) :
        Decoration.__init__(self)

        
    # -----------------------------------------------------------------
    @property
    def EndPointCount(self) :
        return len(self.HostObject.Members)

    # -----------------------------------------------------------------
    @property
    def SourceName(self) :
        node = random.choice(self.HostObject.Members)
        return node.EndPoint.SourceName

    # -----------------------------------------------------------------
    @property
    def DestinationName(self) :
        node = random.choice(self.HostObject.Members)
        return node.EndPoint.DestinationName


## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class BusinessLocationProfileDecoration(Decoration) :
    DecorationName = 'BusinessLocationProfile'
    
    # -----------------------------------------------------------------
    @staticmethod
    def Load(graph, info) :
        epnode = info['EmployeesPerNode']
        cpnode = info['CustomersPerNode']
        btypes = info['PreferredBusinessTypes']  # should this be a copy?
        return BusinessLocationProfileDecoration(epnode, cpnode, btypes)

    # -----------------------------------------------------------------
    def __init__(self, employees = 20, customers = 50, types = None) :
        """
        Args:
            employees -- integer count of employee capacity
            customers -- integer count of customer capacity
            types -- dictionary mapping profiles
        """
        Decoration.__init__(self)

        self.EmployeesPerNode = employees
        self.CustomersPerNode = customers
        self.PreferredBusinessTypes = types or {}

    # -----------------------------------------------------------------
    def Fitness(self, business) :
        """
        Args:
            business -- an object of type LayoutInfo.Business
        """
        btype = business.BusinessProfile.BusinessType
        return self.PreferredBusinessTypes[btype] if btype in self.PreferredBusinessTypes else 0.0

    # -----------------------------------------------------------------
    def Dump(self) :
        result = Decoration.Dump(self)

        result['EmployeesPerNode'] = self.EmployeesPerNode
        result['CustomersPerNode'] = self.CustomersPerNode
        result['PreferredBusinessTypes'] = self.PreferredBusinessTypes        
        
        return result
    
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class BusinessLocationDecoration(Decoration) :
    """
    BusinessLocationDecoration
    
    This class decorates BusinessLocation objects 
    """

    DecorationName = 'BusinessLocation'

    # -----------------------------------------------------------------
    @staticmethod
    def Load(graph, info) :
        return BusinessLocationDecoration()

    # -----------------------------------------------------------------
    def __init__(self) :
        Decoration.__init__(self)

        self.PeakEmployeeCount = 0
        self.PeakCustomerCount = 0
        
    # -----------------------------------------------------------------
    @property
    def EndPointCount(self) :
        """
        EndPointCount -- return the total number of EndPoint nodes inside
        Capsule nodes assigned to the BusinessLocation
        """
        count = 0
        for capsule in self.HostObject.Members :
            count += capsule.Capsule.EndPointCount

        return count

    # -----------------------------------------------------------------
    @property
    def EmployeeCapacity(self) :
        return self.EndPointCount * self.HostObject.BusinessLocationProfile.EmployeesPerNode

    # -----------------------------------------------------------------
    @property
    def CustomerCapacity(self) :
        return self.EndPointCount * self.HostObject.BusinessLocationProfile.CustomersPerNode

    # -----------------------------------------------------------------
    def Fitness(self, business) :
        ecount = self.PeakEmployeeCount
        if business.FindDecorationProvider('EmploymentProfile') :
            ecount += business.EmploymentProfile.PeakEmployeeCount()

        ccount = self.PeakCustomerCount
        if business.FindDecorationProvider('ServiceProfile') :
            ccount += business.ServiceProfile.PeakServiceCount()

        if ecount >= self.EmployeeCapacity : return 0
        if ccount >= self.CustomerCapacity : return 0

        invweight = (ecount / self.EmployeeCapacity + ccount / self.CustomerCapacity) / 2.0
        pfitness = self.HostObject.BusinessLocationProfile.Fitness(business)
        fitness = restrict(random.gauss(1.0 - invweight, 0.1), 0, 1.0) * pfitness

        return fitness

    # -----------------------------------------------------------------
    def AddBusiness(self, business) :
        """
        AddBusiness -- assign a business to this location
        
        Args:
            business -- SocialNodes.Business
        """
        if business.FindDecorationProvider('EmploymentProfile') :
            self.PeakEmployeeCount += business.EmploymentProfile.PeakEmployeeCount()

        if business.FindDecorationProvider('ServiceProfile') :
            self.PeakCustomerCount += business.ServiceProfile.PeakServiceCount()

        # Return the capsule where the business is assigned, with BusinessLocation nodes
        # there should really only be one capsule
        return random.choice(self.HostObject.Members)

    # -----------------------------------------------------------------
    def Dump(self) :
        return Decoration.Dump(self)

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class ResidentialLocationProfileDecoration(Decoration) :
    DecorationName = 'ResidentialLocationProfile'
    
    # -----------------------------------------------------------------
    @staticmethod
    def Load(graph, info) :
        rpnode = info['ResidentsPerNode']
        return ResidentialLocationProfileDecoration(rpnode)

    # -----------------------------------------------------------------
    def __init__(self, residents = 5) :
        """
        Args:
            name -- string
            residents -- integer
        """

        Decoration.__init__(self)
        self.ResidentsPerNode = residents

    # -----------------------------------------------------------------
    def Fitness(self, resident) :
        return 1

    # -----------------------------------------------------------------
    def Dump(self) :
        result = Decoration.Dump(self)

        result['ResidentsPerNode'] = self.ResidentsPerNode
        
        return result
    

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class ResidentialLocationDecoration(Decoration) :
    DecorationName = 'ResidentialLocation'

    # -----------------------------------------------------------------
    @staticmethod
    def Load(graph, info) :
        return ResidentialLocationDecoration()

    # -----------------------------------------------------------------
    def __init__(self) :
        Decoration.__init__(self)

        self.ResidentCount = 0
        self.ResidenceList = {}

    # -----------------------------------------------------------------
    @property
    def EndPointCount(self) :
        """
        EndPointCount -- return the total number of EndPoint nodes inside
        Capsule nodes assigned to the ResidentialLocation
        """
        count = 0
        for capsule in self.HostObject.Members :
            count += capsule.Capsule.EndPointCount

        return count

    # -----------------------------------------------------------------
    @property
    def ResidentCapacity(self) :
        return self.EndPointCount * self.HostObject.ResidentialLocationProfile.ResidentsPerNode

    # -----------------------------------------------------------------
    def Fitness(self, person) :
        if self.ResidentCount >= self.ResidentCapacity : return 0

        invweight = self.ResidentCount / self.ResidentCapacity
        pfitness = self.HostObject.ResidentialLocationProfile.Fitness(person)
        return restrict(random.gauss(1.0 - invweight, 0.1), 0, 1.0) * pfitness

    # -----------------------------------------------------------------
    def AddResident(self, person) :
        """
        AddResident -- find an available EndPoint among the Capsules and
        assign the person to the EndPoint

        Args:
            person -- SocialNodes.Person
        """
        bestcnt = self.HostObject.ResidentialLocationProfile.ResidentsPerNode + 1
        bestfit = None

        # this just goes through the entire list of capsules in the residential
        # location and finds the one with the least number of people assigned to
        # it, really just a way of balancing load across residential units
        for capsule in self.HostObject.Members :
            if capsule.Name not in self.ResidenceList :
                self.ResidenceList[capsule.Name] = []
                bestfit = capsule
                break
            elif len(self.ResidenceList[capsule.Name]) < bestcnt :
                bestcnt = len(self.ResidenceList[capsule.Name])
                bestfit = capsule

        if bestfit :
            self.ResidentCount += 1
            self.ResidenceList[bestfit.Name].append(person)

        # this returns a Capsle
        return bestfit

    # -----------------------------------------------------------------
    def AddResidentToNode(self, person, nodename) :
        """
        AddPersonToNode -- add a person to a specific node

        person -- an object of type Person
        nodename -- the string name of a capsule
        """

        if nodename not in self.ResidenceList :
            self.ResidenceList[nodename] = []

        self.ResidenceList[nodename].append(person)
        self.ResidentCount += 1

        return nodename

    # -----------------------------------------------------------------
    def Dump(self) :
        return Decoration.Dump(self)

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
CommonDecorations = [ CoordDecoration, IntersectionTypeDecoration, RoadTypeDecoration, 
                      EndPointDecoration, CapsuleDecoration,
                      BusinessLocationProfileDecoration, BusinessLocationDecoration,
                      ResidentialLocationProfileDecoration, ResidentialLocationDecoration ]

