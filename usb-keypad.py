from influxdb import InfluxDBClient
import time
from evdev import InputDevice
from threading import Thread
from queue import Queue
from subprocess import call
import schedule
from relays import Relay

relay = Relay()
threadQueue = Queue()      

#Global variables
enteredCode = ""
intraKeyTime = 0
startTime = 0
keyCount = 0
masterUnlock = False


def keyPadScan():
   DEVICE = "/dev/input/by-id/usb-Storm-Interface.com_Storm-Interface-event-kbd"
   dev = InputDevice(DEVICE)
   dev.grab()  #exclusive access, Linux won't think it's a keyboard

   keys = {
    2: "1",
    3: "2",
    4: "3",
    5: "4",
    6: "5",
    7: "6",
    8: "7",
    9: "8",
    10: "9",
    11: "Lock",
    30: "0",
    48: "Un-Lock"
    }

   for event in dev.read_loop():
       if event.type==1 and event.value==1:
         if event.code in keys:
             threadQueue.put([keys[event.code], event.sec]) #drop keypress on the Queue
               
def supervisor():
    global enteredCode
    global intraKeyTime
    global startTime
    global keyCount
    global masterUnlock

    while True:
       if threadQueue.not_empty:
           keypress = threadQueue.get()
           key = keypress[0]  #Key the user hit
           timeStamp = keypress[1] #When the user hit the key
           keyCount += 1      #How many keys the user has hit
           if timeStamp - startTime > 5: #If it's been more than 5 seconds
              clear()             #start over
              intraKeyTime = timeStamp
              startTime = timeStamp
           if timeStamp - intraKeyTime < 3: #If user is confident
               enteredCode += key      #append key
               intraKeyTime = timeStamp     #see how long it takes to get next key
               
           if keyCount == 6: #User has entered the right number of keys
              
              if (key == "Un-Lock") | (key == "Lock"): #If last key hit was lock/unlock
                 # Lock Third Floor
                 if enteredCode == "031775Lock":
                    relay.OFF_3()
                    call(["omxplayer", "/home/pi/elevator/resource/Third lock.m4a"])
                    report("Third Floor Locked")
                    clear()
                 # Unlock Third Floor   
                 elif enteredCode == "031775Un-Lock":
                    relay.ON_3()
                    if masterUnlock:
                       call(["omxplayer", "/home/pi/elevator/resource/Third unlock.m4a"])
                       report("Third Floor Un-Lock")
                    else:
                       report("Third floor Temp Un-locked")
                       call(["omxplayer", "/home/pi/elevator/resource/Third floor temp unlock.m4a"])
                       time.sleep(8)
                       relay.OFF_3()
                       call(["omxplayer", "/home/pi/elevator/resource/Third lock.m4a"])
                       report("Third Floor Locked")
                    clear()
                 # Lock Penthouse   
                 elif enteredCode == "041775Lock":
                    relay.OFF_4()
                    call(["omxplayer", "/home/pi/elevator/resource/Penthouse lock.m4a"])
                    report("Fourth Floor Locked")
                    clear()
                 # Unlock Penthouse   
                 elif enteredCode == "041775Un-Lock":
                    relay.ON_4()
                    if masterUnlock:
                       call(["omxplayer", "/home/pi/elevator/resource/Penthouse unlock.m4a"])
                       report("Fourth Floor Un-Lock")
                    else:
                       report("Fourth Floor Temp Un-Locked")
                       call(["omxplayer", "/home/pi/elevator/resource/Penthouse temp unlock.m4a"])
                       time.sleep(8)
                       relay.OFF_4()
                       call(["omxplayer", "/home/pi/elevator/resource/Penthouse lock.m4a"])
                       report("Fourth Floor Locked")
                    clear()
                 # Master Unlock Code
                 # Unlock both Penthouse and Third Floors
                 elif enteredCode=="991775Un-Lock":
                    masterUnlock = True
                    relay.ON_3()
                    relay.ON_4()
                    call(["omxplayer", "/home/pi/elevator/resource/Both unlock.m4a"])
                    report("Third & Fourth Floor Un-Locked")
                    clear()
                 # Master Lock Code
                 # Lock both the Penthouse and Third Floors
                 elif enteredCode == "991775Lock":
                    masterUnlock = False
                    relay.OFF_3()
                    relay.OFF_4()
                    call(["omxplayer", "/home/pi/elevator/resource/Both lock.m4a"])
                    report("Third & Fourth Floor Locked")
                    clear()
                    
                 else: #wrong code entered
                    report("Wrong Code")
                    call(["omxplayer", "/home/pi/elevator/resource/Try again.m4a"])
                    clear()
                  
                  
           if keyCount>7: #User seems to be mashing keys willy nilly
              report("Just hitting buttions")
              call(["omxplayer", "/home/pi/elevator/resource/You don't know the code.m4a"])
              clear()

           if (key == "Un-Lock") | (key == "Lock"):
              if (keyCount > 3) & (keyCount < 6):
                 report("Meh")
                 call(["omxplayer", "/home/pi/elevator/resource/Meh.m4a"])
                 clear()
              
def timeLock(): #put lock all on the queue
   threadQueue.put(["9",time.time()])
   threadQueue.put(["9",time.time()])
   threadQueue.put(["1",time.time()])
   threadQueue.put(["7",time.time()])
   threadQueue.put(["7",time.time()])
   threadQueue.put(["5",time.time()])
   threadQueue.put(["Lock",time.time()])
   
def clear():
   global enteredCode
   global keyCount
   global startTime
   global intraKeyTime
   enteredCode = ""
   keyCount = 0
   startTime = 0
   intraKeyTime = 0

def report(message):
  json_body = [
    {
      "measurement": "events",
      "tags":{},
##      "time":"",
      "fields": {
      "title": message
         }
      }
   ]
  database = InfluxDBClient('ward.filmworkers.com', 8086,'','','access')
  database.write_points(json_body)
  print(message, time.ctime())

keyPadScanThread = Thread(target = keyPadScan)
supervisorThread = Thread(target = supervisor)

supervisorThread.start()
keyPadScanThread.start()

schedule.every().day.at("18:00").do(timeLock)

while True:
   schedule.run_pending()
   time.sleep(10)

