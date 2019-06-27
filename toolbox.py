from PyQt5.Qt import QVector2D

def minmax(value, low, high):
    return max(min(value, high), low)

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
