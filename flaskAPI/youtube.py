from mainWebPage import app, logger, youtubeDownloder, socketio, configParserMenager
from common.youtubeDataKeys import YoutubeLogs, YoutubeVariables
from flask import send_file, render_template
from common.emits import DownloadMediaFinishEmit, SingleMediaInfoEmit, PlaylistMediaInfoEmit
import zipfile
import os
import yt_dlp
import random
import string
from typing import List
from flask import send_file, render_template

hashTable = {}


class FlaskSingleMedia():
    def __init__(self, title: str, artist: str, url: str) -> None:
        self.title = title
        self.artist = artist
        self.url = url


class FlaskPlaylistMedia():
    def __init__(self, plyalistName: str, trackList: List[FlaskSingleMedia]) -> None:
        self.playlistName = plyalistName
        self.trackList = trackList

    @classmethod
    def initFromPlaylistMedia(cls, playlistName, trackList):
        trackList = []
        for track in trackList:
            trackList.append(FlaskSingleMedia(track.title,
                                              track.artist,
                                              track.url))
        return cls(playlistName, trackList)


def zipAllFilesInList(direcoryPath, playlistName, listOfFilePaths):
    # do utilsa leci
    zipFileFullPath = os.path.join(direcoryPath,
                                   playlistName)
    print(zipFileFullPath)
    with zipfile.ZipFile(f"{zipFileFullPath}.zip", "w") as zipInstance:
        for filePath in listOfFilePaths:
            zipInstance.write(filePath, filePath.split("/")[-1])
    return f"{zipFileFullPath.split('/')[-1]}.zip"


def handleError(errorMsg):
    downloadMediaFinishEmit = DownloadMediaFinishEmit()
    downloadMediaFinishEmit.sendEmitError(errorMsg)
    logger.error(
        f"{YoutubeLogs.MEDIA_INFO_DOWNLAOD_ERROR.value}: {errorMsg}")


def downloadSingleInfoAndMedia(youtubeURL, type=False):
    logger.debug(YoutubeLogs.DOWNLOAD_SINGLE_VIDEO.value)
    singleMediaInfoResult = youtubeDownloder.getSingleMediaInfo(youtubeURL)
    if singleMediaInfoResult.isError():
        errorMsg = singleMediaInfoResult.getErrorInfo()
        handleError(errorMsg)
        return False
    mediaInfo = singleMediaInfoResult.getData()
    flaskSingleMedia = FlaskSingleMedia(mediaInfo.title,
                                        mediaInfo.artist,
                                        mediaInfo.url)
    mediaInfoEmit = SingleMediaInfoEmit()
    mediaInfoEmit.sendEmit(flaskSingleMedia)
    fullPath = downloadSingleMedia(mediaInfo.url,
                                   mediaInfo.title,
                                   type)
    return fullPath


def downloadSingleMedia(singleMediaURL, singleMediaTitle, type):
    direcotryPath = configParserMenager.getSavePath()
    trackTitle = singleMediaTitle
    if type:
        singleMediaInfoResult = youtubeDownloder.downloadVideo(
            singleMediaURL, type)
        trackInfo = singleMediaInfoResult.getData()
        fileName = f"{trackTitle}_{type}p.{trackInfo.extension}"
    else:
        singleMediaInfoResult = youtubeDownloder.downloadAudio(singleMediaURL)
        trackInfo = singleMediaInfoResult.getData()
        fileName = f"{trackTitle}.{YoutubeVariables.MP3.value}"
    if singleMediaInfoResult.isError():
        errorMsg = singleMediaInfoResult.getErrorInfo()
        handleError(errorMsg)
        return False
    logger.info(f"{YoutubeLogs.VIDEO_DOWNLOADED.value}: {fileName}")
    logger.debug(f"{YoutubeLogs.DIRECTORY_PATH.value}: {direcotryPath}")
    return os.path.join(direcotryPath, fileName)


def downloadAllPlaylistTracks(playlistTracks, type):
    filePaths = []
    for track in playlistTracks:
        fullPath = downloadSingleMedia(track.url, track.title, type)
        filePaths.append(fullPath)
    return filePaths


def downloadPlaylist(youtubeURL, type=False):
    logger.debug(YoutubeLogs.DOWNLAOD_PLAYLIST.value)
    playlistMediaInfoResult = youtubeDownloder.getPlaylistMediaInfo(youtubeURL)
    if playlistMediaInfoResult.isError():
        errorMsg = playlistMediaInfoResult.getErrorInfo()
        handleError(errorMsg)
        return False
    playlistInfo = playlistMediaInfoResult.getData()
    playlistName = playlistInfo.playlistName
    flaskPlaylistMedia = FlaskPlaylistMedia(playlistName,
                                            playlistInfo.singleMediaList)
    playlistInfoEmit = PlaylistMediaInfoEmit()
    playlistInfoEmit.sendEmit(flaskPlaylistMedia)
    direcotryPath = configParserMenager.getSavePath()
    filePaths = downloadAllPlaylistTracks(playlistInfo.singleMediaList,
                                          type)
    zipNameFile = zipAllFilesInList(direcotryPath, playlistName, filePaths)
    logger.info(f"{YoutubeLogs.PLAYLIST_DOWNLAODED.value}: {playlistName}")
    logger.debug(f"{YoutubeLogs.DIRECTORY_PATH}: {direcotryPath}")
    fullZipPath = os.path.join(direcotryPath, zipNameFile)
    return fullZipPath


