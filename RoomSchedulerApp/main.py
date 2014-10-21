#!/usr/bin/env python
# -*- coding: cp1252 -*-
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import logging
import urllib
import datetime
import time
import uuid

from google.appengine.ext import db
import webapp2
from google.appengine.ext.webapp import util
from google.appengine.api import mail, users
#from aeoid import middleware, users
from webapp2_extras import jinja2, json
import datetime

from models import *

class BaseHandler(webapp2.RequestHandler):
  def render_template(self, filename, **template_args):
    self.response.write(self.jinja2.render_template(filename, **template_args))
  @webapp2.cached_property  
  def jinja2(self):
    return jinja2.get_jinja2(app=self.app)
  
from equip import *
from admin import *
from rooms import *



class MainHandler(BaseHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      q = db.GqlQuery("SELECT * FROM UserInfo WHERE userid = :1", user.user_id())
      if not q.get():
        uinfo = UserInfo(userid=user.user_id(),email=user.email(), nickname=user.nickname(), role="student")
        uinfo.put()
    uisAdmin = False if not user else UserInfo.isAdmin(user.user_id())
    template_args = {
      'login_url': users.create_login_url('/'),
      'logout_url': users.create_logout_url('/'),
      'user': user,
      'isadmin': uisAdmin,
    }
    self.render_template("index.html", **template_args)
    
class HelpHandler(BaseHandler):
  def get(self):
    user = users.get_current_user()
    template_args ={
        'user': user,
    }
    self.render_template("help.html", **template_args)

class MailHandler(BaseHandler):
  def post(self):
    fromaddr = self.request.get('email') #has to be a google email
    subject = self.request.get('subject')
    msg = self.request.get('message')
    toaddr = "Room Scheduling Message <notification@roomscheduler490.appspotmail.com>"
    mail.send_mail(fromaddr, toaddr, subject, msg)
    self.response.write('Sent Message')

class CalendarHandler(BaseHandler):
  def get(self):
    events = RoomSchedule.all()
    response = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//roomscheduling/eventcal//EN\n"
    for event in events:
      if (event.starttime%4) == 0:
        starthour=event.starttime/4
        startminute=0
      elif (event.starttime%4) == 1:
        starthour=event.starttime/4
        startminute=15
      elif (event.starttime%4) == 2:
        starthour=event.starttime/4
        startminute=30
      else:
        starthour=event.starttime/4
        startminute=45
      if (event.endtime%4) == 0:
        endhour = event.endtime/4
        endminute=0
      elif (event.endtime%4) == 1:
        endhour=event.endtime/4
        endminute=15
      elif (event.endtime%4) == 2:
        endhour=event.endtime/4
        endminute=30
      else:
        endhour=event.endtime/4
        endminute=45
      dtstart=datetime.datetime(event.startdate.year, event.startdate.month, event.startdate.day,starthour+8,startminute).strftime("%Y%m%dT%H%M%S")
      dtend=datetime.datetime(event.startdate.year, event.startdate.month, event.startdate.day,endhour+8,endminute).strftime("%Y%m%dT%H%M%S")
      response += 'BEGIN:VEVENT\nDTSTART;TZID="America/New_York":%s\nDTEND;TZID="America/New_York":%s\nLOCATION:%s\nSUMMARY:%s\nEND:VEVENT\n' % (dtstart,dtend,event.roomnum,event.userid)
    response += "END:VCALENDAR"
    self.response.headers['Content-Type'] = 'text/calendar'
    self.response.out.write(response)

class CalendarEmbedHandler(BaseHandler):
  def get(self):
    template_args = {}
    self.render_template("calendarembed.html", **template_args)
                      

class AboutHandler(BaseHandler):
  def get(self):
	template_args = {}
	self.render_template("about.html", **template_args)

class DeleteOldHandler(BaseHandler):
  def get(self):
    today = datetime.datetime.today()
    olds = db.GqlQuery("SELECT * FROM RoomSchedule WHERE startdate < DATETIME(:year,:month,:day,0,0,0)",year=today.year,month=today.month,day=today.day).run()
    for oldr in olds:
      oldr.delete()

class CalendarJsonHandler(BaseHandler):
  def get(self):
    start=datetime.datetime.strptime(self.request.get('start'),"%Y-%m-%d")
    end=datetime.datetime.strptime(self.request.get('end'),"%Y-%m-%d")
    rnum = self.request.get('room')
    if rnum == 'all':
      allflag = True
      eventlist = db.GqlQuery("SELECT * FROM RoomSchedule WHERE startdate > DATETIME(:syear,:smonth,:sday,0,0,0) AND startdate < DATETIME(:eyear,:emonth,:eday,0,0,0)",syear=start.year,smonth=start.month,sday=start.day,eyear=end.year,emonth=end.month,eday=end.day).run()
    else:
      allflag = False
      eventlist = db.GqlQuery("SELECT * FROM RoomSchedule WHERE roomnum = :roomnum AND startdate > DATETIME(:syear,:smonth,:sday,0,0,0) AND startdate < DATETIME(:eyear,:emonth,:eday,0,0,0)",roomnum=rnum,syear=start.year,smonth=start.month,sday=start.day,eyear=end.year,emonth=end.month,eday=end.day).run()
    json_list = []
    for event in eventlist:
      #eid=uuid.uuid4().int
      etitle=event.userid + "/" + event.roomnum if allflag else "Reserved"
      if (event.starttime%4) == 0:
        starthour=event.starttime/4
        startminute=0
      elif (event.starttime%4) == 1:
        starthour=event.starttime/4
        startminute=15
      elif (event.starttime%4) == 2:
        starthour=event.starttime/4
        startminute=30
      else:
        starthour=event.starttime/4
        startminute=45
      if (event.endtime%4) == 0:
        endhour = event.endtime/4
        endminute=0
      elif (event.endtime%4) == 1:
        endhour=event.endtime/4
        endminute=15
      elif (event.endtime%4) == 2:
        endhour=event.endtime/4
        endminute=30
      else:
        endhour=event.endtime/4
        endminute=45
      edtstart=datetime.datetime(event.startdate.year, event.startdate.month, event.startdate.day,starthour+8,startminute).strftime("%Y-%m-%dT%H:%M:%S")
      edtend=datetime.datetime(event.startdate.year, event.startdate.month, event.startdate.day,endhour+8,endminute).strftime("%Y-%m-%dT%H:%M:%S")
      json_entry = {'start':edtstart, 'end':edtend, 'allDay': False,'title':etitle}
      json_list.append(json_entry)
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.encode(json_list))
		
