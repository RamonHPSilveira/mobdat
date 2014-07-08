#!/usr/bin/python
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

@file    OpenSimBuilder.py
@author  Mic Bowman
@date    2013-12-03

This file defines the opensim builder class for mobdat traffic networks.
The functions in this file will rez a mobdat network in an OpenSim region.
"""

import os, sys
import logging

# we need to import python modules from the $SUMO_HOME/tools directory
sys.path.append(os.path.join(os.environ.get("OPENSIM","/share/opensim"),"lib","python"))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "lib")))

import uuid
import OpenSimRemoteControl
from mobdat.common.graph import Graph

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class OpenSimBuilder :

    # -----------------------------------------------------------------
    def __init__(self, settings, world, laysettings) :
        self.Logger = logging.getLogger(__name__)

        self.World = world
        self.LayoutSettings = laysettings

        self.RoadMap = {}
        self.NodeMap = {}

        try :
            self.OpenSimConnector = OpenSimRemoteControl.OpenSimRemoteControl(settings["OpenSimConnector"]["EndPoint"])
            self.OpenSimConnector.Capability = uuid.UUID(settings["OpenSimConnector"]["Capability"])
            self.OpenSimConnector.Scene = settings["OpenSimConnector"]["Scene"]

            woffs = settings["OpenSimConnector"]["WorldCenter"]
            self.WorldCenterX = woffs[0]
            self.WorldCenterY = woffs[1]
            self.WorldCenterZ = woffs[2]

        except NameError as detail: 
            self.Logger.warn("Failed processing OpenSim configuration; name error %s", (str(detail)))
            sys.exit(-1)
        except KeyError as detail: 
            self.Logger.warn("unable to locate OpenSim configuration value for %s", (str(detail)))
            sys.exit(-1)
        except :
            exctype, value =  sys.exc_info()[:2]
            self._Logger.warn('handler failed with exception type %s; %s', exctype, str(value))
            sys.exit(-1)

    # -----------------------------------------------------------------
    def FindAssetInObject(self, assetinfo) :
        oname = assetinfo["ObjectName"]
        iname = assetinfo["ItemName"]

        result = self.OpenSimConnector.FindObjects(pattern = oname)
        if not result["_Success"] or len(result["Objects"]) == 0 :
            self.Logger.warn("Unable to locate container object %s; %s",oname, result["_Message"])
            sys.exit(-1)

        objectid = result["Objects"][0]
        result = self.OpenSimConnector.GetObjectInventory(objectid)
        if not result["_Success"] :
            self.Logger.warn("Failed to get inventory from container object %s; %s",oname, result["_Message"])
            sys.exit(-1)
            
        for item in result["Inventory"] :
            if item["Name"] == iname :
                return item["AssetID"]

        self.Logger.warn("Failed to locate item %s in object %s",iname, oname);
        return None

    # -----------------------------------------------------------------
    def ComputeRotation(self, sig1, sig2) :
        for i in range(4) :
            success = True
            for j in range(4) :
                if sig1[j] != sig2[(i + j) % 4] and sig2[(i + j) % 4] != '*/*' :
                    success = False
                    break

            if success :
                return i

        return -1

    # -----------------------------------------------------------------
    def ComputeLocation(self, snode, enode) :
        if snode.Name not in self.NodeMap :
            self.Logger.warn('cannot find node %s in the node map' % (snode.Name))
            return False

        if enode.Name not in self.NodeMap :
            self.Logger.warn('cannot find node %s in the node map' % (enode.Name))
            return False

        sbump = self.NodeMap[snode.Name].Padding
        ebump = self.NodeMap[enode.Name].Padding
    
        deltax = enode.Coord.X - snode.Coord.X
        deltay = enode.Coord.Y - snode.Coord.Y

        # west
        if deltax < 0 and deltay == 0 :
            s1x = snode.Coord.X - sbump
            s1y = snode.Coord.Y
            e1x = enode.Coord.X + ebump
            e1y = enode.Coord.Y

        # north
        elif deltax == 0 and deltay > 0 :
            s1x = snode.Coord.X
            s1y = snode.Coord.Y + sbump
            e1x = enode.Coord.X
            e1y = enode.Coord.Y - ebump

        # east
        elif deltax > 0 and deltay == 0 :
            s1x = snode.Coord.X + sbump
            s1y = snode.Coord.Y
            e1x = enode.Coord.X - ebump
            e1y = enode.Coord.Y

        # south
        elif deltax == 0 and deltay < 0 :
            s1x = snode.Coord.X
            s1y = snode.Coord.Y - sbump
            e1x = enode.Coord.X
            e1y = enode.Coord.Y + ebump

        else :
            self.Logger.warn('something went wrong computing the signature')
            return(0,0,0,0)

        return (s1x + self.WorldCenterX, s1y + self.WorldCenterY, e1x + self.WorldCenterX, e1y + self.WorldCenterY)


    # -----------------------------------------------------------------
    def PushNetworkToOpenSim(self) :
        self.CreateNodes()
        self.CreateRoads()

    # -----------------------------------------------------------------
    def CreateRoads(self) :

        for rname, road in self.World.IterEdges(edgetype = 'Road') :
            if rname in self.RoadMap :
                continue

            if road.RoadType.Name not in self.LayoutSettings.RoadTypeMap :
                self.Logger.warn('Failed to find asset for %s' % (road.RoadType.Name))
                continue 

            # check to see if we need to render this road at all
            if road.RoadType.Render :
                asset = self.LayoutSettings.RoadTypeMap[road.RoadType.Name][0].AssetID
                zoff = self.LayoutSettings.RoadTypeMap[road.RoadType.Name][0].ZOffset

                if type(asset) == dict :
                    asset = self.FindAssetInObject(asset)
                    self.LayoutSettings.RoadTypeMap[road.RoadType.Name][0].AssetID = asset

                (p1x, p1y, p2x, p2y) = self.ComputeLocation(road.StartNode, road.EndNode)
                startparms = "{ 'spoint' : '<%f, %f, %f>', 'epoint' : '<%f, %f, %f>' }" % (p1x, p1y, zoff, p2x, p2y, zoff)

                if abs(p1x - p2x) > 0.1 or abs(p1y - p2y) > 0.1 :
                    result = self.OpenSimConnector.CreateObject(asset, pos=[p1x, p1y, zoff], name=road.Name, parm=startparms)

            # build the map so that we do render the reverse roads
            self.RoadMap[Graph.GenEdgeName(road.StartNode, road.EndNode)] = True
            self.RoadMap[Graph.GenEdgeName(road.EndNode, road.StartNode)] = True
    

    # -----------------------------------------------------------------
    def CreateNode(self, name, node) :
        tname = node.IntersectionType.Name
        sig1 = node.EdgeMap.Signature()

        if tname not in self.LayoutSettings.IntersectionTypeMap :
            self.Logger.warn('Unable to locate node type %s' % (tname))
            return

        success = False
        for itype in self.LayoutSettings.IntersectionTypeMap[tname] :
            sig2 = itype.Signature

            rot = self.ComputeRotation(sig1, sig2)
            if rot >= 0 :
                self.NodeMap[name] = itype

                p1x = node.Coord.X + self.WorldCenterX
                p1y = node.Coord.Y + self.WorldCenterY
                p1z = itype.ZOffset
                asset = itype.AssetID
                if type(asset) == dict :
                    asset = self.FindAssetInObject(asset)
                    itype.AssetID = asset

                startparms = "{ 'center' : '<%f, %f, %f>', 'angle' : %f }" % (p1x, p1y, p1z, 90.0 * rot)

                if node.IntersectionType.Render :
                    result = self.OpenSimConnector.CreateObject(asset, pos=[p1x, p1y, p1z], name=name, parm=startparms)

                success = True
                break

        if not success :
            self.NodeMap[name] = self.LayoutSettings.IntersectionTypeMap[tname][0]
            self.Logger.warn("No match for node %s with type %s and signature %s" % (name, tname, sig1))

    # -----------------------------------------------------------------
    def CreateNodes(self) :

        for name, node in self.World.IterNodes(nodetype = 'Intersection') :
            self.CreateNode(name, node)

        for name, node in self.World.IterNodes(nodetype = 'EndPoint') :
            self.CreateNode(name, node)
