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
        self.crnt_x = 0
        self.crnt_y = 0
        self.crnt_v = 0
        self.crnt_v_alpha = 0
        self.crnt_alpha = 0
        self.a_max = 0
        self.a_alpha_max = 0
        self.positionsData = {}

        # These will be fetched by the main program
        self.a = 0
        self.a_alpha = 0

    def fetchValues(self):
        return self.a, self.a_alpha

    def aimAt(self, target_x, target_y):

        delta_x = target_x - self.crnt_x
        delta_y = target_y - self.crnt_y
        target_alpha = math.degrees(math.atan2(delta_y, delta_x)) % 360

        delta_alpha = (target_alpha - self.crnt_alpha) % 360

        # Do we need to move clockwise or counterclockwise?
        if delta_alpha > 180:
            counterclockwise = True
            delta_alpha = 360 - delta_alpha
        else:
            counterclockwise = False

        if delta_alpha < robots.EPSILON_ALPHA and self.crnt_v_alpha < robots.EPSILON_V_ALPHA:
            # If we are at the target, don't accelerate
            self.a_alpha = 0
            self.fullStopRotationSignal.emit()
        else:

            stopping_distance = self.crnt_v_alpha*self.crnt_v_alpha / (2 * self.a_alpha_max) + robots.EPSILON_ALPHA

            if delta_alpha <= stopping_distance:
                # In this case, brake
                if self.crnt_v_alpha > 0:
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

        delta_x = target_x - self.crnt_x
        delta_y = target_y - self.crnt_y
        delta_dist = math.sqrt(delta_x*delta_x + delta_y*delta_y)

        if delta_dist < robots.EPSILON_POS and self.crnt_v < robots.EPSILON_V:
            # If we are at the target, don't accelerate
            self.a = 0
            self.fullStopSignal.emit()
        else:

            stopping_distance = self.crnt_v*self.crnt_v / (2 * self.a_max) + robots.EPSILON_ALPHA

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
        self.crnt_x = x
        self.crnt_y = y
        self.crnt_alpha = alpha
        self.crnt_v = v
        self.crnt_v_alpha = v_alpha

    # THis will be called once every 10 ticks
    def receiveRobotPositions(self, positionsData):
        self.positionsData = positionsData


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
            if self.targetId in self.positionsData:
                self.target_x = self.positionsData[self.targetId]['x']
                self.target_y = self.positionsData[self.targetId]['y']

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

            if self.crnt_x > 800 or self.crnt_x < 200 or self.crnt_y > 800 or self.crnt_y < 200:
                self.target_x = 500
                self.target_y = 500

            elif self.targetId in self.positionsData:
                self.target_x = self.crnt_x + (self.crnt_x - self.positionsData[self.targetId]['x'])
                self.target_y = self.crnt_y + (self.crnt_y - self.positionsData[self.targetId]['y'])

            self.aimAt(self.target_x, self.target_y)
            self.msleep(100)
