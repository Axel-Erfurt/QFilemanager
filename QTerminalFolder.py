#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import getpass
import socket
from pathlib import Path
from PyQt5.QtWidgets import QWidget, QApplication, QPlainTextEdit, QMainWindow, QAction
from PyQt5.QtGui import QFont, QTextCursor, QKeySequence, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QProcess, QCoreApplication, QSettings, QEvent, QPoint, QSize, QFileInfo, QByteArray


class MainWindow(QMainWindow):
    def __init__(self, parent=None, movable=False):
        super(MainWindow, self).__init__()
        self.setAcceptDrops(True)
        self.shellWin = PlainTextEdit()
        self.setCentralWidget(self.shellWin)
        self.setGeometry(0, 0, 700, 600)
        self.setWindowTitle("QTerminal")
        self.settings = QSettings("QTerminal", "QTerminal")
        self.readSettings()

    def closeEvent(self, e):
        self.writeSettings()

    def readSettings(self):
        if self.settings.contains("commands"):
            self.shellWin.commands = self.settings.value("commands")
        if self.settings.contains("pos"):
            pos = self.settings.value("pos", QPoint(200, 200))
            self.move(pos)
        if self.settings.contains("size"):
            size = self.settings.value("size", QSize(400, 400))
            self.resize(size)

    def writeSettings(self):
        self.settings.setValue("commands", self.shellWin.commands)
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("size", self.size())

class PlainTextEdit(QPlainTextEdit):
    commandSignal = pyqtSignal(str)
    commandZPressed = pyqtSignal(str)
    startDir = ''

    def __init__(self, parent=None, movable=False):
        super(PlainTextEdit, self).__init__()
        self.installEventFilter(self)
        self.setAcceptDrops(True)
        QApplication.setCursorFlashTime(1000)
        self.process = QProcess()
        self.process.readyReadStandardError.connect(self.onReadyReadStandardError)
        self.process.readyReadStandardOutput.connect(self.onReadyReadStandardOutput)
