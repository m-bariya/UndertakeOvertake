import Tkinter as tk
import threading
import time
import serial

class UOGui(threading.Thread):

    def __init__(self, connection):
        self.connection = connection
        self.auto = False
        self.speed = 1.2
        self.realSpeed = 0.0
        self.speedStep = 0.25
        self.MAX_SPEED = 1.2
        self.MIN_SPEED = 0
        self.overtake = 0
        self.lane = 0  # Right Lane = 0
        threading.Thread.__init__(self)
        self.start()

    def callback(self):
        self.root.quit()

    def toggleAuto(self):
        self.auto = not self.auto
        if self.auto:
            self.connection.write("auto\n")
            self.autoOnOff["text"] = "Enter Manual"
            self.autoOnOff["bg"] = "red"
        else:
            self.connection.write("manual\n")
            self.autoOnOff["text"] = "Enter Auto"
            self.autoOnOff["bg"] = "green"

    def speedUp(self):
        self.speed = min(self.speed+self.speedStep, self.MAX_SPEED)
        self.connection.write("speed,{}\n".format(self.speed))
        self.updateSpeedDisplay()

    def slowDown(self):
        self.speed = max(self.speed-self.speedStep, self.MIN_SPEED)
        self.connection.write("speed,{}\n".format(self.speed))
        self.updateSpeedDisplay()

    def updateSpeedDisplay(self):
        self.speedDisp["text"] = "Speed: " + str(self.speed)

    def moveLeft(self):
        self.lane = 1
        self.connection.write("shift,l\n")
        self.updateLaneDisplay()

    def moveRight(self):
        self.lane = 0
        self.connection.write("shift,r\n")
        self.updateLaneDisplay()

    def updateLaneDisplay(self):
        self.laneDisp["text"] = "Lane: " + str(self.lane)

    def override(self):
        print "overriding"

    def overtakeToggle(self):
        print "Automatic overtake control"
        self.overtake = not self.overtake
        if (self.overtake):
            self.overtakeButton["text"] = "Turn off auto overtake"
            self.overtakeButton["bg"] = "red"
        else:
            self.overtakeButton["text"] = "Turn on auto overtake"
            self.overtakeButton["bg"] = "green"
        self.connection.write("overtake\n")

    def createWidgets(self):
        self.speedDisp = tk.Label(relief='sunken')
        self.speedDisp["text"] = "Speed: " + str(self.speed)
        self.speedDisp.grid(row=0, column=0)

        self.goalSpeedDisp = tk.Label(relief='sunken')
        self.goalSpeedDisp["text"] = "Actual: " + str(self.realSpeed)
        self.goalSpeedDisp.grid(row=0, column=1)

        self.laneDisp = tk.Label(relief='sunken')
        self.laneDisp["text"] = "Lane: " + str(self.lane)
        self.laneDisp.grid(row=0, column=2, columnspan=2, sticky='news')

        self.autoOnOff = tk.Button(self.root)
        self.autoOnOff["text"] = "Enter auto"
        self.autoOnOff["command"] = self.toggleAuto
        self.autoOnOff["bg"] = "green"
        self.autoOnOff.grid(row=3, column=0, columnspan=4, sticky='news')

        self.overtakeButton = tk.Button(self.root)
        self.overtakeButton["text"] = "Turn on auto overtake."
        self.overtakeButton["command"] = self.overtakeToggle
        self.overtakeButton["bg"] = "green"
        self.overtakeButton.grid(row=4, column=0, columnspan=4, sticky='news')

        self.faster = tk.Button(self.root)
        self.faster["text"] = "+"
        self.faster["command"] = self.speedUp
        self.faster.grid(row=1, column=1,sticky='news')

        self.slower = tk.Button(self.root)
        self.slower["text"] = "-"
        self.slower["command"] = self.slowDown
        self.slower.grid(row=1, column=0, sticky='news')

        self.changeLaneLeft = tk.Button(self.root)
        self.changeLaneLeft["text"] = "<<"
        self.changeLaneLeft["command"] = self.moveLeft
        self.changeLaneLeft.grid(row=1, column=2)

        self.changeLaneRight = tk.Button(self.root)
        self.changeLaneRight["text"] = ">>"
        self.changeLaneRight["command"] = self.moveRight
        self.changeLaneRight.grid(row=1, column=3)

        self.overrideButton = tk.Button(self.root)
        self.overrideButton["text"] = "Override"
        self.overrideButton["command"] = self.override
        self.overrideButton.grid(row=2, column = 2, columnspan=2)

    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.createWidgets()
        self.root.mainloop()


frdm = serial.Serial('COM4', 9600, timeout=0.1)
#frdmIn = serial.Serial('COM6', 115200, timeout=0.1)
app = UOGui(frdm)

while True:
    frdmOut = frdm.readline()
    if frdmOut:
        print frdmOut