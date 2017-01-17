

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
    11: "*",
    30: "0",
    48: "#"
    }

from evdev import InputDevice

DEVICE = "/dev/input/by-id/usb-Storm-Interface.com_Storm-Interface-event-kbd"

dev = InputDevice(DEVICE)
dev.grab()  #exclusive access

for event in dev.read_loop():
      if event.type==1 and event.value==1:
         if event.code in keys:
            print("KEY CODE: ", keys[event.code])
               
