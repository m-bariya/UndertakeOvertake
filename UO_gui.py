import Tkinter as tk
import threading
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
        self.enableAll = 0

        self.state = 'MANUAL'
        self.sameLaneDist = 0.0
        self.oppLaneDist = 0.0
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
        self.disableEverything()

    def moveRight(self):
        self.lane = 0
        self.connection.write("shift,r\n")
        self.updateLaneDisplay()
        self.disableEverything()

    def updateLaneDisplay(self):
        self.laneDisp["text"] = "Lane: " + str(self.lane)

    def override(self):
        print "overriding"

    def overtakeToggle(self):
        print "Automatic overtake control"
        self.overtake = 1
        self.overtakeButton["state"] = "disabled"
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
        self.overtakeButton["state"] = "disabled"
        self.overtakeButton["command"] = self.overtakeToggle
        self.overtakeButton.grid(row=4, column=0, columnspan=4, sticky='news')

        self.faster = tk.Button(self.root)
        self.faster["text"] = "+"
        self.faster["command"] = self.speedUp
        self.faster.grid(row=1, column=1, sticky='news')

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
        self.overrideButton.grid(row=2, column=2, columnspan=2)

        self.stateDisp = tk.Label(relief='sunken')
        self.stateDisp["text"] = "State: " + self.state
        self.stateDisp.grid(row=2, column=0, columnspan=2)

        self.sameLaneDisp = tk.Label(relief='sunken')
        self.sameLaneDisp["text"] = "Samelane Dist: " + str(0.0)
        self.sameLaneDisp.grid(row=5, column=0, columnspan=2, sticky='news')

        self.oppLaneDisp = tk.Label(relief='sunken')
        self.oppLaneDisp["text"] = "Oncoming Dist: " + str(0.0)
        self.oppLaneDisp.grid(row=5, column=2, columnspan=2, sticky='news')

    def update(self):
        if (self.state == "OBSTACLE"):
            self.overtakeButton["state"] = "active"
        else:
            self.overtakeButton["state"] = "disabled"
        self.goalSpeedDisp["text"] = "Actual: " + str(self.realSpeed)
        self.stateDisp["text"] = self.state
        self.laneDisp["text"] = "Lane: " + str(self.lane)
        self.sameLaneDisp["text"] = "Samelane Dist: " + str(self.sameLaneDist)
        self.oppLaneDisp["text"] = "Oncoming Dist: " + str(self.oppLaneDist)
        self.root.after(10, self.update)
        if (self.enableAll):
              self.enableEverything();

    def enableEverything(self):
        self.autoOnOff["state"] = "active"
        self.overtakeButton["state"] = "active"
        self.faster["state"] = "active"
        self.slower["state"] = "active"
        self.changeLaneLeft["state"] = "active"
        self.changeLaneRight["state"] = "active"
        self.overrideButton["state"] = "active"

    def disableEverything(self):
        self.autoOnOff["state"] = "disabled"
        self.overtakeButton["state"] = "disabled"
        self.faster["state"] = "disabled"
        self.slower["state"] = "disabled"
        self.changeLaneLeft["state"] = "disabled"
        self.changeLaneRight["state"] = "disabled"
        self.overrideButton["state"] = "disabled"

    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.createWidgets()
        self.root.after(10, self.update)
        self.root.mainloop()

frdm = serial.Serial('COM10', 115200, timeout=0.1)
app = UOGui(frdm)

while True:
    frdmOut = frdm.readline()
    if frdmOut:
        tokens = frdmOut.strip('\n').strip('\r').split(',')
        if len(tokens) == 5:
            try:
                app.state = tokens[0].upper()
                app.realSpeed= float(tokens[1])
                app.lane = int(tokens[2])
                app.sameLaneDist = float(tokens[3])
                app.oppLaneDist = float(tokens[4])
            except Exception as e:
                print 'Parsing error.', e
        elif tokens[0] == "DIDIT":
            app.enableAll = 1
        #print frdmOut