def emitHashWithDownloadedFile(fullFilePath):
    splitedFilePath = fullFilePath.split("/")
    fileName = splitedFilePath[-1]
    direcotryPath = "/".join(splitedFilePath[:-1])
    generatedHash = ''.join(random.sample(
        string.ascii_letters + string.digits, 6))
    hashTable[generatedHash] = {
        YoutubeVariables.DOWNLOAD_FILE_NAME.value: fileName,
        YoutubeVariables.DOWNLOAD_DIRECOTRY_PATH.value: direcotryPath
    }
    downloadMediaFinishEmit = DownloadMediaFinishEmit()
    downloadMediaFinishEmit.sendEmit(generatedHash)


def downloadCorrectData(youtubeURL, type, isPlaylist):
    if type == YoutubeVariables.MP3.value and isPlaylist:
        fullFilePath = downloadPlaylist(youtubeURL)
    elif type != YoutubeVariables.MP3.value and isPlaylist:
        fullFilePath = downloadPlaylist(youtubeURL, type)
    elif type == YoutubeVariables.MP3.value and not isPlaylist:
        fullFilePath = downloadSingleInfoAndMedia(youtubeURL)
    elif type != YoutubeVariables.MP3.value and not isPlaylist:
        fullFilePath = downloadSingleInfoAndMedia(youtubeURL, type)
    return fullFilePath


@socketio.on("FormData")
def socketDownloadServer(formData):
    logger.debug(formData)
    youtubeURL = formData[YoutubeVariables.YOUTUBE_URL.value]
    isPlaylist = False
    downloadErrorEmit = DownloadMediaFinishEmit()
    if YoutubeVariables.DOWNLOAD_TYP.value not in formData:
        logger.warning(YoutubeLogs.NO_FORMAT.value)
        downloadErrorEmit.sendEmitError(YoutubeLogs.NO_FORMAT.value)
        return False
    else:
        type = formData[YoutubeVariables.DOWNLOAD_TYP.value]
        logger.debug(f"{YoutubeLogs.SPECIFIED_FORMAT.value} {type}")
    if youtubeURL == "":
        logger.warning(YoutubeLogs.NO_URL.value)
        downloadErrorEmit.sendEmitError(YoutubeLogs.NO_URL.value)
    elif YoutubeVariables.URL_LIST.value in youtubeURL\
            and YoutubeVariables.URL_VIDEO.value in youtubeURL:
        logger.warning(YoutubeLogs.PLAYLIST_AND_VIDEO_HASH_IN_URL.value)
        return
    elif YoutubeVariables.URL_LIST.value in youtubeURL \
            and YoutubeVariables.URL_VIDEO.value not in youtubeURL:
        isPlaylist = True
    fullFilePath = downloadCorrectData(youtubeURL, type, isPlaylist)
    if not fullFilePath:
        return False
    download_data = getDataDict(fullFilePath)
    genereted_hash = genereteHash()
    hashTable[genereted_hash] = download_data
    emitDownloadFinish = DownloadMediaFinishEmit()
    emitDownloadFinish.sendEmit(genereted_hash)


def getDataDict(fullFilePath):
    splitedFilePath = fullFilePath.split("/")
    fileName = splitedFilePath[-1]
    direcotryPath = "/".join(splitedFilePath[:-1])
    data_dict = {"downloadFileName": fileName,
                 "downloadDirectoryPath": direcotryPath}
    return data_dict


def genereteHash():
    return ''.join(random.sample(string.ascii_letters + string.digits, 6))


@app.route("/downloadFile/<name>")
def downloadFile(name):
    downloadFileName = yt_dlp.utils.sanitize_filename(
        hashTable[name][YoutubeVariables.DOWNLOAD_FILE_NAME.value])
    downloadedFilePath = hashTable[name][YoutubeVariables.DOWNLOAD_DIRECOTRY_PATH.value]
    print(downloadFileName, downloadedFilePath)
    fullPath = os.path.join(downloadedFilePath, downloadFileName)
    logger.info(YoutubeLogs.SENDING_TO_ATTACHMENT.value)
    return send_file(fullPath, as_attachment=True)


@socketio.on("downloadFromConfigFile")
def downloadConfigPlaylist(formData):
    print(formData)
    playlistName = formData["playlistToDownload"]
    logger.info(f"Selected playlist form config {playlistName}")
    playlistURL = configParserMenager.getPlaylistUrl(playlistName)
    print(playlistURL, "test")
    fullFilePath = downloadPlaylist(playlistURL)
    if not fullFilePath:
        return False
    emitHashWithDownloadedFile(fullFilePath)


@socketio.on("addPlaylist")
def addPlalistConfig(formData):
    print(formData)
    playlistName = formData["playlistName"]
    playlistURL = formData["playlistURL"]
    print(playlistName, playlistURL)
    configParserMenager.addPlaylist(playlistName, playlistURL)
    playlistList = list(configParserMenager.getPlaylists().keys())
    socketio.emit("uploadPlalists", {"data": {"plalistList": playlistList}})


@socketio.on("deletePlaylist")
def deletePlalistConfig(formData):
    playlistName = formData["playlistToDelete"]
    configParserMenager.deletePlaylist(playlistName)
    playlistList = list(configParserMenager.getPlaylists().keys())
    socketio.emit("uploadPlalists", {"data": {"plalistList": playlistList}})


@app.route("/modify_playlist.html")
def modify_playlist_html():
    playlistList = configParserMenager.getPlaylists()
    return render_template("modify_playlist.html", playlistsNames=playlistList.keys())


@app.route("/youtube.html")
def youtube_html():
    return render_template("youtube.html")
