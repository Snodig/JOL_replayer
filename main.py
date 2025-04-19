#! python3

'''
 * Date: 2025-04-06
 * Desc: Replay visualizer for JOL games
 * Author: H. Skjevling
'''

from datetime import datetime
import traceback
import sys
import os
#import threading

from GameParser import GameHistory

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class BorderedBox(QWidget):
    def __init__(self, color=None):
        super().__init__()
        self.setStyleSheet("border: 1px solid " + (color if color !=None else "grey"))

class Card(BorderedBox):
    def __init__(self, cardNum, carddata):
        super().__init__()

        self.setMinimumHeight(25)

        layout:QHBoxLayout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        #print(carddata)
        number:QLabel = QLabel(cardNum)
        name:QLabel = QLabel(carddata["name"])
        layout.addWidget(number, 0)
        layout.addWidget(name, 1)

        self.update(carddata)

    def update(self, carddata):
        pass

class Region(BorderedBox):
    def __init__(self, parent, regionName):
        super().__init__("blue")

        self.name = regionName

        layout:QVBoxLayout = QVBoxLayout(self)

        name:QLabel = QLabel(regionName)
        name.setAlignment(Qt.AlignCenter)
        font:QFont = name.font()
        font.setPointSize(12)
        name.setFont(font)

        self.cardlistWidget = QWidget()
        cardlistLayout:QVBoxLayout = QVBoxLayout(self.cardlistWidget)
        cardlistLayout.setSpacing(2)
        cardlistLayout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(name, 0, Qt.AlignTop)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.cardlistWidget)

        layout.addWidget(self.scrollArea)

    def clear(self):
        while self.cardlistWidget.layout().count() > 0:
            child = self.cardlistWidget.layout().takeAt(0) # Hacky af
            if child.widget():
                child.widget().deleteLater()

    # TODO: Gotta be a smarter way to recursively add cards here, but this works for now
    # TODO: To get the real order of cards, we need to look at the playerData.
    # The "cards" struct lists them in an arbitrary order.
    # getRegionContents may also need to be refactored to reflect this.
    def addCards(self, carddata, currentParent = None, parentNums = None):
        cardNum = 1

        if currentParent == None:
            for c1 in carddata:
                isTopLevel = True
                for c2 in carddata:
                    if "cards" in c2.keys() and c1["id"] in c2["cards"]:
                        isTopLevel = False
                        break

                if isTopLevel: # Top level cards are present in the regions data, so could use that
                    fullNum = (str(cardNum) if not parentNums else parentNums + "." + str(cardNum))
                    #self.layout().addWidget(Card(str(fullNum), c1))
                    self.cardlistWidget.layout().addWidget(Card(str(fullNum), c1))
                    self.addCards(carddata, c1["id"], fullNum)
                    cardNum += 1
        else:
            for c1 in carddata:
                if c1["id"] == currentParent and "cards" in c1.keys():
                    for c2 in carddata:
                        if c2["id"] in c1["cards"]:
                            fullNum = parentNums + "." + str(cardNum)
                            #self.layout().addWidget(Card(str(fullNum), c2))
                            self.cardlistWidget.layout().addWidget(Card(str(fullNum), c2))
                            self.addCards(carddata, c2["id"], fullNum)
                            cardNum += 1

class PlayerPanel(BorderedBox):
    def __init__(self, playerName):
        super().__init__()

        self.setMinimumHeight(500)

        layout:QVBoxLayout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.name:QLabel = QLabel(playerName)
        self.name.setAlignment(Qt.AlignCenter)
        font:QFont = self.name.font()
        font.setPointSize(24)
        self.name.setFont(font)
        self.name.setMaximumHeight(50)
        self.layout().addWidget(self.name)

        self.regions = list()
        self.addRegion(playerName, "Hand", False)
        self.addRegion(playerName, "Ready", False)
        self.addRegion(playerName, "Uncontrolled", False)
        self.addRegion(playerName, "Ash heap", False)
        #self.addRegion(playerName, "Library", False)
        #self.addRegion(playerName, "Crypt", False)
        self.addRegion(playerName, "Research", True)

    def addRegion(self, playerName, regionName, hidden=False):
        region:Region = Region(self, regionName)
        self.regions.append(region)
        if(hidden):
            region.hide() # looks dumb, but region.setHidden does wonky things during initialization
        self.layout().addWidget(region)

    def loadTurn(self, turn, player):
        playerData = s_game.getPlayerData(player)
        namePlateText = playerData["name"] + " (" + str(playerData["pool"]) + ")"
        if playerData["victoryPoints"] != 0.0:
            namePlateText += (" - " + str(playerData["victoryPoints"]) + " VP")
        self.name.setText(namePlateText)
        #print(turn, player)
        for r in self.regions:
            if r.name not in ("Library", "Crypt") or True:
                cards = s_game.getRegionContents(player, r.name) # TODO: Refactor relationship between instances
                r.clear()
                r.addCards(cards)

    def setCurrentPlayer(self, current):
        if current:
            self.name.setStyleSheet("background-color: lightblue")
        else:
            self.name.setStyleSheet("")

