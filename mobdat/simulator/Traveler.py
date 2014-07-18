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

@file    Traveler.py
@author  Mic Bowman
@date    2014-04-02

This module defines the SocialConnector class. This class implements
the social (people) aspects of the mobdat simulation.

"""

import os, sys
import logging

sys.path.append(os.path.join(os.environ.get("SUMO_HOME"), "tools"))
sys.path.append(os.path.join(os.environ.get("OPENSIM","/share/opensim"),"lib","python"))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "lib")))

import random
import Trip, LocationKeyMap

from mobdat.common import TravelTimeEstimator, ValueTypes
from mobdat.common.timedevent import TimedEvent, TimedEventList, IntervalVariable
from mobdat.common.graph import SocialDecoration 

logger = logging.getLogger(__name__)


# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
class Traveler :

    # -----------------------------------------------------------------
    def __init__(self, person, connector) :
        """
        Args:
            person -- Graph.Node (NodeType == Person) or SocialNodes.Person
            connector -- SocialConnector
        """
        self.Connector = connector
        self.World = self.Connector.World

        self.Person = person
        self.Job = self.Person.JobDescription

        self.RuleMap = TravelRules.BuildRuleMap(self.World, self.Person)

        self.LocationKeyMap = LocationKeyMap.LocationKeyMap(self.World, self.Person)
        self.TravelEstimator = TravelTimeEstimator.TravelTimeEstimator()

        self.EventList = None
        if self.BuildDailyEvents(self.Connector.WorldDay) :
            self.ScheduleNextTrip()

    # -----------------------------------------------------------------
    def BuildDailyEvents(self, worldday, addextras = True) :
        logger.debug('Compute day %d schedule for %s', worldday, self.Person.Name)

        homeev = TimedEvent.BackgroundEvent.Create('home', 0.0, (0.0, 0.0), (24.0 * 1000.0, 24.0 * 1000.0))
        evlist = TimedEventList.TimedEventList(homeev, estimator = self.TravelEstimator)
        lastev = evlist.LastEvent.EventID

        if self.RuleMap['Work'].Apply(worldday, evlist) :

            if addextras :
                self.RuleMap['CoffeeBeforeWork'].Apply(worldday, evlist)
                self.RuleMap['LunchDuringWork'].Apply(worldday, evlist)
                self.RuleMap['Dinner'].Apply(worldday, evlist) :
                self.RuleMap['ShoppingTrip'].Apply(worldday, evlist)

        # if its not a work day, then see if we should go shopping
        else :
            self.RuleMap['Dinner'].Apply(worldday, evlist) :
            self.RuleMap['ShoppingTrip'].Apply(worldday, evlist)

        # attempt to solve the constraints, if it doesn't work, then try
        # again with just work, really need to add an "optional" or "maximal"
        # notion to the constraint solver
        if not evlist.SolveConstraints() :
            if addextras :
                return self.BuildDailyEvents(worldday, False)
            else :
                logger.warn('Failed to resolve schedule constraints for traveler %s', self.Person.Name)
                self.EventList = None
                return False

        self.EventList = evlist
        return True

    # -----------------------------------------------------------------
    def ScheduleNextTrip(self) :
        if not self.EventList :
            return

        # this builds out daily events up to one week in the future with
        # the idea that we should be able to go through at least a full
        # work week looking for something interesting to happen
        for day in range(0, 7) :
            if self.EventList.MoreTripEvents() : break
            self.BuildDailyEvents(self.Connector.WorldDay + day + 1) :

        while self.EventList.MoreTripEvents() :
            tripev = self.EventList.PopTripEvent()
            starttime = float(tripev.StartTime)

            # this just allows us to start in the middle of the day, traveler at work
            # will start at work rather than starting at home
            if starttime > self.Connector.WorldTime :
                source = self.LocationKeyMap.ResolveLocationKey(tripev.SrcName)
                destination = self.LocationKeyMap.ResolveLocationKey(tripev.DstName)
                self.Connector.AddTripToEventQueue(Trip.Trip(self, starttime, source, destination))

                logger.info('Scheduled trip from %s to %s', source.Name, destination.Name)
                return

        logger.info('No trip events for %s', self.Person.Name)

    # -----------------------------------------------------------------
    def TripCompleted(self, trip) :
        """
        TripCompleted -- event handler called by the connector when the trip is completed

        Args:
            trip -- initialized Trip object
        """
        self.TravelEstimator.SaveTravelTime(trip.Source, trip.Destination, self.Connector.WorldTime - trip.ActualStartTime)
        self.ScheduleNextTrip()

    # -----------------------------------------------------------------
    def TripStarted(self, trip) :
        pass

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
def AddWorkEvent(evlist, event, schedule, deviation = 2.0) :
    duration = schedule.WorldEndTime - schedule.WorldStartTime
    sinterval = (schedule.WorldStartTime - deviation, schedule.WorldStartTime + deviation)
    einterval = (schedule.WorldEndTime - deviation, schedule.WorldEndTime + deviation)

    workEV = TimedEvent.AggregateDurationEvent.Create('work', 0.0, sinterval, einterval, duration)
    workID = evlist.AddPlaceEvent(workEV)
    evlist.InsertWithinPlaceEvent(event, workID)

    return workID

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
def AddCoffeeBeforeWorkEvent(evlist, workevent, worldtime) :
    """Add a PlaceEvent for coffee before a work event. This moves the
    coffee event as close as possible to the work event.
    """

    event = TimedEvent.PreEventEvent.Create('coffee', worldtime, (0.0, 24.0), (0.0, 24.0), 0.2)
    idc = evlist.AddPlaceEvent(event)

    evlist.InsertAfterPlaceEvent(evlist.PrevPlaceID(workevent), idc)

    return idc

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
def AddLunchToWorkEvent(evlist, workevent, worldtime) :
    event = TimedEvent.VariableMiddleEvent.Create('lunch', worldtime, (11.5, 13.0), (12.5, 14.0), 0.75)
    idl = evlist.AddPlaceEvent(event)

    evlist.InsertWithinPlaceEvent(workevent, idl)

    return idl

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
def AddRestaurantAfterWorkEvent(evlist, workevent, worldtime) :
    event = TimedEvent.PostEventEvent.Create('dinner', worldtime, (0.0, 24.0), (0.0, 24.0), 1.5)
    idr = evlist.AddPlaceEvent(event)

    evlist.InsertAfterPlaceEvent(workevent, idr)

    return idr

## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
def AddShoppingTrip(evlist, worldtime, maxcount = 4, prevevent = None) :
    # happens between 7am and 10pm

    if prevevent :
        ids = prevevent
    else :
        event = TimedEvent.VariableMiddleEvent.Create('shopping', worldtime, (7.0, 22.0), (7.0, 22.0), 0.75)
        ids = evlist.AddPlaceEvent(event)
        evlist.InsertWithinPlaceEvent(evlist.LastEvent.EventID, ids)

    stops = int(random.triangular(0, 4, 1))
    while stops > 0 :
        stops = stops - 1

        postev = TimedEvent.PostEventEvent.Create('shopping', worldtime, (7.0, 22.0), (7.0, 22.0), 0.5)
        idnew = evlist.AddPlaceEvent(postev)
        evlist.InsertAfterPlaceEvent(ids, idnew)
        ids = idnew

