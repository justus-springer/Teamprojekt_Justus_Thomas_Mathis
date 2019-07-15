from PyQt5.QtCore import QRectF
from enum import Enum

class Tile(Enum):
    grass = 0
    wall = 1
    stone = 2
    sand = 3
    dark_sand = 4
    sand_stone = 5
    snow = 6
    water = 7
    stonewall = 8
    fire = 9

    def walkable(self):
        return self in [Tile.grass, Tile.sand, Tile.dark_sand, Tile.snow, Tile.stone]
    def shootable(self):
        return self in [Tile.grass, Tile.sand, Tile.dark_sand, Tile.snow, Tile.stone, Tile.water]

class LevelLoader:

    LEVEL_SIZE = 100
    TILE_SIZE = 10

    # Reads a txt file and creates an 2 dimensional array representing a level
    # A '0' represents free space, a '1' represents a wall
    @staticmethod
    def loadLevel(filePath):
        levelMatrix = []
        rects = []

        f = open(filePath, "r")
        for i in range(LevelLoader.LEVEL_SIZE):
            line = f.readline()
            row = []
            for c in line:
                if c == '\n':
                    continue
                try:
                    tileNum = int(c)
                    row.append(Tile(tileNum))
                except:
                    raise Exception('Unknown symbol: "' + c + '" in level "' + filePath + '"')
            levelMatrix.append(row)

        for i in range(LevelLoader.LEVEL_SIZE):
            for j in range(LevelLoader.LEVEL_SIZE):
                if levelMatrix[i][j] == Tile.wall:
                    new_rect = QRectF(j * LevelLoader.TILE_SIZE, i * LevelLoader.TILE_SIZE,
                                    LevelLoader.TILE_SIZE, LevelLoader.TILE_SIZE)

                    # Check if the rect would already be covered by one of our rects
                    if any(rect.contains(new_rect) for rect in rects):
                        continue

                    # Explore right and down to cover more walls in one square
                    n=0
                    while all(all(x == Tile.wall for x in column[j:j+n]) for column in levelMatrix[i:i+n]):
                        n += 1

                    rects.append(QRectF(j * LevelLoader.TILE_SIZE, i * LevelLoader.TILE_SIZE,
                                        (n-1) * LevelLoader.TILE_SIZE, (n-1) * LevelLoader.TILE_SIZE))

        return levelMatrix, rects
