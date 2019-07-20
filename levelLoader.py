from PyQt5.QtCore import QRectF
from enum import Enum
import re

class Tile(Enum):
    grass = 0
    wall = 1
    stone = 2
    sand = 3
    dark_sand = 4
    sand_stone = 5
    snow = 6
    ice = 7
    stonewall = 8
    fire = 9

    def walkable(self):
        return self in [Tile.grass, Tile.sand, Tile.dark_sand, Tile.snow, Tile.stone]
    def shootable(self):
        return self in [Tile.grass, Tile.sand, Tile.dark_sand, Tile.snow, Tile.stone, Tile.ice]

class LevelLoader:

    LEVEL_SIZE = 100
    TILE_SIZE = 10

    META_DATA_TAGS = ['single_spawn', 'duel_spawns', 'chaser_spawns']
    META_DATA_DEFAULT_VALUES = {'single_spawn' : (50,50), 'duel_spawns' : [(10,50),(90,50)], 'chaser_spawns' : [(50,20),(20,50),(70,50)]}

    # Reads a txt file and creates an 2 dimensional array representing a level
    # A '0' represents free space, a '1' represents a wall
    @classmethod
    def loadLevel(self, filePath):
        levelMatrix = []
        rects = []
        metadata = {}

        # construct regex pattern
        pattern = '(?P<name>'
        for tag in self.META_DATA_TAGS:
            pattern += tag + '|'
        pattern = pattern[:-1] # remove last '|'
        pattern += ')'
        pattern += ':\s*(?P<data>.*)'

        with open(filePath, "r") as fileObject:
            for line in fileObject:
                if line.startswith('\n'):
                    continue

                match = re.match(pattern, line)
                if match:
                    # if it matches, the line contains metadata
                    tag = match.group('name')
                    if tag in self.META_DATA_TAGS:
                        metadata[tag] = eval(match.group('data'))
                    else:
                        raise Exception('Unknown tag name: "' + tag + '" in level "' + filePath + '"')
                else:
                    # else it contains level data
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

        # construct obstacle list
        for i in range(self.LEVEL_SIZE):
            for j in range(self.LEVEL_SIZE):
                if levelMatrix[i][j] == Tile.wall:
                    new_rect = QRectF(j * self.TILE_SIZE, i * self.TILE_SIZE,
                                          self.TILE_SIZE, self.TILE_SIZE)

                    # Check if the rect would already be covered by one of our rects
                    if any(rect.contains(new_rect) for rect in rects):
                        continue

                    # Explore right and down to cover more walls in one square
                    n=0
                    while all(all(x == Tile.wall for x in column[j:j+n]) for column in levelMatrix[i:i+n]):
                        n += 1

                    rects.append(QRectF(j * self.TILE_SIZE, i * self.TILE_SIZE,
                                        (n-1) * self.TILE_SIZE, (n-1) * self.TILE_SIZE))

        # fill in missing metadata with default values
        for tag in self.META_DATA_TAGS:
            if tag not in metadata:
                metadata[tag] = self.META_DATA_DEFAULT_VALUES[tag]

        return levelMatrix, rects, metadata
