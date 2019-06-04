from PyQt5.QtCore import QRectF

class LevelLoader:

    LEVEL_SIZE = 100
    TILE_SIZE = 10

    FLOOR_TILE = 0
    WALL_TILE = 1
    MUD_TILE = 2

    # Reads a txt file and creates an 2 dimensional array representing a level
    # A '0' represents free space, a '1' represents a wall
    @staticmethod
    def loadLevel(filePath):
        levelMatrix = []
        obstacles = []

        f = open(filePath, "r")
        for i in range(LevelLoader.LEVEL_SIZE):
            line = f.readline()
            row = []
            for c in line:
                if c == '0':
                    row.append(LevelLoader.FLOOR_TILE)
                elif c == '1':
                    row.append(LevelLoader.WALL_TILE)
                elif c == '2':
                    row.append(LevelLoader.MUD_TILE)
                elif c == '\n':
                    pass
                else:
                    raise Exception('Unknown symbol: "' + c + '" in level "' + filePath + '"')
            levelMatrix.append(row)

        for row in range(LevelLoader.LEVEL_SIZE):
            for column in range(LevelLoader.LEVEL_SIZE):
                if levelMatrix[row][column] == 1:
                    obstacles.append(QRectF(column * LevelLoader.TILE_SIZE, row * LevelLoader.TILE_SIZE,
                                            LevelLoader.TILE_SIZE, LevelLoader.TILE_SIZE))

        return levelMatrix, obstacles
