#! python3

'''
 * Date: 2025-04-06
 * Desc: Gamestate parser
 * Author: H. Skjevling
'''

import os
import json
import traceback

from PyQt5.QtCore import *


class GameHistory(QObject):
    turnChanged = pyqtSignal(int, int, dict, list, name="turnChanged")
    poolChanged = pyqtSignal(int, int, name="poolChanged")

    def __init__(self, gameDir):
        super().__init__()

        self.gameDir = os.path.dirname(os.path.realpath(__file__)) + "\\games\\" + gameDir
        actions = list()
        for root, dirs, files in os.walk(self.gameDir):
            for filename in files:
                actions.append(filename)

        self.turns = dict()

        actions = list(filter(lambda f: f.startswith("actions-"), actions))
        for action in actions:
            turnNums = action[len("actions-"):][:-len(".json")].split("-")
            turnNums[0] = int(turnNums[0])
            turnNums[1] = int(turnNums[1])
            if not turnNums[0] in self.turns.keys():
                self.turns[turnNums[0]] = list()
            self.turns[turnNums[0]].append(turnNums[1])

        with open(self.gameDir + "\\game-1-1.json", encoding="utf-8") as f:
            self.firstState = json.load(f)

        self.currentTurn = 1
        self.currentPlayer = 1
        self.numPlayers = len(self.getPlayers())

        # Load initially available turn data
        self.loadTurnData()

    def getPlayers(self):
        return self.firstState["playerOrder"]

    def getPlayerRegions(self, player):
        return self.firstState["players"][player]["regions"]

    def loadActions(self, turn, player):
        if not str(player).isnumeric():  # Passed a player name
            player = self.getPlayers().index(player)

        turnNum = str(turn) + "-" + str(player)

        actions = None

        try:
            with open(self.gameDir + "\\actions-" + turnNum + ".json", encoding="utf-8") as f:
                actions = json.load(f)
        except:
            traceback.print_exc()
            print("No such turn", turnNum)

        self.currentActions = actions
        self.currentActionIx = 0
        # print(len(self.currentActions["chats"]), self.currentActions["chats"])

        return self.getActions()

    def getActions(self):
        # print(self.currentActions)
        if self.currentActions is None:
            return None
        return self.currentActions["chats"][:self.currentActionIx + 1]

    def loadState(self, turn, player):
        if not str(player).isnumeric():  # Passed a player name
            player = self.getPlayers().index(player) + 1

        turnNum = str(turn) + "-" + str(player)

        state = None

        try:
            with open(self.gameDir + "\\game-" + turnNum + ".json", encoding="utf-8") as f:
                state = json.load(f)
        except:
            traceback.print_exc()
            print("No such turn", turnNum)

        self.currentState = state

        return self.getState()

    def getState(self):
        return self.currentState

    def getPlayerData(self, player):
        if str(player).isnumeric():  # Passed a player number
            player = self.getPlayers()[player - 1]

        return self.getState()["players"][player]

    def getRegionContents(self, player, region, turn=None, currentPlayer=None):
        if turn is None:
            turn = self.currentTurn
            if turn > 1:
                turn -= 1  # We want the state from the end of last turn

        if currentPlayer is None:
            currentPlayer = self.currentPlayer

        if str(player).isnumeric():  # Passed a player number
            player = self.getPlayers()[player - 1]

        region = region.upper().replace(" ", "_")
        state = self.getState()

        regionIDs = dict()  # TODO: Could be a persistent set, unless that fucks with swapped players
        for r, data in self.getPlayerData(player)["regions"].items():
            regionIDs[r.upper().replace(" ", "_")] = data["id"]

        # print(state["cards"])
        # print(list(state["cards"].items())[0])

        cards = dict(filter(lambda x: x[1]["region"] == regionIDs[region], state["cards"].items()))

        regionContents = dict()
        regionContents["region"] = state["players"][player]["regions"][region]
        regionContents["carddata"] = cards

        # if len(cards) == 0:
        #    print(f"Player {player} has no '{region}'' contents for turn {turn}")

        # if(player == "Ankha"):
        #    print(player, region, regionIDs[region], "\n", cards)

        return regionContents

    def emitTurnChanged(self):
        if self.currentState is None:
            print("Unable to get state data for turn", self.currentTurn, self.currentPlayer)
        elif self.currentActions is None:
            print("Unable to get action data for turn", self.currentTurn, self.currentPlayer)
        else:
            # print("State:", state)
            # print("Actions:", actions)
            # print("turn " + self.currentActions["turnId"], self.currentActions)
            self.turnChanged.emit(self.currentTurn, self.currentPlayer, self.getState(), self.getActions())

    def nextTurn(self, endOfTurn=False):
        if self.currentPlayer < len(self.turns[self.currentTurn]):
            self.currentPlayer += 1
            # TODO: Looks like players keep existing, but gamedata files do not
            # Need to move forward until we find a player who is still alive
        elif self.currentTurn < len(self.turns):
            # TODO: also set current player to first player alive in that turn
            self.currentPlayer = 1  # temp
            self.currentTurn += 1
        else:
            return  # No such turn

        self.loadTurnData()

        if endOfTurn and self.currentActions is not None:
            self.currentActionIx = len(self.currentActions["chats"]) - 1
        else:
            self.currentActionIx = 0

        self.emitTurnChanged()

    def previousTurn(self, endOfTurn=False):
        if self.currentPlayer > 1:
            self.currentPlayer -= 1
        elif self.currentTurn > 1:
            # TODO: also set current player to last player alive in that turn
            self.currentPlayer = 5  # temp
            self.currentTurn -= 1
        else:
            return  # At start of game

        self.loadTurnData()

        if endOfTurn and self.currentActions is not None:
            self.currentActionIx = len(self.currentActions["chats"]) - 1
        else:
            self.currentActionIx = 0

        self.emitTurnChanged()

    def loadTurnData(self):
        self.loadState(self.currentTurn, self.currentPlayer)
        self.loadActions(self.currentTurn, self.currentPlayer)

    def nextAction(self):
        if self.currentActionIx < len(self.currentActions["chats"]) - 1:
            self.currentActionIx += 1
            self.emitTurnChanged()  # TODO: This probably won't cut it once actions are parsed to determine state
        else:
            self.nextTurn()

        print(self.getActions()[-1])

    def previousAction(self):
        if self.currentActionIx > 0:
            self.currentActionIx -= 1
            self.emitTurnChanged()
        else:
            self.previousTurn(True)

        print(self.getActions()[-1])
