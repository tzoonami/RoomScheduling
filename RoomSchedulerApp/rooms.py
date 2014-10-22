from google.appengine.ext import db
import webapp2
from google.appengine.api import users, mail
import datetime
from datetime import date
import re
from hashlib import sha1
from random import random
import logging
import os
from os import listdir
from os.path import isfile, join


from main import BaseHandler
from models import *

def genblocktable(building, room, day):
  # day is an actual datetime object representing the desired day
  dayblocks=["Free"]*48
  #logging.info(day.strftime("%a %m/%d"))
  dayschedule = db.GqlQuery("SELECT starttime, endtime FROM RoomSchedule WHERE roomnum = :1 AND startdate = :2 AND building = :3", room, day, building).run()
  if dayschedule is not None:
    for sched in dayschedule:
      for i in range(sched.starttime, sched.endtime):
        dayblocks[i] = "Reserved"
  return dayblocks

class RoomHandler(BaseHandler):
  def get(self,building):
    user = users.get_current_user()
    q = db.GqlQuery("SELECT * FROM BuildingInfo WHERE buildingname = :1", building)
    if q.get() is None:
      self.response.write('Error: invalid building name selected')
    else:
      templatepath = join(os.getcwd(),"templates")
      templates = [ f for f in listdir(templatepath) if isfile(join(templatepath,f)) ]
      if 'rooms-%s.html' % building in templates:
        template = 'rooms-%s.html' % building
      else:
        template = 'rooms.html'
      nums = RoomInfo.all().filter("building =", building).order("roomnum")
      template_args = {
        'logout_url': users.create_logout_url('/'),
        'user': user,
        'building': building,
        'rooms': nums
        }
      self.render_template(template, **template_args)

class RoomDetailHandler(BaseHandler):
  def get(self, building, roomnum):
    q = db.GqlQuery("SELECT * FROM RoomInfo WHERE building = :1 AND roomnum= :2", building, roomnum)
    if q.get() is None:
      self.response.write('Error: invalid room number selected')
    else:
      today = date.today()
      daylist = [today,today+datetime.timedelta(days=1),today+datetime.timedelta(days=2)]
      daystr=map(lambda x: x.strftime("%a %m/%d"), daylist)
      template_args = {
        'roomnum': roomnum,
        'timetable': timetable,
        'daystr': daystr,
        'building': building,
      }
      self.render_template("roomdetail.html", **template_args)

  def post(self, building, roomnum):
    try:
      failflag = False
      reason = ""
      timestamp = datetime.datetime.now()
      uid = self.request.get('name')
      if not uid:
        failflag = True
        reason = "You forgot your name."
      uemail = self.request.get('email')
      if (not failflag) and (not (re.match(r"[^@]+@[^@]+\.[^@]+", uemail) and uemail.split('@')[1].endswith('sc.edu'))):
        failflag = True
        reason="Valid sc.edu email address needed."
      sdate = self.request.get('sdate')
      
      if not failflag and not sdate:
        failflag = True
        reason = "You forgot the date."
      elif not failflag:
        startdatetime = datetime.datetime.strptime(sdate.strip(" "), '%m/%d/%Y')
        delta = startdatetime - timestamp
        if delta.days < -1:
          failflag = True
          reason = "You entered a date in the past."
      rnum = roomnum
      stime = self.request.get('stime')
      etime = self.request.get('etime')
      if not failflag and int(etime)-int(stime) <= 0:
        failflag = True
        reason = "Your end time was before the start time."
      if not failflag:
        blocks = genblocktable(building, roomnum,startdatetime.date())
        for i in range(int(stime),int(etime)):
          if blocks[i] == "Reserved":
            failflag = True
            reason = "The room is already reserved at that time."
      if failflag:
        template_args = {
          'reason': reason,
          'timestamp': timestamp,
        }
        self.render_template("roomfailure.html", **template_args)
        return
      dkey = sha1(str(random())).hexdigest()
      rss = ScheduleRequest(roomnum=rnum,userid=uid,useremail=uemail,role="admin",timestamp=timestamp,
      building=building,
      deletekey=dkey,
      startdate = startdatetime.date(),
      starttime = int(stime), 
      endtime = int(etime), reserved=True)
      rss.put()
      sender_address = "Room Scheduling Notification <notification@roomscheduler490.appspotmail.com>"
      subject = "Schedule Request deletion URL"
      body = """
      Your request of room %s in building %s from %s to %s on %s has been submitted. If you need to delete this request, use the link below.
      http://roomscheduler490.appspot.com/delete?dkey=%s
      """ % (rnum,building,timetable[int(stime)],timetable[int(etime)],sdate, dkey)
      user_address = uemail
      mail.send_mail(sender_address, user_address, subject, body)
    except ValueError:
      template_args = {
        'reason': "Invalid format given.",
        'timestamp': timestamp,
      }
      self.render_template("roomfailure.html", **template_args)
    else:
      template_args = {
        'roomnum': rnum,
        'sdate': sdate,
        'stime': timetable[int(stime)],
        'etime': timetable[int(etime)],
        'timestamp': timestamp.strftime("%Y-%m-%d %H:%M:%S"),
      }
      self.render_template("roomsuccess.html", **template_args)


class RoomListHandler(BaseHandler):
  def get(self,building):
    user = users.get_current_user()
    if building == "all":
      rms = RoomSchedule.all()
    else:
      rms = RoomSchedule.all().filter("building =", building)
    uisAdmin = False if not user else UserInfo.isAdmin(user.user_id())
    template_args = {
      'user': user,
      'rms': rms,
      'timetable': timetable,
      'isadmin': uisAdmin,
    }
    self.render_template("roomlist.html", **template_args)

class BuildingHandler(BaseHandler):
  def get(self):
    buildings = BuildingInfo.all()
    template_args = {
      'buildings': buildings
      }
    self.render_template("buildings.html", **template_args)

class DeletionHandler(BaseHandler):
  def get(self):
    deletionkey = self.request.get("dkey")
    q = db.GqlQuery("SELECT * FROM ScheduleRequest WHERE deletekey = :1", deletionkey)
    deleterecord = q.get()
    if deleterecord is None:
      q = db.GqlQuery("SELECT * FROM RoomSchedule WHERE deletekey = :1", deletionkey)
      deleterecord = q.get()
      if deleterecord is None:
        self.response.out.write("Invalid deletion URL.")
      else:
        deleterecord.delete()
        self.response.out.write("Scheduled room reservation deleted.")
    else:
      deleterecord.delete()
      self.response.out.write("Room reservation request deleted.")
    self.response.out.write('<br /><a href="/">Go back</a>')
      



  
