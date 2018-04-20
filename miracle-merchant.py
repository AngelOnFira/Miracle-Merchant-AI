
# coding: utf-8

# In[323]:


# Imports

from random import shuffle
import csv
import re
import copy
import random
import itertools
import time
import numpy as np
from plotly.offline import download_plotlyjs, init_notebook_mode, plot,iplot
import pylab as plt
import threading, Queue

init_notebook_mode(connected=True)
import plotly.graph_objs as go


# In[309]:


# Functions

# Get all if the possible ways to play a hand
# out - a list of all permutations
def getTurnPermutations():
    baseString = [4, 1, 4, 2, 4, 3, 4, 4]
    currPerm = [0] * 8
    permList = []
    
    finishPerm = False
    while (not finishPerm):
        for i in range(8):
            pos = 7 - i
            if (currPerm[pos] / baseString[pos] == 1):
                if (pos == 0):
                    finishPerm = True
                    break
                currPerm[pos] = 0
                currPerm[pos - 1] += 1
        permList.append(''.join(str(e) for e in currPerm))
        currPerm[7] += 1
    
    return permList[:-1]

# Make sure that there are always enough cards
# left to finish the game
# in - the loaded game state
# out - a list to reference if a card can be played
def getPlayRestrictions(game):
    restrictions = [
        [-1] * 13,
        [-1] * 13,
        [-1] * 13,
        [-1] * 13
    ]
    cardCount = [0]*4
    
    for turn, need in enumerate(list(reversed(game[4]))):
        i = colorToNum(need)
        
        if (need == 'D'):
            minFound = -1
            minIndex = 0
            for deck in range(4):
                for index in range(13):
                    if (game[deck][12 - index][1] == "D"):
                        if (index < minFound or minFound == -1):
                            minFound = index
                            minIndex = deck
                            break
            
            restrictions[minIndex][12 - minFound] = 12 - turn
        else:
            while(game[i][12 - cardCount[i]][1] == "D"):
                cardCount[i] += 1
            
            restrictions[i][12 - cardCount[i]] = 12 - turn
            cardCount[i] += 1
    return restrictions

# Play a hand to test if everything is working
# in - the test in the form of a hand
# in - the proper answer
# in - the instance of test that this is
# in - if debug info should be shown
def playTest(thisTest, verify, testNum, debug=False):
    
    result = []
    for card in thisTest:
        cardCopy = copy.deepcopy(card)
        
        playCard(result, cardCopy[0], cardCopy[1])
        if (debug):
            printHand(result)
            print "\n"
        
    if (not result == verify):
        if (debug == False):
            unitTest(thisTest, verify, testNum, True)
        
        print "This test's output"
        print result
        print ""
        
        printHand(result)
        print "--------------------------------"
        print "should be"
        print "--------------------------------"
        printHand(verify)
        
        raise ValueError('Test ' + str(testNum) + ' Failed.\n')
        
# Calculate the total points of a hand to test
# in - the test in the form of a hand
# in - the color needed for this hand
# in - the color loved for this hand
def pointTest(thisHand, colorNeeded, colorLoved, verify, testNum, debug=False):
    
    result = countPoints(thisHand, colorNeeded, colorLoved)
    
    if (not result == verify):
        raise ValueError('Wanted ' + str(verify) + ' got ' + str(result))
        
