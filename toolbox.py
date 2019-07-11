from PyQt5.Qt import QVector2D, Qt
import math
import robotGame
def minmax(value, low, high):
    return max(min(value, high), low)

# Takes an angle in degrees and returns a normalized vector pointing in that angle
def angleToVector(angle):
    return QVector2D(math.cos(math.radians(angle)), math.sin(math.radians(angle)))

def vectorToAngle(vector):
    return math.degrees(math.atan2(vector.y(), vector.x()))

def sumvectors(vecs):
    result = QVector2D(0,0)
    for v in vecs:
        result += v
    return result

# Takes in center points (type: QVector2D) and radii of two circles and returns overlap vector
# returns None if there is no collision
def circleCircleCollision(p1, r1, p2, r2):

    delta = p1 - p2
    distance = delta.length()
    direction = delta.normalized()
    overlap_length = r1 + r2 - distance

    if overlap_length > 0:
        return direction * overlap_length
    else:
        return None

# Takes in center point (QVector2D) and radius of a circle and a rectangle (QRectF) and returns overlap vector
# returns None if there is no collision
def circleRectCollision(pos, r, rect):

    rect_center = QVector2D(rect.center())
    vec = pos - rect_center
    length = vec.length()
    # scale the vector so it has length l-r
    vec *= (length-r) / length
    # This is the point of the circle which is closest to the rectangle
    closest_point = (rect_center + vec).toPointF()

    if rect.contains(closest_point):
        if pos.x() >= rect_center.x() and pos.y() >= rect_center.y():
            corner = rect.bottomRight()
        elif pos.x() >= rect_center.x() and pos.y() <= rect_center.y():
            corner = rect.topRight()
        elif pos.x() <= rect_center.x() and pos.y() >= rect_center.y():
            corner = rect.bottomLeft()
        elif pos.x() <= rect_center.x() and pos.y() <= rect_center.y():
            corner = rect.topLeft()

        overlap = QVector2D(corner - closest_point)
        return overlap
    else:
        return None


def isNumberKey(keyId):
    return keyId in [getattr(Qt, 'Key_' + str(i)) for i in range(10)]

def keyToNumber(keyId):
    for i in range(10):
        if keyId == getattr(Qt, 'Key_' + str(i)):
            return i

    return 0

# Pos has to be on the playground  or its out of bound
def posToTileIndex(pos,levelMatrix):
    return levelMatrix[int(pos.y() // robotGame.TILE_SIZE)][int(pos.x() // robotGame.TILE_SIZE)]

def onPlayground(pos):
    return (0 <= pos.x() < robotGame.WINDOW_SIZE) and (0 <= pos.y() < robotGame.WINDOW_SIZE)