from google.appengine.ext import db
import webapp2
from google.appengine.api import users, mail
import itertools
import logging

from main import BaseHandler
from models import *

def is_overlapping(rq1, rq2):
  return max(rq1.starttime,rq2.starttime) <= min(rq1.endtime,rq2.endtime)


class AdminListHandler(BaseHandler):
  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect("/login")
    elif not UserInfo.isAdmin(user.user_id()):
      self.redirect("/")
    else:
      rqs = ScheduleRequest.all()
      template_args ={
        'user': user,
        'rqs': rqs,
        'timetable': timetable
      }
      self.render_template("adminlist.html", **template_args)

  def post(self):
    arqs = self.request.get_all("approve")
    drqs = self.request.get_all("deny")
    parqs = []
    pdrqs = []
    roomdaylist = []
    crqs = []
    pcrqs = []
    pcrqks = []
    for rq in arqs:
      rq = db.get(rq)
      roomday = (rq.roomnum, rq.startdate)
      if roomday in roomdaylist:
        crqs.append(rq)
      else:
        roomdaylist.append(roomday)
    for crq in crqs:
      allcrqs = db.GqlQuery("SELECT * FROM ScheduleRequest WHERE roomnum = :rnum AND startdate = :sdate", rnum=crq.roomnum, sdate=crq.startdate).run()
      for pair in itertools.combinations(allcrqs,2):
        if is_overlapping(pair[0],pair[1]):
          if str(pair[0].key()) not in pcrqks:
            pcrqs.append(pair[0])
            pcrqks.append(str(pair[0].key()))
            arqs.remove(str(pair[0].key()))
          if str(pair[1].key()) not in pcrqks:
            pcrqs.append(pair[1])
            pcrqks.append(str(pair[1].key()))
            arqs.remove(str(pair[1].key())) 
    for rq in arqs:
      if rq in drqs: drqs.remove(rq)
      rq = db.get(rq)
      parqs.append(rq)
      accepted = RoomSchedule(roomnum=rq.roomnum, userid=rq.userid,role=rq.role,
                              startdate=rq.startdate,
                              starttime=rq.starttime,endtime=rq.endtime,
                              deletekey=rq.deletekey, reserved=True)
      accepted.put()
      sender_address = "Room Scheduling Notification <notification@roomscheduler490.appspotmail.com>"
      subject = "Your request has been approved"
      body = """
      Your request of room %s has been approved.
      """ % rq.roomnum
      user_address = rq.useremail
      mail.send_mail(sender_address, user_address, subject, body)
      rq.delete()

    for rq in drqs:
      rq = db.get(rq)
      pdrqs.append(rq)
      sender_address = "Room Scheduling Notification <notification@roomscheduler490.appspotmail.com>"
      subject = "Your request has been denied"
      body = """
      Your request of room %s has been denied.
      """ % rq.roomnum
      user_address = rq.useremail
      mail.send_mail(sender_address, user_address, subject, body)
      rq.delete()

    template_args = {
      'user': users.get_current_user(),
      'arqs': parqs,
      'drqs': pdrqs,
      'crqs': pcrqs,
      'timetable': timetable
    } 
    self.render_template("adminsuccess.html", **template_args)