# Play a card onto the table
# in - array of cards on the table
# in - card just played
# in - position that the card was played at
# out - updated cards on table
def playCard(playedCards, currCard, position):
    
    cardColor = currCard[1]
    cardLeft = currCard[2]
    cardMiddle = currCard[3]
    cardRight = currCard[4]
    playedCards.insert(position, currCard)
    
    oldPoints = []
    for i in range(len(playedCards)):
        oldPoints.append(playedCards[i][0])
    
    # Go through each card left to right
    for i, card in enumerate(playedCards):

        # See if this card's middle is the card just added
        if (card[3] == cardColor):
            if (cardColor == 'D'):
                playedCards[position][0] += 1
            else:
                card[0] += 1
        
        # See if this card is the played card's middle
        if (card[1] == cardMiddle and not i == position):
            if (cardMiddle == 'D'):
                card[0] += 1
            else:
                playedCards[position][0] += oldPoints[i]

        # The card to the left of the card just played
        if (i == position - 1):
            if (playedCards[i][4] == cardColor):
                if (cardColor == 'D'):
                    playedCards[position][0] += 1
                else:
                    card[0] += 1

        # The card to the right of the card just played
        if (i == position + 1):
            if (playedCards[i][2] == cardColor):
                if (cardColor == 'D'):
                    playedCards[position][0] += 1
                else:
                    card[0] += 1

        # The card just played
        if (i == position):
            if (i > 0):
                if (playedCards[i - 1][1] == cardLeft):
                    if (cardLeft == 'D'):
                        playedCards[position - 1][0] += 1
                    else:
                        card[0] += oldPoints[i - 1]
            if (i < len(playedCards) - 1):
                if (playedCards[i + 1][1] == cardRight):
                    if (cardRight == 'D'):
                        playedCards[position + 1][0] += 1
                    else:
                        card[0] += oldPoints[i + 1]

# Calculate the score of a hand
# in - array of cards on the table
# in - the needed color
# in - the loved color
# out - points from this hand
def countPoints(playedCards, need, love):
    if (not len(playedCards) == 4):
        raise ValueError('There are not 4 cards in this hand, there are ' + str(len(playedCards)))
        
    cardColors = []
    needCard = False
    loveCard = False
    darkCard = False
    points = 0
    
    # Put each card color into an array, make
    # sure the needed color was used and
    # add any points from cards
    for card in playedCards:
        thisColor = card[1]
        cardColors.append(thisColor)
        
        multiplier = 1
        if (thisColor == need):
            needCard = True
        if (thisColor == love):
            multiplier = 2
            loveCard = True
        if (thisColor == 'D'):
            darkCard = True
            
        points += card[0] * multiplier
        
    unique = len(list(set(cardColors))) == len(cardColors)
    
    # Return if the needed color was not used
    if (not needCard):
        return -1
    
    # Check if there are any bonus for this hand
    
    # Check if all the cards are the same
    if (cardColors[0] == cardColors[1] == cardColors[2] == cardColors[3]):
        points += 8
    # Check if 3 of the 4 cards are the same
    elif (cardColors[0] == cardColors[1] == cardColors[2] or cardColors[1] == cardColors[2] == cardColors[3]):
        if (loveCard):
            points += 8
        else:
            points += 4
    else:
        # Keep track if we will need to look at the rainbow bonus
        shouldCheckRainbow = True
        
        # Check if there is a pair
        for i in range(0, 3):
            if (cardColors[i] == cardColors[i + 1]):
                if (cardColors[i] == love):
                    points += 4
                else:
                    points += 2
                shouldCheckRainbow = False
        
        if (shouldCheckRainbow):
            if (not darkCard and unique):
                if (love == 'D'):
                    points += 3
                else:
                    points += 6
    
    return points

# Print a hand visually
# in - array of the hand
def printHand(hand):
    score = ""
    color = ""
    bottom = ""
    
    for card in hand:
        left = ' ' if str(card[2]) == 'N' else str(card[2])
        middle = ' ' if str(card[3]) == 'N' else str(card[3])
        right = ' ' if str(card[4]) == 'N' else str(card[4])
        
        if (card[1] == 'R'):
            score += "\x1b[31m"
            color += "\x1b[31m"
            bottom += "\x1b[31m"
        elif (card[1] == 'G'):
            score += "\x1b[32m"
            color += "\x1b[32m"
            bottom += "\x1b[32m"
        elif (card[1] == 'B'):
            score += "\x1b[34m"
            color += "\x1b[34m"
            bottom += "\x1b[34m"
        elif (card[1] == 'Y'):
            score += "\x1b[33m"
            color += "\x1b[33m"
            bottom += "\x1b[33m"
        elif (card[1] == 'D'):
            score += "\x1b[30m"
            color += "\x1b[30m"
            bottom += "\x1b[30m"
        
        score += "|" + (' ' if card[0] >= 0 and card[0] < 10 else '') + "" + str(card[0]) + " |  "
        color += "| " + str(card[1]) + " |  "
        bottom += "|" + left + "" + middle + "" + right + "|  "
    
    score += "\x1b[30m"
    color += "\x1b[30m"
    bottom += "\x1b[30m"
        
    print score
    print color
    print bottom
    print ""
    
