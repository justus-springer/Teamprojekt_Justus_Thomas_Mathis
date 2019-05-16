class LevelLoader:

    # Reads a txt file and creates an 2 dimensional array representing a level
    # A '0' represents free space, a '1' represents a wall
    @staticmethod
    def loadLevel(filePath):
        result = []

        f = open(filePath, "r")
        for i in range(100):
            line = f.readline()
            row = []
            for c in line:
                if c == '0':
                    row.append(0)
                elif c == '1':
                    row.append(1)
            result.append(row)

        return result