#        global self.startDir(str)
        self.commands = []  # This is a list to track what commands the user has used so we could display them when
        # up arrow key is pressed
        self.tracker = 0
        self.setStyleSheet("QPlainTextEdit{background-color: #212121; color: #f3f3f3; padding: 8;}")
        self.verticalScrollBar().setStyleSheet("background-color: #212121;")
        self.text = None
        self.setFont(QFont("Noto Sans Mono", 8))
        self.previousCommandLength = 0

        self.copySelectedTextAction = QAction(QIcon.fromTheme("edit-copy"), "Copy", shortcut = "Shift+Ctrl+c", triggered = self.copyText)
        self.addAction(self.copySelectedTextAction)
        self.pasteTextAction = QAction(QIcon.fromTheme("edit-paste"), "Copy", shortcut = "Shift+Ctrl+v", triggered = self.pasteText)
        self.addAction(self.pasteTextAction)
        if not self.startDir == "":
            os.chdir(self.startDir)
            self.name = (str(getpass.getuser()) + "@" + str(socket.gethostname()) 
                                + ":" + str(os.getcwd()) + "$ ")
            self.appendPlainText(self.name)
        else:
            os.chdir(os.path.dirname(sys.argv[0]))
            self.name = (str(getpass.getuser()) + "@" + str(socket.gethostname()) 
                                + ":" + str(os.getcwd()) + "$ ")
            self.appendPlainText(self.name)

    def copyText(self):
        self.copy()

    def pasteText(self):
        self.paste()


    def eventFilter(self, source, event):
        if (event.type() == QEvent.DragEnter):
            event.accept()
            print ('DragEnter')
            return True
        elif (event.type() == QEvent.Drop):
            print ('Drop')
            self.setDropEvent(event)
            return True
        else:
            return False ### super(QPlainTextEdit).eventFilter(event)

    def setDropEvent(self, event):
        if event.mimeData().hasUrls():
            f = str(event.mimeData().urls()[0].toLocalFile())
            self.insertPlainText(f)
            event.accept()
        elif event.mimeData().hasText():
            ft = event.mimeData().text()
            print("text:", ft)
            self.insertPlainText(ft)
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, e):
        cursor = self.textCursor()

        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_A:
            return

        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_Z:
            self.commandZPressed.emit("True")
            return

        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_C:
            self.process.kill()
            self.name = (str(getpass.getuser()) + "@" + str(socket.gethostname()) 
                                    + ":" + str(os.getcwd()) + "$ ")
            self.appendPlainText("process cancelled")
            self.appendPlainText(self.name)
            self.textCursor().movePosition(QTextCursor.End)
            return

        if e.key() == Qt.Key_Return:
            text = self.textCursor().block().text()

            if text == self.name + text.replace(self.name, "") and text.replace(self.name, "") != "":  # This is to prevent adding in commands that were not meant to be added in
                self.commands.append(text.replace(self.name, ""))
            self.handle(text)
            self.commandSignal.emit(text)
            self.appendPlainText(self.name)

            return

        if e.key() == Qt.Key_Up:
            try:
                if self.tracker != 0:
                    cursor.select(QTextCursor.BlockUnderCursor)
                    cursor.removeSelectedText()
                    self.appendPlainText(self.name)

                self.insertPlainText(self.commands[self.tracker])
                self.tracker -= 1

            except IndexError:
                self.tracker = 0

            return

        if e.key() == Qt.Key_Down:
            try:
                cursor.select(QTextCursor.BlockUnderCursor)
                cursor.removeSelectedText()
                self.appendPlainText(self.name)

                self.insertPlainText(self.commands[self.tracker])
                self.tracker += 1

            except IndexError:
                self.tracker = 0

        if e.key() == Qt.Key_Backspace:
            if cursor.positionInBlock() <= len(self.name):
                return

        if e.key() == Qt.Key_Left:
            if cursor.positionInBlock() <= len(self.name):
                return

        if e.key() == Qt.Key_Delete:
            return

        super().keyPressEvent(e)
        cursor = self.textCursor()
        e.accept()

    def ispressed(self):
        return self.pressed

    def onReadyReadStandardError(self):
        self.error = self.process.readAllStandardError().data().decode()
        self.appendPlainText(self.error.strip('\n'))

    def onReadyReadStandardOutput(self):
        self.result = self.process.readAllStandardOutput().data().decode()
        self.appendPlainText(self.result.strip('\n'))
        self.state = self.process.state()

    def run(self, command):
        """Executes a system command."""
        if not command == "ls":
            if self.process.state() != 2:
                self.process.start(command)
                print(self.process.exitStatus())
                if not self.process.exitStatus() != 0:
                    self.textCursor().movePosition(QTextCursor.End)
                    self.name = (str(getpass.getuser()) + "@" + str(socket.gethostname()) 
                                        + ":" + str(os.getcwd()) + "$ ")
                    self.appendPlainText(self.name)
        else:
            if self.process.state() != 2:
                self.process.start(command)
                self.process.waitForFinished()

    def handle(self, command):
#        print("begin handle") 
        """Split a command into list so command echo hi would appear as ['echo', 'hi']"""
        real_command = command.replace(self.name, "")

        if command == "True":
            if self.process.state() == 2:
                self.process.kill()
                self.appendPlainText("Program execution killed, press enter")

        if real_command.startswith("python"):
            pass

        if real_command != "":
            command_list = real_command.split()
        else:
            command_list = None
        """Now we start implementing some commands"""
        if real_command == "clear":
            self.clear()

        elif command_list is not None and command_list[0] == "echo":
            self.appendPlainText(" ".join(command_list[1:]))

        elif real_command == "exit":
            quit()

        elif command_list is not None and command_list[0] == "cd" and len(command_list) > 1:
            try:
                os.chdir(" ".join(command_list[1:]))
                self.name = (str(getpass.getuser()) + "@" + str(socket.gethostname()) 
                                        + ":" + str(os.getcwd()) + "$ ")
                self.textCursor().movePosition(QTextCursor.End)

            except FileNotFoundError as E:
                self.appendPlainText(str(E))

        elif command_list is not None and len(command_list) == 1 and command_list[0] == "cd":
            os.chdir(str(Path.home()))
            self.name = (str(getpass.getuser()) + "@" + str(socket.gethostname()) 
                                    + ":" + str(os.getcwd()) + "$ ")
            self.textCursor().movePosition(QTextCursor.End)

        elif self.process.state() == 2:
            self.process.write(real_command.encode())
            self.process.closeWriteChannel()

        elif command == self.name + real_command:
            self.run(real_command)
        else:
            pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    print(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())