application = webapp2.WSGIApplication([
    webapp2.Route(r'/', handler=MainHandler, name='home'),
    webapp2.Route(r'/rooms', handler=RoomHandler, name='room-list'),
    webapp2.Route(r'/rooms/<roomnum>', handler=RoomDetailHandler, name='room-detail'),
    webapp2.Route(r'/help', handler=HelpHandler, name='help'),
    webapp2.Route(r'/sendmail', handler=MailHandler, name='contact'),
    webapp2.Route(r'/equipment', handler=EquipHandler, name='equip'),
    webapp2.Route(r'/roomlist', handler=RoomListHandler, name='scheduledrooms'),
    webapp2.Route(r'/admin', handler=AdminListHandler, name='admin'),
    webapp2.Route(r'/delete', handler=DeletionHandler, name='delete'),
    webapp2.Route(r'/calendar', handler=CalendarHandler, name='cal'),
    webapp2.Route(r'/calendarembed', handler=CalendarEmbedHandler, name='calembed'),
    webapp2.Route(r'/about', handler=AboutHandler, name='about'),
    webapp2.Route(r'/deleteold', handler=DeleteOldHandler, name='deleteold'),
    webapp2.Route(r'/eventfeed', handler=CalendarJsonHandler, name='calendarjson'),
], debug=True)

def main():
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
