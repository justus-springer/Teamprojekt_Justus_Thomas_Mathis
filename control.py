from PyQt5.QtCore import QThread, pyqtSignal, QDateTime
from PyQt5.Qt import QVector2D, Qt
import random
import math

import robots
from toolbox import sumvectors, isNumberKey, keyToNumber
from inputs import get_gamepad, NoDataError, UnpluggedError

DAEMON_SLEEP = 50

class Controller(QThread):

    # This will be emittet whenevery the controller wants the robot to do a full stop
    fullStopSignal = pyqtSignal()
    fullStopRotationSignal = pyqtSignal()

    shootSignal = pyqtSignal()
    switchToGunSignal = pyqtSignal(int)
    nextGunSignal = pyqtSignal(int)


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
        self.readyToFire = False

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
                self.a = - self.a_max
            else:
                self.a = + self.a_max


    def moveInDirection(self, direction, speed=1000):
        self.moveAtSpeed(speed)
        self.aimAt(self.x + 200 * direction.x(), self.y + 200 * direction.y())

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
    def receiveRobotInfo(self, x, y, alpha, v, v_alpha, readyToFire):
        self.x = x
        self.y = y
        self.alpha = alpha
        self.v = v
        self.v_alpha = v_alpha
        self.readyToFire = readyToFire

    # THis will be called once every 10 ticks
    def receiveRobotsInView(self, robotsInView):
        self.robotsInView = robotsInView

    def receiveWallsInView(self, wallsInView):
        self.wallsInView = wallsInView


class PlayerController(Controller):

    def __init__(self, robotId):
        super().__init__(robotId)
        self.target_x = 500
        self.target_y = 500
        self.keysPressed = []


    def run(self):

        while True:

            if Qt.Key_W in self.keysPressed:
                self.moveAtSpeed(self.v_max)
            elif Qt.Key_S in self.keysPressed:
                self.moveAtSpeed(-self.v_max)
            else:
                self.moveAtSpeed(0)

            if Qt.Key_A in self.keysPressed:
                self.rotateAtSpeed(-self.v_alpha_max)
            elif Qt.Key_D in self.keysPressed:
                self.rotateAtSpeed(self.v_alpha_max)
            else:
                self.rotateAtSpeed(0)

            if Qt.Key_Space in self.keysPressed:
                self.shootSignal.emit()

            for key in filter(isNumberKey, self.keysPressed):
                self.switchToGunSignal.emit(keyToNumber(key) - 1)

            self.msleep(DAEMON_SLEEP)

    ### Slots

    def keysPressedSlot(self, keysPressed):
        self.keysPressed = keysPressed


class PlayerController2(Controller):

    def __init__(self, robotId):
        super().__init__(robotId)
        self.target_x = 500
        self.target_y = 500
        self.keysPressed = []

    def run(self):

        while True:

            print('wasd: ', self.v_alpha)

            if Qt.Key_I in self.keysPressed:
                self.moveAtSpeed(self.v_max)
            elif Qt.Key_K in self.keysPressed:
                self.moveAtSpeed(-self.v_max)
            else:
                self.moveAtSpeed(0)

            if Qt.Key_J in self.keysPressed:
                self.rotateAtSpeed(-self.v_alpha_max)
            elif Qt.Key_L in self.keysPressed:
                self.rotateAtSpeed(self.v_alpha_max)
            else:
                self.rotateAtSpeed(0)

            if Qt.Key_O in self.keysPressed:
                self.shootSignal.emit()

            for key in filter(isNumberKey, self.keysPressed):
                self.switchToGunSignal.emit(keyToNumber(key) - 1)

            self.msleep(DAEMON_SLEEP)

    ### Slots

    def keysPressedSlot(self, keysPressed):
        self.keysPressed = keysPressed


# abstract
class ChaseController(Controller):

    def __init__(self, robotId, targetId):
        super().__init__(robotId)

        self.targetId = targetId
        self.lastSighting = {'x' : 500, 'y' : 500, 'pos' : QVector2D(0,0), 'dist' : 0, 'angle' : 0, 'timestamp' : 1000}
        self.previousSighting = {'x' : 501, 'y' : 501, 'pos' : QVector2D(0,0), 'dist' : 0, 'angle' : 0, 'timestamp' : 0}
        self.aimPos = QVector2D(500, 500)
        self.state = "Searching"

    # abstract
    def computeAim(self):
        raise NotImplementedError("Implement this method, stupid!")

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
                if self.readyToFire:
                    self.shootSignal.emit()


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
        speed = distanceTravelled / timeDifference

        # Extrapolate the position one second into the FUTURE
        futurePosEstimate = self.lastSighting['pos'] + 1 * speed * direction
        return futurePosEstimate

class ChaseGuardController(ChaseController):

    def computeAim(self):
        middle = QVector2D(500, 500)
        delta_vec = middle - self.lastSighting['pos']
        if delta_vec.length() != 0:
            delta_vec *= 200 / delta_vec.length()
            return self.lastSighting['pos'] + delta_vec
        else:
            return self.lastSighting['pos']


class RunController(Controller):

    def __init__(self, robotId, targetIds):
        super().__init__(robotId)

        self.targetIds = targetIds
        self.aim_direction = QVector2D(1,0)

    def run(self):

        while True:

            if self.robotsInView != {}:

                vecs = []
                myPosition = QVector2D(self.x, self.y)

                for id in self.targetIds:
                    robot = self.robotsInView[id]
                    v = (myPosition - robot['pos']).normalized()
                    v *= (1 / robot['dist'])
                    vecs.append(v)

                wall_vecs = []
                distances = []
                for rect in self.wallsInView:

                    rect_center = QVector2D(rect.center().x(), rect.center().y())
                    direction = (myPosition - rect_center).normalized()
                    distance = (myPosition - rect_center).length()

                    if distance < 200:
                        wall_vecs.append(direction)
                        distances.append(distance)

                if len(distances) == 0:
                    avg_distance = 1000
                else:
                    avg_distance = sum(distances) / len(distances)

                result_wall_vec = sumvectors(wall_vecs).normalized()
                result_wall_vec *= 3 * (1 / avg_distance) # wall vector counts 3 times as much as a robot
                vecs.append(result_wall_vec)

                self.aim_direction = sumvectors(vecs).normalized()
                self.moveInDirection(self.aim_direction)


            self.msleep(DAEMON_SLEEP)

class XboxController(Controller):
    def __init__(self, robotId):
        super().__init__(robotId)
        self.target_x = 0
        self.target_y = 0


    def run(self):

        rotation = 0
        movespeed = 0

        while True:

            try:
                events = get_gamepad(blocking = False)

                for event in events:
                    if event.code in ['ABS_X', 'ABS_Y', 'ABS_RX', 'ABS_RY', 'SYN_REPORT']:
                        continue
                    print(event.ev_type, event.code, event.state)

                for event in events:
                    if event.code == 'ABS_X':
                        if event.state > 28000:
                            rotation = 1
                        elif event.state < -28000:
                            rotation = -1
                        else:
                            rotation = 0
                    elif event.code == 'ABS_RZ':
                        movespeed = event.state / 255
                    elif event.code == 'ABS_Z':
                        movespeed = -event.state / 255
                    elif event.code == 'BTN_WEST' and event.state == 1:
                        self.shootSignal.emit()
                    elif event.code == 'ABS_HAT0X':
                        self.nextGunSignal.emit(event.state)

            except NoDataError:
                pass
            except UnpluggedError:
                pass

            self.rotateAtSpeed(self.v_alpha_max * rotation)
            self.moveAtSpeed(self.v_max * movespeed)
