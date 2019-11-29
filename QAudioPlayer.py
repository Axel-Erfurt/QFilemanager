#!/usr/bin/python3

from PyQt5.QtCore import (pyqtSignal, pyqtSlot, Q_ARG, QAbstractItemModel,
        QFileInfo, qFuzzyCompare, QMetaObject, QModelIndex, QObject, Qt,
        QThread, QTime, QUrl, QSettings)
from PyQt5.QtGui import qGray, QImage, QPainter, QPalette, QFont, QIcon
from PyQt5.QtMultimedia import (QAbstractVideoBuffer, QMediaContent,
        QMediaMetaData, QMediaPlayer, QMediaPlaylist)
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QFileDialog,
        QFormLayout, QHBoxLayout, QLabel, QListView, QMessageBox, QPushButton,
        QSizePolicy, QSlider, QStyle, QToolButton, QVBoxLayout, QWidget, QStyleFactory, QStatusBar)

class PlaylistModel(QAbstractItemModel):
    Title, ColumnCount = range(2)

    def __init__(self, parent=None):
        super(PlaylistModel, self).__init__(parent)

        self.m_playlist = None
        print("Welcome!")

    def rowCount(self, parent=QModelIndex()):
        return self.m_playlist.mediaCount() if self.m_playlist is not None and not parent.isValid() else 0

    def columnCount(self, parent=QModelIndex()):
        return self.ColumnCount if not parent.isValid() else 0

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row, column) if self.m_playlist is not None and not parent.isValid() and row >= 0 and row < self.m_playlist.mediaCount() and column >= 0 and column < self.ColumnCount else QModelIndex()

    def parent(self, child):
        return QModelIndex()

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            if index.column() == self.Title:
                location = self.m_playlist.media(index.row()).canonicalUrl()
                return QFileInfo(location.path()).fileName()

            return self.m_data[index]

        return None

    def playlist(self):
        return self.m_playlist

    def setPlaylist(self, playlist):
        if self.m_playlist is not None:
            self.m_playlist.mediaAboutToBeInserted.disconnect(
                    self.beginInsertItems)
            self.m_playlist.mediaInserted.disconnect(self.endInsertItems)
            self.m_playlist.mediaAboutToBeRemoved.disconnect(
                    self.beginRemoveItems)
            self.m_playlist.mediaRemoved.disconnect(self.endRemoveItems)
            self.m_playlist.mediaChanged.disconnect(self.changeItems)


        self.beginResetModel()
        self.m_playlist = playlist

        if self.m_playlist is not None:
            self.m_playlist.mediaAboutToBeInserted.connect(
                    self.beginInsertItems)
            self.m_playlist.mediaInserted.connect(self.endInsertItems)
            self.m_playlist.mediaAboutToBeRemoved.connect(
                    self.beginRemoveItems)
            self.m_playlist.mediaRemoved.connect(self.endRemoveItems)
            self.m_playlist.mediaChanged.connect(self.changeItems)

        self.endResetModel()

    def beginInsertItems(self, start, end):
        self.beginInsertRows(QModelIndex(), start, end)

    def endInsertItems(self):
        self.endInsertRows()

    def beginRemoveItems(self, start, end):
        self.beginRemoveRows(QModelIndex(), start, end)

    def endRemoveItems(self):
        self.endRemoveRows()

    def changeItems(self, start, end):
        self.dataChanged.emit(self.index(start, 0),
                self.index(end, self.ColumnCount))

class PlayerControls(QWidget):

    play = pyqtSignal()
    pause = pyqtSignal()
    stop = pyqtSignal()
    next = pyqtSignal()
    previous = pyqtSignal()
    changeVolume = pyqtSignal(int)
    changeMuting = pyqtSignal(bool)
    changeRate = pyqtSignal(float)

    def __init__(self, parent=None):
        super(PlayerControls, self).__init__(parent)

        self.playerState = QMediaPlayer.StoppedState
        self.playerMuted = False

        self.playButton = QToolButton(clicked=self.playClicked)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.stopButton = QToolButton(clicked=self.stop)
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stopButton.setEnabled(False)

        self.nextButton = QToolButton(clicked=self.next)
        self.nextButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaSkipForward))

        self.previousButton = QToolButton(clicked=self.previous)
        self.previousButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaSkipBackward))

        self.muteButton = QToolButton(clicked=self.muteClicked)
        self.muteButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaVolume))

        self.volumeSlider = QSlider(Qt.Horizontal, sliderMoved=self.changeVolume)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.setValue(50)
        self.volumeSlider.setStyleSheet(stylesheet(self))

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stopButton)
        layout.addWidget(self.previousButton)
        layout.addWidget(self.playButton)
        layout.addWidget(self.nextButton)
        layout.addWidget(self.muteButton)
