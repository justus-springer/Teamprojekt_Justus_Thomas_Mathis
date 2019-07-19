from PyQt5.QtGui import QPixmap
from PyQt5.Qt import QSoundEffect, QUrl

class ResourceManager:

    textures = {}
    soundEffects = {}

    @classmethod
    def getTexture(self, filePath):

        if filePath in self.textures:
            return self.textures[filePath]
        else:
            txt = QPixmap(filePath)
            self.textures[filePath] = txt
            return txt

    @classmethod
    def getSoundEffect(self, filePath):

        if filePath in self.soundEffects:
            return self.soundEffects[filePath]
        else:
            soundEffect = QSoundEffect()
            soundEffect.setSource(QUrl.fromLocalFile(filePath))
            soundEffect.setVolume(0.1)
            self.soundEffects[filePath] = soundEffect
            return soundEffect
