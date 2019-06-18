from PyQt5.Qt import QVector2D

def minmax(value, low, high):
    return max(min(value, high), low)

def sumvectors(vecs):
    result = QVector2D(0,0)
    for v in vecs:
        result += v
    return result