#        layout.addStretch(0)
        layout.addWidget(self.volumeSlider)
        self.setLayout(layout)

    def state(self):
        return self.playerState

    def setState(self,state):
        if state != self.playerState:
            self.playerState = state

            if state == QMediaPlayer.StoppedState:
                self.stopButton.setEnabled(False)
                self.playButton.setIcon(
                        self.style().standardIcon(QStyle.SP_MediaPlay))
            elif state == QMediaPlayer.PlayingState:
                self.stopButton.setEnabled(True)
                self.playButton.setIcon(
                        self.style().standardIcon(QStyle.SP_MediaPause))
            elif state == QMediaPlayer.PausedState:
                self.stopButton.setEnabled(True)
                self.playButton.setIcon(
                        self.style().standardIcon(QStyle.SP_MediaPlay))

    def volume(self):
        return self.volumeSlider.value()

    def setVolume(self, volume):
        self.volumeSlider.setValue(volume)

    def isMuted(self):
        return self.playerMuted

    def setMuted(self, muted):
        if muted != self.playerMuted:
            self.playerMuted = muted

            self.muteButton.setIcon(
                    self.style().standardIcon(
                            QStyle.SP_MediaVolumeMuted if muted else QStyle.SP_MediaVolume))

    def playClicked(self):
        if self.playerState in (QMediaPlayer.StoppedState, QMediaPlayer.PausedState):
            self.play.emit()
        elif self.playerState == QMediaPlayer.PlayingState:
            self.pause.emit()

    def muteClicked(self):
        self.changeMuting.emit(not self.playerMuted)

class Player(QWidget):

    fullScreenChanged = pyqtSignal(bool)

    def __init__(self, playlist, parent=None):
        super(Player, self).__init__(parent)
        self.setStyleSheet(stylesheet(self))
        self.colorDialog = None
        self.trackInfo = ""
        self.statusInfo = ""
        self.duration = 0

        self.url = ""
        self. settings = QSettings("QAudioPlayer", "QAudioPlayer")

        self.player = QMediaPlayer()
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)

        self.player.durationChanged.connect(self.durationChanged)
        self.player.positionChanged.connect(self.positionChanged)
        self.player.metaDataChanged.connect(self.metaDataChanged)
        self.playlist.currentIndexChanged.connect(self.playlistPositionChanged)
        self.player.mediaStatusChanged.connect(self.statusChanged)
        self.player.bufferStatusChanged.connect(self.bufferingProgress)
        self.player.error.connect(self.displayErrorMessage)

        self.playlistModel = PlaylistModel()
        self.playlistModel.setPlaylist(self.playlist)

        self.playlistView = QListView()
#        self.playlistView.setSpacing(1)
        self.playlistView.setStyleSheet(stylesheet(self))
        self.playlistView.setModel(self.playlistModel)
        self.playlistView.setCurrentIndex(
                self.playlistModel.index(self.playlist.currentIndex(), 0))

        self.playlistView.activated.connect(self.jump)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, self.player.duration() / 1000)
        self.slider.setStyleSheet(stylesheet(self))

        self.labelDuration = QLabel()
        self.slider.sliderMoved.connect(self.seek)

        openButton = QPushButton("Open", clicked=self.open)
        openButton.setIcon(openButton.style().standardIcon(QStyle.SP_DialogOpenButton))

        clearButton = QPushButton("", clicked=self.clearList)
        clearButton.setFixedWidth(36)
        clearButton.setIcon(QIcon.fromTheme("edit-delete"))
        clearButton.setToolTip("clear List")

        controls = PlayerControls()
        controls.setState(self.player.state())
        controls.setVolume(self.player.volume())
        controls.setMuted(controls.isMuted())

        controls.play.connect(self.player.play)
        controls.pause.connect(self.player.pause)
        controls.stop.connect(self.player.stop)
        controls.next.connect(self.playlist.next)
        controls.previous.connect(self.previousClicked)
        controls.changeVolume.connect(self.player.setVolume)
        controls.changeMuting.connect(self.player.setMuted)
        controls.changeRate.connect(self.player.setPlaybackRate)

        self.player.stateChanged.connect(controls.setState)
        self.player.volumeChanged.connect(controls.setVolume)
        self.player.mutedChanged.connect(controls.setMuted)

        displayLayout = QHBoxLayout()
        displayLayout.addWidget(self.playlistView)

        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(openButton)
        controlLayout.addWidget(clearButton)
