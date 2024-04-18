class SingleMedia {
    constructor(title, artist, url) {
        this.title = title;
        this.artist = artist;
        this.url = url;
    }
}

class PlaylistMedia {
    constructor(playlistName, trackList){
        this.playlistName = playlistName;
        this.trackList = trackList;
    }
}

class FlaskResultHash{
    constructor(hash) {
        this.hash = hash
    }
}

class MessageManager{
    constructor (requestJson){
        this.requestJson = requestJson;
    }

    isError(){
        if ("error" in this.requestJson){
            return true
        }
        return false
    }

    getError(){
        if ("error" in this.requestJson){
            return this.requestJson["error"]
        }
    }

    convertMessageToData(){
        
    }
    
    getData(){
        if ("data" in this.requestJson){
            return this.convertMessageToData(this.requestJson["data"])
        }
    }
}

class PlaylistMediaEmit extends MessageManager {
    static emitMsg = "playlistMediaInfo"

    constructor(requestJson){
        super(requestJson)
    }
    

    convertMessageToData(data) {
        var playlistName = data["playlist_name"]
        var trackList = data["trackList"]
        var singleMediaArr = []
        console.log(trackList)
        console.log(typeof(trackList))
        for (track of trackList) {
            console.log(track)
            singleMediaArr.push(new SingleMedia(track["title"],
                                            track["artist"],
                                            track["url"]))
        return new PlaylistMedia(playlistName, singleMediaArr)
       }
    }
}

class SingleMediaEmit extends MessageManager {
    static emitMsg = "mediaInfo"

    constructor(requestJson){
        super(requestJson)
    }
    
    convertMessageToData(requestJson) {
        var singleMediaData = requestJson["data"]
        return new SingleMedia(singleMediaData["title"],
                           singleMediaData["artist"],
                           singleMediaData["url"])
    }
}




$(document).ready(function () {
    var socket = io();
    console.log("ready")
    socket.on('connect', function () {
        console.log("Connected Youtube");
    });
    var downloadForm = document.getElementById("DownloadForm");
    downloadForm.addEventListener("submit", function (event) {
        event.preventDefault();
        // allLogs = "";
        var traks_urls_table = document.getElementById("downloadInfo");
        traks_urls_table.innerHTML = "";
        var download_file_button = document.getElementById("downloadSection");
        download_file_button.innerHTML = "";
        var youtubeURL = document.getElementById("youtubeURL");
        var downloadTypes = document.getElementsByName("qualType");
        for (var i = 0; i < downloadTypes.length; i++) {
            if (downloadTypes[i].checked == true) {
                var downloadType = downloadTypes[i].value;
                console.log(downloadType)
                break;
            }
        }
        socket.emit("FormData", {
            "youtubeURL": youtubeURL.value,
            "downloadType": downloadType
        });
        return true
    })

    socket.on("downloadMediaFinish", function (response) {
        if ("error" in response) {
            console.log("Error", response["error"])
        }
        else {
            var downloadSection = document.getElementById("downloadSection")
            var fileHash = response["data"]["HASH"]
            console.log(fileHash)
            downloadSection.innerHTML = "<br><a href=/downloadFile/" + fileHash + " class='neon-button'>Download File</a>"
        }
    })

    

    socket.on(PlaylistMediaEmit.emitMsg, function (response) {
        // console.log("InProgress", response["data"])
        var table = document.getElementById("downloadInfo")
        var playlistMediaEmit = new PlaylistMediaEmit(response)
        console.log(playlistMediaEmit)
        if (playlistMediaEmit.isError()){
            console.log(playlistMediaEmit.getError())
            return
        }
        var playlistMedia = playlistMediaEmit.getData()
        console.log(playlistMedia.trackList)
        for (singleMedia of playlistMedia.trackList) {
            var row = table.insertRow()
            var cell = row.insertCell()
            var cell2 = row.insertCell()
            var cell3 = row.insertCell()
            cell.innerHTML = singleMedia.artist
            cell2.innerHTML = singleMedia.title
            console.log(singleMedia.artist)
            console.log(singleMedia.title)
            cell3.innerHTML = "<a class=neon-button target='_blank' href=" + singleMedia.url + ">" + "url</a>"
        }
    })
});