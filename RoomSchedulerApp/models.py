from google.appengine.ext import db
from google.appengine.api import users

class UserInfo(db.Model):
  userid = db.StringProperty()
  email = db.StringProperty()
  nickname = db.StringProperty()
  role = db.StringProperty(required=True, choices=set(["student","faculty","admin"]))
  
  @staticmethod
  def isAdmin(userid):
    q = db.GqlQuery("SELECT * FROM UserInfo WHERE userid = :1", userid)
    if q.get():
      return q.get().role == 'admin'
    else:
      return False
      
 
class RoomSchedule(db.Model):
  roomnum = db.StringProperty(required=True)
  userid = db.StringProperty(required=True)
  role = db.StringProperty(required=True, choices=set(["student","faculty","admin"]))
  startdate = db.DateProperty(required=True)
  starttime = db.IntegerProperty(required=True)
  endtime = db.IntegerProperty(required=True)
  reserved = db.BooleanProperty(indexed=False)
  deletekey = db.StringProperty(required=True)

class ScheduleRequest(db.Model):
  roomnum = db.StringProperty(required=True)
  userid = db.StringProperty(required=True)
  useremail = db.StringProperty(required=True)
  role = db.StringProperty(required=True, choices=set(["student","faculty","admin"]))
  startdate = db.DateProperty(required=True)
  starttime = db.IntegerProperty(required=True)
  endtime = db.IntegerProperty(required=True)
  reserved = db.BooleanProperty(indexed=False)
  timestamp = db.DateTimeProperty(required=True)
  deletekey = db.StringProperty(required=True)
  
class EquipmentUsage(db.Model):
  userid = db.StringProperty(required=True)
  useremail = db.StringProperty(required=True)
  equipment = db.StringProperty()
  iclickeramt = db.StringProperty()
  laptopsel = db.StringProperty()
  startdate = db.DateProperty(required=True)

class RoomInfo(db.Model):
  roomnum = db.StringProperty(required=True)
 
class EquipmentInfo(db.Model):
  equipmenttype = db.StringProperty(required=True)

class AdminName(db.Model):
  email = db.StringProperty(required=True)

#timetable = ['8:00 AM', '8:30 AM', '9:00 AM', '9:30 AM', '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM','12:00 PM', '12:30 PM', '1:00 PM', '1:30 PM', '2:00 PM', '2:30 PM', '3:00 PM', '3:30 PM', '4:00 PM', '4:30 PM', '5:00 PM', '5:30 PM', '6:00 PM', '6:30 PM', '7:00 PM', '7:30 PM', '8:00 PM']
timetable = ['8:00 AM', '8:15 AM', '8:30 AM', '8:45 AM', '9:00 AM', '9:15 AM', '9:30 AM', '9:45 AM', '10:00 AM', '10:15 AM', '10:30 AM', '10:45 AM', '11:00 AM', '11:15 AM', '11:30 AM', '11:45 AM','12:00 PM', '12:15 PM', '12:30 PM', '12:45 PM', '1:00 PM', '1:15 PM', '1:30 PM', '1:45 PM', '2:00 PM', '2:15 PM', '2:30 PM', '2:45 PM', '3:00 PM', '3:15 PM', '3:30 PM', '3:45 PM', '4:00 PM', '4:15 PM', '4:30 PM', '4:45 PM', '5:00 PM', '5:15 PM', '5:30 PM', '5:45 PM', '6:00 PM', '6:15 PM', '6:30 PM', '6:45 PM', '7:00 PM', '7:15 PM', '7:30 PM', '7:45 PM', '8:00 PM']