#        controlLayout.addStretch(1)
        controlLayout.addWidget(controls)
#        controlLayout.addStretch(1)

        layout = QVBoxLayout()
        layout.addLayout(displayLayout)
        hLayout = QHBoxLayout()
        hLayout.addWidget(self.slider)
        hLayout.addWidget(self.labelDuration)
        layout.addLayout(hLayout)
        layout.addLayout(controlLayout)

        self.statusBar = QStatusBar()
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.statusBar)
        layout.addLayout(vlayout)
        self.statusBar.showMessage("Welcome")
        self.setWindowTitle("QAudioPlayer")
        self.setMinimumSize(300, 200)
#        self.setBackgroundRole(QPalette.Window)
        self.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        self.readSettings()

        if not self.player.isAvailable():
            QMessageBox.warning(self, "Service not available",
                    "The QMediaPlayer object does not have a valid service.\n"
                    "Please check the media service plugins are installed.")

            controls.setEnabled(False)
            self.playlistView.setEnabled(False)
            openButton.setEnabled(False)
            self.colorButton.setEnabled(False)
            self.fullScreenButton.setEnabled(False)

        self.metaDataChanged()

        self.addToPlaylist(playlist)

    def readSettings(self):
        if self.settings.contains("url"):
            self.url = self.settings.value("url")
            self.addToPlaylist(self.url)

    def writeSettings(self):
        self.settings.setValue("url", self.url)

    def closeEvent(self, event):
        print("writing settings")
        self.writeSettings()
        print("goodbye ...")
        event.accept()

    def open(self):
        fileNames, _ = QFileDialog.getOpenFileNames(self, "Open Files", "/home", "Audio Files *.mp3 *.m4a *.ogg *.wav *.m3u")
        if fileNames:
            self.url = fileNames
            self.addToPlaylist(fileNames)
            print("added Files to playlist")

    def openOnStart(self, name):
        fileInfo = QFileInfo(name)
        if fileInfo.exists():
            url = QUrl.fromLocalFile(fileInfo.absoluteFilePath())
            if fileInfo.suffix().lower() == 'm3u':
                self.playlist.load(url)
            else:
                self.playlist.addMedia(QMediaContent(url))
        else:
            url = QUrl(name)
            if url.isValid():
                self.playlist.addMedia(QMediaContent(url))
        print("added Files to playlist")

    def clearList(self):
        self.playlist.clear()

    def addToPlaylist(self, fileNames):
        for name in fileNames:
            fileInfo = QFileInfo(name)
            if fileInfo.exists():
                url = QUrl.fromLocalFile(fileInfo.absoluteFilePath())
                if fileInfo.suffix().lower() == 'm3u':
                    self.playlist.load(url)
                else:
                    self.playlist.addMedia(QMediaContent(url))
            else:
                url = QUrl(name)
                if url.isValid():
                    self.playlist.addMedia(QMediaContent(url))

    def durationChanged(self, duration):
        duration /= 1000

        self.duration = duration
        self.slider.setMaximum(duration)

    def positionChanged(self, progress):
        progress /= 1000

        if not self.slider.isSliderDown():
            self.slider.setValue(progress)

        self.updateDurationInfo(progress)

    def metaDataChanged(self):
        if self.player.isMetaDataAvailable():
            self.setTrackInfo("%s - %s" % (
                    self.player.metaData(QMediaMetaData.AlbumArtist),
                    self.player.metaData(QMediaMetaData.Title)))

    def previousClicked(self):
        # Go to the previous track if we are within the first 5 seconds of
        # playback.  Otherwise, seek to the beginning.
        if self.player.position() <= 5000:
            self.playlist.previous()
        else:
            self.player.setPosition(0)

    def jump(self, index):
        if index.isValid():
            self.playlist.setCurrentIndex(index.row())
            self.player.play()

    def playlistPositionChanged(self, position):
        self.playlistView.setCurrentIndex(
                self.playlistModel.index(position, 0))

    def seek(self, seconds):
        self.player.setPosition(seconds * 1000)

    def statusChanged(self, status):
        self.handleCursor(status)

        if status == QMediaPlayer.LoadingMedia:
            self.setStatusInfo("Loading...")
        elif status == QMediaPlayer.StalledMedia:
            self.setStatusInfo("Media Stalled")
        elif status == QMediaPlayer.EndOfMedia:
            QApplication.alert(self)
        elif status == QMediaPlayer.InvalidMedia:
            self.displayErrorMessage()
        else:
            self.setStatusInfo("")

    def handleCursor(self, status):
        if status in (QMediaPlayer.LoadingMedia, QMediaPlayer.BufferingMedia, QMediaPlayer.StalledMedia):
            self.setCursor(Qt.BusyCursor)
        else:
            self.unsetCursor()

    def bufferingProgress(self, progress):
        self.setStatusInfo("Buffering %d%" % progress)

    def setTrackInfo(self, info):
        self.trackInfo = info

        if self.statusInfo != "":
             self.statusBar.showMessage("%s | %s" % (self.trackInfo, self.statusInfo))
        else:
            self.statusBar.showMessage(self.trackInfo)

    def setStatusInfo(self, info):
        self.statusInfo = info

        if self.statusInfo != "":
            self.statusBar.showMessage("%s | %s" % (self.trackInfo, self.statusInfo))
        else:
            self.statusBar.showMessage(self.trackInfo)

    def displayErrorMessage(self):
        self.setStatusInfo(self.player.errorString())

    def updateDurationInfo(self, currentInfo):
        duration = self.duration
        if currentInfo or duration:
            currentTime = QTime((currentInfo/3600)%60, (currentInfo/60)%60,
                    currentInfo%60, (currentInfo*1000)%1000)
            totalTime = QTime((duration/3600)%60, (duration/60)%60,
                    duration%60, (duration*1000)%1000);

            format = 'hh:mm:ss' if duration > 3600 else 'mm:ss'
            tStr = currentTime.toString(format) + " / " + totalTime.toString(format)
        else:
            tStr = ""

        self.labelDuration.setText(tStr)