class Table(QWidget):
    def __init__(self, initialState):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.players = list()

        for player in initialState["playerOrder"]:
            print(player)
            p:PlayerPanel = PlayerPanel(player)
            self.players.append(p)
            self.layout().addWidget(p)

        self.loadTurn(1, 1, None, None)

    def loadTurn(self, turn, player, state, actions):
        print("Loading turn", turn, player)
        for p in self.players:
            p.loadTurn(turn, self.players.index(p)+1)
            p.setCurrentPlayer(self.players.index(p)+1 == player)
       # while self.layout().count():
       #     child = self.layout().itemAt(0)
       #     if child.widget():
       #         child.widget().deleteLater()

    def poolChanged(self, player, change):
        pass

    def actionChanged(self):
        pass

class FugueIcon(QIcon):
    def __init__(self, filepath):
        if not "/" in filepath:
            filepath = "icons/" + filepath
        if not filepath.endswith(".png"):
            filepath += ".png"
        super().__init__("res/fugue/"+filepath)

class ChatPanel(QTextEdit):
    def __init__(self, actions):
        super().__init__()
        with open("jol.css", "r") as f:
            self.setStyleSheet(f.read())
        self.setReadOnly(True)
        self.loadTurn(1, None, None, actions)

    def loadTurn(self, turn, player, state, actions):

        # TODO: Iterating through actions (not including chats?)

        chatLines = list()
        for lines in actions:
            line = "<span>"

            line += '<span style="color: #888;font-size: smaller;">' + lines['timestamp'] + "</span> "

            if "source" in lines:
                line += "<b>"+lines["source"] + "</b> "

            line += lines['message']
            line += "</span>"
            chatLines.append(line)

        self.setText("<br>".join(chatLines))

    def actionChanged(self):
        pass

class PlayPauseButton(QPushButton):
    stateChanged = pyqtSignal(bool, name="stateChanged")

    def __init__(self):
        super().__init__(icon=FugueIcon("control"))
        self.playing:bool = False
        self.playIcon = FugueIcon("control")
        self.pauseIcon = FugueIcon("control-pause")
        self.clicked.connect(self.togglePlayPause)

    def togglePlayPause(self):
        self.playing = (not self.playing)
        self.setIcon(self.pauseIcon if self.playing else self.playIcon)
        self.stateChanged.emit(self.playing)

class ReplayControls(QWidget):
    resumePlay = pyqtSignal(name="resumePlay")
    pausePlay = pyqtSignal(name="pausePlay")
    nextTurn = pyqtSignal(name="nextTurn")
    previousTurn = pyqtSignal(name="previousTurn")
    nextAction = pyqtSignal(name="nextAction")
    previousAction = pyqtSignal(name="previousAction")

    def __init__(self):
        super().__init__()

        btn_playPause:PlayPauseButton = PlayPauseButton()
        btn_nextTurn:QPushButton = QPushButton(icon=FugueIcon("control-skip"))
        btn_previousTurn:QPushButton = QPushButton(icon=FugueIcon("control-skip-180"))
        btn_nextAction:QPushButton = QPushButton(icon=FugueIcon("control-double"))
        btn_previousAction:QPushButton = QPushButton(icon=FugueIcon("control-double-180"))

        btn_playPause.stateChanged.connect(lambda state: self.resumePlay.emit() if state else self.pausePlay.emit())
        btn_nextTurn.clicked.connect(lambda: self.nextTurn.emit())
        btn_previousTurn.clicked.connect(lambda: self.previousTurn.emit())
        btn_nextAction.clicked.connect(lambda: self.nextAction.emit())
        btn_previousAction.clicked.connect(lambda: self.previousAction.emit())

        layout:QHBoxLayout = QHBoxLayout()
        layout.addWidget(btn_previousTurn)
        layout.addWidget(btn_previousAction)
        layout.addWidget(btn_playPause)
        layout.addWidget(btn_nextAction)
        layout.addWidget(btn_nextTurn)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JOL Replay")

        global s_currentTurn #temp
        s_currentTurn = "8-2"
        global s_game
        s_game = GameHistory(sys.argv[1])

        controls:ReplayControls = ReplayControls()

        # Not sure where these connect yet
        #replayControls.resumePlay.connect()
        #replayControls.pausePlay.connect()

        state = s_game.getState()
        actions = s_game.getActions()
        table:Table = Table(state)
        chat:ChatPanel = ChatPanel(actions)

        s_game.turnChanged.connect(chat.loadTurn)
        s_game.turnChanged.connect(table.loadTurn)

        controls.nextTurn.connect(s_game.nextTurn)
        controls.previousTurn.connect(s_game.previousTurn)
        controls.nextAction.connect(s_game.nextAction)
        controls.previousAction.connect(s_game.previousAction)

        s_game.poolChanged.connect(table.poolChanged)

        layout:QVBoxLayout = QVBoxLayout()
        layout.addWidget(chat)
        layout.addWidget(controls)
        layout.addWidget(table)

        mainWidget:QWidget = QWidget()
        mainWidget.setLayout(layout)
        self.setCentralWidget(mainWidget)

def main():
    try:
        t0:time.struct_time = datetime.today()
        
        if(len(sys.argv) == 1):
            sys.argv.append("Cranky awing Female")
            #print("main.py <path-to-game-dir>")
            #return 1;

        app:QApplication = QApplication(sys.argv)
        window:QMainWindow = MainWindow()
        window.setMinimumSize(2000,800)
        window.show()
        return app.exec()

    except KeyboardInterrupt:
        print("\n-- Ctrl^C ---")

    except:
        print("\n")
        traceback.print_exc()

    finally:
        totalTime = datetime.today() - t0
        print(f"Running since \t {t0}")
        print(f"Time is now\t\t {datetime.today()} ({totalTime} seconds)")

if __name__ == "__main__":
    exit(main())