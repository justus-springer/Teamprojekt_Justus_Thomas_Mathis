class A:

    def __init__(self, x):
        self._x = x

    def printX(self):
        print(self._x)

if __name__ == '__main__':
    a = A(4)
    print(a._x)