def stylesheet(self):
    return """
Player
{
border: 1px solid #d5d5d5;
background: #729fcf;
}
QSlider::handle:horizontal 
{
background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #204a87, stop:1 #729fcf);
width: 6px;
border: 1px solid #D5D5D5;
border-radius: 0px;
}

QSlider::groove:horizontal {
border: 1px solid #444444;
height: 8px;
background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8D8D8D, stop:1 #C5C5C5);
}
QListView
{
border: 1px solid #D5D5D5;
background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #729fcf, stop:1 #204a87);
font-family: Helvetica;
font-weight: bold;
font-size: 8pt;
color: #eeeeec; 
}

QListView::item 
    {
    height: 17px; 
    }


QListView::item:selected 
{
color: #76d8ff;
background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2e3436, stop:1 #555753);
}
QListView::item:hover
{   
border: 0.5px solid #f4f4f4;
color: black;
background: qlineargradient(x1:0, y1:0, x2:1, y2:1,stop:0 #c4a000, stop:1 #fce94f);
font-weight: bold;       
        }
        QPushButton
        {
            height: 22px;
            font-family: Droid Sans;
            font-size: 8pt;
            border: 1px inset #353535;
            color: #464646; 
            border-radius: 0px;
            width: 70px;
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #729fcf, stop:1 #eeeeec);
        } 

        QPushButton::hover
        {
            border: 1px inset #353535;
            color: #ECECEC; 
            border-radius: 0px;
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #A7CEFF, stop:1 #556782);
        } 
        QPushButton::action
        {
            color: #ECECEC; 
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ef2929, stop:1 #a40000);
        } 
        QToolButton
        {
            height: 20px;
            font-family: Droid Sans;
            font-size: 8pt;
            border: 1px inset #353535;
            color: #464646; 
            border-radius: 0px;
            width: 32px;
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #729fcf, stop:1 #eeeeec);
        } 

        QToolButton::hover
        {
            color: #ECECEC; 
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #A7CEFF, stop:1 #556782);
        } 

        QToolButton::action
        {
            color: #cc0000; 
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #A7CEFF, stop:1 #556782);
        } 
        QApplication
        {
        background: #729fcf;
        border: 1px inset #353535;
        }
        QStatusBar
        {
         font-family: Droid Sans;
        font-weight: bold;
        font-size: 8pt;
        background: #729fcf;
        color: #eeeeec;
         }
        QLabel
        {
         font-family: Droid Sans;
        font-weight: bold;
        font-size: 8pt;
        color: #eeeeec;
         }
    """

#if __name__ == '__main__':
#
#    import sys
#
#    app = QApplication(sys.argv)
#    player = Player('')
#    player.setGeometry(100,100,500,250)
#    player.show()
#    player.clearList()
#    if len(sys.argv) > 1:
#        path = sys.argv[1]
#        player.openOnStart(path)
#    sys.exit(app.exec_())