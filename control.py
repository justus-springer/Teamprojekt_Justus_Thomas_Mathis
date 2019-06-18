from PyQt5.QtCore import QThread, pyqtSignal, QDateTime
from PyQt5.Qt import QVector2D
import random
import math

import robots

DAEMON_SLEEP = 50

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

    def rotateAtSpeed(self, target_speed):

        if self.v_alpha < target_speed:
            self.a_alpha = self.a_alpha_max
        else:
            self.a_alpha = -self.a_alpha_max

    def moveAtSpeed(self, target_speed):

        if self.v < target_speed:
            self.a = self.a_max
        else:
            self.a = -self.a_max


    ### Slots ###

    # This will be called once at the beginning of the game
    def receiveRobotSpecs(self, a_max, a_alpha_max, v_max, v_alpha_max):
        self.a_max = a_max
        self.a_alpha_max = a_alpha_max
        self.v_max = v_max
        self.v_alpha_max = v_alpha_max

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
            self.msleep(DAEMON_SLEEP)

class ChaseController(Controller):

    def __init__(self, robotId, targetId):
        super().__init__(robotId)

        self.targetId = targetId
        self.lastSighting = {'x' : 500, 'y' : 500, 'pos' : QVector2D(0,0), 'dist' : 0, 'angle' : 0, 'timestamp' : 1000}
        self.previousSighting = {'x' : 501, 'y' : 501, 'pos' : QVector2D(0,0), 'dist' : 0, 'angle' : 0, 'timestamp' : 0}
        self.aimPos = QVector2D(500, 500)
        self.state = "Searching"

    # This should be implemented by any inheriting class
    # returns the position to aim at
    def computeAim(self):
        return QVector2D(500, 500) # dummy

    def updateLastSighting(self):

        # if the last sighting is older than 2 seconds, return to Searching
        current_time = QDateTime.currentMSecsSinceEpoch()
        if current_time > self.lastSighting['timestamp'] + 2000:
            self.state = "Searching"

        if self.targetId in self.robotsInView:
            self.state = "Chasing"
            newSighting = self.robotsInView[self.targetId]

            # id this sighting is newer than the old one
            if newSighting['timestamp'] > self.lastSighting['timestamp']:
                self.previousSighting = self.lastSighting
                self.lastSighting = newSighting

    def run(self):

        while True:

            self.updateLastSighting()

            self.aimPos = self.computeAim()

            if self.state == "Searching":

                self.moveAtSpeed(0)
                self.rotateAtSpeed(100)

            elif self.state == "Chasing":

                self.moveTo(self.aimPos.x(), self.aimPos.y())

            self.msleep(DAEMON_SLEEP)


class ChaseDirectlyController(ChaseController):

    def computeAim(self):
        return self.lastSighting['pos']

class ChasePredictController(ChaseController):

    def computeAim(self):

        delta_vec = self.lastSighting['pos'] - self.previousSighting['pos']
        timeDifference = (self.lastSighting['timestamp'] - self.previousSighting['timestamp']) / 1000
        direction = delta_vec.normalized()
        distanceTravelled = delta_vec.length()

        if timeDifference != 0:
            speed = distanceTravelled / timeDifference
            # Compute the future position estimate in one second
            futurePosEstimate = self.lastSighting['pos'] + 1 * speed * direction

            return futurePosEstimate
        else:
            return QVector2D(500, 500)

class ChaseFollowController(ChaseController):

    def computeAim(self):

        delta_vec = self.lastSighting['pos'] - self.previousSighting['pos']
        timeDifference = (self.lastSighting['timestamp'] - self.previousSighting['timestamp']) / 1000
        direction = delta_vec.normalized()
        distanceTravelled = delta_vec.length()

        if timeDifference != 0:
            speed = distanceTravelled / timeDifference
            # Compute the past position estimate of one second ago
            futurePosEstimate = self.lastSighting['pos'] - 1 * speed * direction

            return futurePosEstimate
        else:
            return QVector2D(500, 500)


class RunController(Controller):

    def __init__(self, robotId, targetIds):
        super().__init__(robotId)

        self.target_x = 0
        self.target_y = 0
        self.targetIds = targetIds

    def run(self):

        self.a = self.a_max
        self.result = 0

        while True:
            self.temp = 0

            #if self.x > 800 or self.x < 200 or self.y > 800 or self.y < 200:
#
             #   self.target_x = 500
             #   self.target_y = 500
             #   self.aimAt(self.target_x, self.target_y)
             #   self.msleep(63)


            for rect in self.wallsInView:

                self.rect_center = QVector2D(rect.center())
                if (math.fabs(self.x - self.rect_center.x()) < 200 and math.fabs(self.y - self.rect_center.y()) < 200):
                    self.target_x = 500
                    self.target_y = 500
                    self.aimAt(self.target_x, self.target_y)
                    self.msleep(100)


                    break









            if self.targetIds[0] in self.robotsInView :

                self.temp_max = 2000

                for i in range(3):

                    if (self.robotsInView[self.targetIds[i]]['dist'] < self.temp_max):
                        self.temp_max = self.robotsInView[self.targetIds[i]]['dist']
                        self.result = i
                        
                   # if (math.sqrt(math.fabs(self.robotsInView[self.targetIds[i]]['x'] - self.x) + math.fabs(self.robotsInView[self.targetIds[i]]['y'] - self.y)) < self.temp_max):
                   #     self.temp_max = math.sqrt(math.fabs(self.robotsInView[self.targetIds[i]]['x'] - self.x) + (math.fabs(self.robotsInView[self.targetIds[i]]['y'] - self.y)))
                   #     self.result = i

                self.target_x = self.x + (self.x - self.robotsInView[self.targetIds[self.result]]['x'])
                self.target_y = self.y + (self.y - self.robotsInView[self.targetIds[self.result]]['y'])

            self.aimAt(self.target_x, self.target_y)
            self.msleep(DAEMON_SLEEP)