# Read a CSV to a list
# in - the filename to load
# out - a list of the game
def readCSV(filename):
    with open(filename, 'rb') as f:
        reader = csv.reader(f)
        your_list = list(reader)
    
    deck = [[], [], [], [], [], []]
    for cards in your_list:
        for i, card in enumerate(cards):
            if (i < 4):
                thisCardColor = numToColor(i)

                if (card[:2] == "D "):
                    thisCardPoints = -1 * int(card[-1])
                    thisCardColor = 'D'
                    thisCardLeft = thisCardMiddle = thisCardRight = 'N'
                else:
                    thisCardLeft = card[0]
                    thisCardMiddle = card[1]
                    thisCardRight = card[2]

                    thisCardPoints = 1

                thisCard = [
                    thisCardPoints,
                    thisCardColor,
                    thisCardLeft,
                    thisCardMiddle,
                    thisCardRight
                ]
                deck[i].append(thisCard)
            else:
                deck[i].append(card)
    return deck

# Generate a new game
# out - a new game array
def makeGame():
    startOrder = ['B', 'B', 'B', 'G', 'G', 'G', 'Y', 'Y', 'Y', 'R', 'R', 'R', 'D']

    needOrder = copy.deepcopy(startOrder)
    while (needOrder[0] == 'D' or needOrder[-1] == 'D'):
        shuffle(needOrder)

    loveOrder = copy.deepcopy(startOrder)
    while (loveOrder[0] == 'D' or loveOrder[-1] == 'D'):
        shuffle(loveOrder)
        
    placesToTake = []
    for piles in range(4):
        
        thisPile = []
        for cards in range(13):
            thisPile.append(cards)
        shuffle(thisPile)
        placesToTake.append(thisPile)
    
    game = [[0] * 13, [0] * 13, [0] * 13, [0] * 13]

    for pile in range(4):
        
        first = random.randint(1, 5)
        second = random.randint(first + 3, 8)
        third = random.randint(second + 3, 11)
        
        game[pile][first] = [-3, 'D', 'N', 'N', 'N']
        game[pile][second] = [-2, 'D', 'N', 'N', 'N']
        game[pile][third] = [-1, 'D', 'N', 'N', 'N']
        
        placesToTake[pile].remove(first)
        placesToTake[pile].remove(second)
        placesToTake[pile].remove(third)
        
    for pile in range(4):
        
        color = numToColor(pile)
            
        NNNpos = placesToTake[pile].pop(0)
        game[pile][NNNpos] = [1, color, 'N', 'N', 'N']
        
        XNXpos = placesToTake[pile].pop(0)
        colorChoose = ['B', 'G', 'Y', 'R', 'D']
        shuffle(colorChoose)
        game[pile][XNXpos] = [1, color, colorChoose.pop(0), 'N', colorChoose.pop(0)]
        
        for middle in range(2):
            
            NXNpos = placesToTake[pile].pop(0)
            colorChoose = ['B', 'G', 'Y', 'R', 'D']
            shuffle(colorChoose)
            game[pile][NXNpos] = [1, color, 'N', colorChoose.pop(0), 'N']
            
        while (len(placesToTake[pile]) > 0):
            
            pos = placesToTake[pile].pop(0)
            colorChoose = ['B', 'G', 'Y', 'R', 'D']
            shuffle(colorChoose)
            
            if (random.randint(0, 1)):
                left = colorChoose.pop(0)
                right = 'N'
            else:
                right = colorChoose.pop(0)
                left = 'N'
            
            game[pile][pos] = [1, color, left, 'N', right]
    
    game.append(needOrder)
    game.append(loveOrder)
    return game

