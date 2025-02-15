from .youtubeDataKeys import MetaDataType
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import logging
import os

logger = logging.getLogger(__name__)


class EasyID3Manager():  # pragma: no_cover

    def __init__(self):
        self.filePath = None
        self.title = None
        self.album = None
        self.artist = None
        self.playlistName = None
        self.trackNumber = None
        self.website = None

    def setParams(self, filePath,
                  title=None,
                  album=None,
                  artist=None,
                  ytHash=None,
                  trackNumber=None,
                  playlistName=None):
        if not os.path.isfile(filePath):
            logger.warning(
                f"File {filePath} doesn't exist - provide correct file path")
        self.filePath = filePath
        self.title = title
        self.album = album
        self.artist = artist
        self.ytHash = ytHash
        self.trackNumber = trackNumber
        self.playlistName = playlistName

    def saveMetaData(self):
        if self.filePath is None:
            raise FileNotFoundError(
                f"File {self.filePath} doesn't exist - provide correct file path")
        audio = EasyID3(self.filePath)
        if self.title:
            audio[MetaDataType.TITLE.value] = self.title
        if self.album:
            audio[MetaDataType.ALBUM.value] = self.album
        if self.artist:
            audio[MetaDataType.ARTIST.value] = self.artist
        if self.ytHash:
            audio[MetaDataType.WEBSITE.value] = self.ytHash
        if self.trackNumber:
            audio[MetaDataType.TRACK_NUMBER.value] = self.trackNumber
        audio.save()

    def readMetaData(self):
        audio = EasyID3(self.filePath)
        if MetaDataType.TITLE.value in audio:
            self.title = audio[MetaDataType.TITLE.value]
        if MetaDataType.ALBUM.value in audio:
            self.album = audio[MetaDataType.ALBUM.value]
        if MetaDataType.ARTIST.value in audio:
            self.artist = audio[MetaDataType.ARTIST.value]
        if MetaDataType.WEBSITE.value in audio:
            self.ytHash = audio[MetaDataType.WEBSITE.value]
        if MetaDataType.TRACK_NUMBER.value in audio:
            self.trackNumber = audio[MetaDataType.TRACK_NUMBER.value]

    def _showMetaDataInfo(self, path):  # pragma: no_cover
        """Method used to show Metadata info

        Args:
            path (str): file path
        """
        audioInfo = MP3(path, ID3=EasyID3)
        logger.info(audioInfo.pprint())
