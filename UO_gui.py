import Tkinter as tk
import threading
import time
import serial

class UOGui(threading.Thread):

    def __init__(self, connection):
        self.connection = connection
        self.auto = False
        self.speed = 3
        self.MAX_SPEED = 12
        self.MIN_SPEED = 0
        self.lane = 0  # Right Lane = 0
        threading.Thread.__init__(self)
        self.start()

    def callback(self):
        self.root.quit()

    def toggleAuto(self):
        self.auto = not self.auto
        if self.auto:
            self.connection.write("auto\n")
            self.autoOnOff["text"] = "Exit Auto"
            self.autoOnOff["bg"] = "red"
        else:
            self.connection.write("manual\n")
            self.autoOnOff["text"] = "Enter Auto"
            self.autoOnOff["bg"] = "green"

    def speedUp(self):
        print "speeding up"
        self.speed = min(self.speed+1, self.MAX_SPEED)
        self.connection.write("speed,{}\n".format(self.speed / 10.0))
        print self.speed

    def slowDown(self):
        print "slowing down"
        self.speed = max(self.speed-1, self.MIN_SPEED)
        self.connection.write("speed,{}\n".format(self.speed / 10.0))
        print self.speed

    def toggleLane(self):
        print "changing lane"
        self.lane = int(not self.lane)
        if self.lane == 0:
            self.changeLane["text"] = "Move to left"
            self.connection.write("shift,l\n")
        else:
            self.changeLane["text"] = "Move to right"
            self.connection.write("shift,r\n")
        print self.lane

    def createWidgets(self):
        self.autoOnOff = tk.Button(self.root)
        self.autoOnOff["text"] = "Enter auto"
        self.autoOnOff["command"] = self.toggleAuto
        self.autoOnOff["bg"] = "green"
        self.autoOnOff.grid(row=0, column=0)

        self.faster = tk.Button(self.root)
        self.faster["text"] = "Speed up"
        self.faster["command"] = self.speedUp
        self.faster.grid(row=1, column=0)

        self.slower = tk.Button(self.root)
        self.slower["text"] = "Slow down"
        self.slower["command"] = self.slowDown
        self.slower.grid(row=1, column=1)

        self.changeLane = tk.Button(self.root)
        self.changeLane["text"] = "Move to left"
        self.changeLane["command"] = self.toggleLane
        self.changeLane.grid(row=2, column=0)

    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.createWidgets()
        self.root.mainloop()


frdm = serial.Serial('COM4', 9600, timeout=0.1)
app = UOGui(frdm)

while True:
	frdmOut = frdm.readline()
	if frdmOut:
		print frdmOut
