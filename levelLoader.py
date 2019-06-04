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
    def loadLevel(filePath, dontBeAnIdiot = True):
        levelMatrix = []
        rects = []

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

        if dontBeAnIdiot:
            for i in range(LevelLoader.LEVEL_SIZE):
                for j in range(LevelLoader.LEVEL_SIZE):
                    if levelMatrix[i][j] == 1:
                        new_rect = QRectF(j * LevelLoader.TILE_SIZE, i * LevelLoader.TILE_SIZE,
                                        LevelLoader.TILE_SIZE, LevelLoader.TILE_SIZE)

                        # Check if the rect would already be covered by one of our rects
                        if any(rect.contains(new_rect) for rect in rects):
                            continue

                        # Explore right and down to cover more walls in one square
                        n=0
                        while all(all(x == 1 for x in column[j:j+n]) for column in levelMatrix[i:i+n]):
                            n += 1

                        rects.append(QRectF(j * LevelLoader.TILE_SIZE, i * LevelLoader.TILE_SIZE,
                                            (n-1) * LevelLoader.TILE_SIZE, (n-1) * LevelLoader.TILE_SIZE))
        else:
            for i in range(LevelLoader.LEVEL_SIZE):
                for j in range(LevelLoader.LEVEL_SIZE):
                    if levelMatrix[i][j] == 1:
                        rects.append(QRectF(j * LevelLoader.TILE_SIZE, i * LevelLoader.TILE_SIZE,
                                            LevelLoader.TILE_SIZE, LevelLoader.TILE_SIZE))

        return levelMatrix, rects
