from PyQt5.QtCore import QThread, pyqtSignal
import random
import math

import robots

class Controller(QThread):

    # This will be emittet whenevery the controller wants the robot to do a full stop
    fullStopSignal = pyqtSignal()
    fullStopRotationSignal = pyqtSignal()

    def __init__(self, robotId):
        super().__init__()
        self.robotId = robotId

        # This data will be received every tick
        self.x = 0
        self.y = 0
        self.v = 0
        self.v_alpha = 0
        self.alpha = 0
        self.a_max = 0
        self.a_alpha_max = 0
        self.robotsInView = {}
        self.wallsInView = {}

        # These will be fetched by the main program
        self.a = 0
        self.a_alpha = 0

    def fetchValues(self):
        return self.a, self.a_alpha

    def aimAt(self, target_x, target_y):

        delta_x = target_x - self.x
        delta_y = target_y - self.y
        target_alpha = math.degrees(math.atan2(delta_y, delta_x)) % 360

        delta_alpha = (target_alpha - self.alpha) % 360

        # Do we need to move clockwise or counterclockwise?
        if delta_alpha > 180:
            counterclockwise = True
            delta_alpha = 360 - delta_alpha
        else:
            counterclockwise = False

        if delta_alpha < robots.EPSILON_ALPHA and self.v_alpha < robots.EPSILON_V_ALPHA:
            # If we are at the target, don't accelerate
            self.a_alpha = 0
            self.fullStopRotationSignal.emit()
        else:

            stopping_distance = self.v_alpha ** 2 / (2 * self.a_alpha_max) + robots.EPSILON_ALPHA

            if delta_alpha <= stopping_distance:
                # In this case, brake
                if self.v_alpha > 0:
                    self.a_alpha = -self.a_alpha_max
                else:
                    self.a_alpha = self.a_alpha_max
            else:
                # In this case, accelerate
                if counterclockwise:
                    self.a_alpha = -self.a_alpha_max
                else:
                    self.a_alpha = self.a_alpha_max


    def moveTo(self, target_x, target_y):

        self.aimAt(target_x, target_y)

        delta_x = target_x - self.x
        delta_y = target_y - self.y
        delta_dist = math.sqrt(delta_x*delta_x + delta_y*delta_y)

        if delta_dist < robots.EPSILON_POS and self.v < robots.EPSILON_V:
            # If we are at the target, don't accelerate
            self.a = 0
            self.fullStopSignal.emit()
        else:

            stopping_distance = self.v ** 2 / (2 * self.a_max) + robots.EPSILON_ALPHA

            if delta_dist <= stopping_distance:
                self.a = -self.a_max
            else:
                self.a = self.a_max


    ### Slots ###

    # This will be called once at the beginning of the game
    def receiveRobotSpecs(self, a_max, a_alpha_max):
        self.a_max = a_max
        self.a_alpha_max = a_alpha_max

    # This will be called every tick
    def receiveRobotInfo(self, x, y, alpha, v, v_alpha):
        self.x = x
        self.y = y
        self.alpha = alpha
        self.v = v
        self.v_alpha = v_alpha

    # THis will be called once every 10 ticks
    def receiveRobotsInView(self, robotsInView):
        self.robotsInView = robotsInView

    def receiveWallsInView(self, wallsInView):
        self.wallsInView = wallsInView

class TargetController(Controller):

    def __init__(self, robotId):
        super().__init__(robotId)
        self.target_x = 0
        self.target_y = 0

    def setTarget(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y

    def run(self):

        while True:
            self.moveTo(self.target_x, self.target_y)
            self.msleep(100)


class FollowController(Controller):

    def __init__(self, robotId, targetId):
        super().__init__(robotId)

        self.targetId = targetId
        self.target_x = 0
        self.target_y = 0

    def run(self):

        self.a = self.a_max

        while True:
            if self.targetId in self.robotsInView:
                self.target_x = self.robotsInView[self.targetId]['x']
                self.target_y = self.robotsInView[self.targetId]['y']

            self.aimAt(self.target_x, self.target_y)
            self.msleep(100)

class runController(Controller):

    def __init__(self, robotId, targetId):
        super().__init__(robotId)

        self.target_x = 0
        self.target_y = 0
        self.targetId = targetId

    def run(self):

        self.a = self.a_max

        while True:

            if self.x > 800 or self.x < 200 or self.y > 800 or self.y < 200:
                self.target_x = 500
                self.target_y = 500

            elif self.targetId in self.robotsInView:
                self.target_x = self.x + (self.x - self.robotsInView[self.targetId]['x'])
                self.target_y = self.y + (self.y - self.robotsInView[self.targetId]['y'])

            self.aimAt(self.target_x, self.target_y)
            self.msleep(100)
