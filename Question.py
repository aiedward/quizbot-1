#import GlobalConfig as conf

import glob
import re
import sqlite3
import string
import datetime
import time
from random import randint # TODO kan slettes
from random import choice

VERBOSE = True

class Question(object):

    def __init__(self, cfg):
        """
        Set up a new question object.

        @type cfg: dict
        @param cfg: Config data
        """
        self.cfg = cfg
        self.data = {}
        self.status = 'new'
        self.regex = None
        self.qid = 1 # TODO
        self.active = False # TODO control if question is active

    def getStatus(self):
        """
        @return: Status in question loop
        """        
        return self.status

    def getID(self):
        """
        TODO
        """
        return 1

    def reset(self):
        """
        Resets status for question.
        """
        self.status = 'new'
        
    def __str__(self):
        """
        @return: Question string
        """
        return self.data['Question']

    def askQuestion(self, c, n):
        """
        Returns formatted question for channel.

        @type c: string
        @param c: channel
        @type n: number
        @param n: Question number
        """
        self.status = 0
        return [(0, c, "Question {}: {}".format(n, self.__str__()))]

    def tip_n(self):
        """
        @return: Number of possible tips
        """
        tmp = len(self.data['Tip'])
        if tmp > self.cfg['max_tips']:
            return self.cfg['max_tips']
        return len(self.data['Tip'])

    def giveTip(self):
        """
        @return: Next tip if exist, else returns correct answer.
        """
        if VERBOSE: print("Len-tip: {}".format(len(self.data['Tip'])))
        if VERBOSE: print("give tip ... {}".format(self.status))
        if self.tip_n() > self.status + 1:
            self.status += 1
            return self.data['Tip'][self.status - 1]
        else:
            self.status = 'finished'
            return self.data['Answer']

            # return self.data['Tip']
        
    def stringToQuestion(self, qstring, source):
        """
        Creates question from string.

        @type qstring: string
        @param qstring: Question formatted as string
        @type source: string
        @param source: Source name of string
        """
        #print("stringToQuestion: {}".format(qstring))
        tmp = qstring.splitlines()
        self.data = dict([l.strip() for l in line.split(':',1)] for line in tmp if line != '' and line[0:3] != 'Tip')
        self.data['Tip'] = [ line[4:].strip() for line in tmp if line[0:3] == 'Tip']
        if len(self.data['Tip']) == 0:
            self.data['Tip'] = self.createTip(self.data['Answer'])
        self.data['Source'] = source
        if 'Regexp' in self.data:
            self.regex = re.compile(self.data['Regexp'], re.IGNORECASE)
        else:
            self.regex = re.compile(self.data['Answer'], re.IGNORECASE)
        #print self.data

    def createTip(self, qstring):
        """
        Creates tips.
        TODO: Improve tips - ignore whitespace.

        @return: list of tips.
        """
        tmp = []
        i = 0
        while i < len(qstring) and i < self.cfg['tip_freq']:
            tmp.append(''.join(c if (j-i) % self.cfg['tip_freq'] == 0 or c == ' ' else '.' for j,c in enumerate(qstring)))
            i += 1
            #print tmp
        return tmp[:-1]