# Translate a color to a number
# in - the color to be transformed
# out - the number that represents the color
def colorToNum(color):
    if (color == 'B'):
        return 0
    elif(color == 'G'):
        return 1
    elif(color == 'Y'):
        return 2
    elif(color == 'R'):
        return 3
    elif(color == 'D'):
        return 4

# Translate a number to a color
# in - the number to be transformed
# out - the color that represents the number
def numToColor(num):
    if (num == 0):
        return 'B'
    elif(num == 1):
        return 'G'
    elif(num == 2):
        return 'Y'
    elif(num == 3):
        return 'R'
    elif(num == 4):
        return 'D'
    
def timeFunction(fun):
    start_time = time.time()
        
    print (time.time() - start_time)
    playCard(hand, cardToPlay, posToPlay)

# In[330]:


# Method 2

def method2(verbose=False, fileout=False):
    print "entered method 2"
    #game = readCSV("GameData/game.csv")
    game = makeGame()
    restrictions = getPlayRestrictions(game)
    gameCardsTaken = [0]*4
    gameScore = 0

    # Play each of the 13 game hands
    for hands in range(13):

        maxFound = 0
        maxIndex = 0
        permList = getTurnPermutations()
        permScoreList = []

        # Play each permutation of this hand
        for permCount, perm in enumerate(permList):
            
            shouldEnter = True
            # See if we can skip this loop because the needed color
            # is not in this permutation
            needed = str(colorToNum(game[4][hands]))
            needs = [perm[0], perm[2], perm[4], perm[6]]
            if (needed not in needs and needed != 4):
                permScoreList.append([-1, perm])
                shouldEnter = True
                
            hand = []
            cardsTaken = copy.deepcopy(gameCardsTaken)
            shouldTally = True

            if (shouldEnter):
                for i in range(4):
                    pile = int(perm[i * 2])

                    if (cardsTaken[pile] > 12):
                        shouldTally = False
                        break

                    # Verify that there are enough of a color left to make it
                    # to the end of the game
                    cardToPlay = copy.deepcopy(game[pile][cardsTaken[pile]])
                    if (not hands >= restrictions[pile][cardsTaken[pile]]):
                        shouldTally = False
                        break

                    cardsTaken[pile] += 1
                    posToPlay = int(perm[i * 2 + 1])

                    playCard(hand, cardToPlay, posToPlay)

                if (shouldTally):
                    total = countPoints(hand, game[4][hands], game[5][hands])

                    permScoreList.append([total, perm])

                    if (total > maxFound):
                        maxFound = total
                        maxIndex = permCount
                else:
                    permScoreList.append([-1, perm])
        permScoreList.sort()
        permScoreList = list(reversed(permScoreList))

        gameScore += maxFound

        hand = []
        for i in range(4):
            pile = int(permList[maxIndex][i * 2])

            try:
                cardToPlay = game[pile][gameCardsTaken[pile]]
            except:
                print pile, gameCardsTaken[pile], gameCardsTaken, gameScore, maxFound
                return - 1
                
            posToPlay = int(permList[maxIndex][i * 2 + 1])

            playCard(hand, cardToPlay, posToPlay)
            
            if (verbose):
                printHand(hand)
                
            gameCardsTaken[pile] += 1
        
        if (verbose):
            print "---------"
            print "This hand score: " + str(maxFound)
            print "Current game score: " + str(gameScore)
            print "---------"
    if (verbose):
        print "---------"
        print "Final score: " + str(gameScore)
    
    if (fileout):
        with open("out.txt", "a") as myfile:
            myfile.write(str(gameScore) + "\n")
    else:
        return gameScore
    
method2()
while (True):
    method2(fileout=True)