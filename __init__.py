# -*- coding: utf-8 -*-

# Quiz-plugin for DasBot
# Copyright (C) 2013 Trond Thorbjørnsen

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import sqlite3
import string
import datetime
import time
from random import randint # TODO kan slettes
from random import choice
from Quiz import Quiz

TIME_VALUE = { 'd':86400,
        'h':3600,
        'm':60,
        's':1}

class Plugin(object):
    # TODO: Sjekk at cron er aktivert

    def __init__(self, **kwargs):
        self.quizzes = {}
        self.jobs = {}
        self.count = 0
        self.del_job = None
        self.new_job = None
        self.pluginconf = kwargs['config']
        self.VERBOSE = kwargs['verbose']
        
    def listen(self, msg, channel, **kwargs):
        if channel in self.quizzes:
            tmp = self.quizzes[channel].listen(msg, channel, kwargs['from_nick'])
            print tmp
            if tmp[0] == True:
                print("LISTEN: {}".format( tmp[1]))
                for i in self.jobs[channel]:
                    self.del_job(i) # kwargs['del_job'] does not work
                #return tmp[1]
                self.jobs[channel] = []
                self.quizNewRound(channel)
                return tmp[1]

    def cmd(self, command, args, channel, **kwargs):
        if command == 'q-rank':
            if channel in self.quizzes:
                rank = []
                ranklist = self.quizzes[channel].getRank()
                #print("Q-RANK: {}".format(tmp))
                #if len(tmp) == 0:
                #    return [(0, channel, "Ingen har svart rett foreløpig!")]
                #ranklist = [(v,k) for k,v in tmp.items()]
                ranklist.sort(reverse=True)
                for i, item in enumerate(ranklist):
                    rank.insert(0, (0, channel, "{}. {} ({})".format(i+1, item[1], item[0]))) #k, v)))
                #rank.reverse()
                return rank[0:3]
            return [(0, channel, kwargs['from_nick'], '*Kremt*, kjører ingen quiz her.')]

        if command == 'q-data-list':
            if channel not in self.quizzes:
                self.quizzes[channel] = Quiz(args, channel, self.pluginconf)
            tmp = ", ".join(self.quizzes[channel].quizdata_list())
            if tmp == "":
                tmp = "TODO: Can't find data files"
            return [(0, kwargs['from_nick'], "data sources in active language:"),(0, kwargs['from_nick'], tmp)]

        if command == 'q-data-load':
            if kwargs["auth_level"] > 60:
                if channel not in self.quizzes:
                    self.quizzes[channel] = Quiz(args, channel, self.pluginconf)
                return self.quizzes[channel].quizdata_load(args)
            
            
        if command == 'q-start':
            if kwargs["auth_level"] > 60:
                self.del_job = kwargs['del_job']
                self.new_job = kwargs['new_job']
                if channel in self.quizzes and self.quizzes[channel].quiz_started != None:
                    return [(0, channel, kwargs['from_nick'], '*Kremt*, det er startet en quiz i denne kanalen allerede.')]
                elif channel not in self.quizzes:
                    print "HIT"
                    self.quizzes[channel] = Quiz(args, channel, self.pluginconf)

                #print self.quizzes[channel].getQuestionSources()
                if len(self.quizzes[channel].getQuestionSources()) == 0:
                    self.quizzes[channel].loadQuestions()
                self.jobs[channel] = []
                self.quizNewRound(channel)
                return [(0, channel, kwargs['from_nick'], 'Quiz startet i {}.'.format(channel))]

        if command == 'q-stop':
            if kwargs["auth_level"] > 60:
                if channel in self.jobs:
                    for i in self.jobs[channel]:
                        kwargs['del_job'](i)
                    self.jobs[channel] = {}
                if channel in self.quizzes:
                    del self.quizzes[channel]
                    return [(0, channel, kwargs['from_nick'], 'Stoppa.')] # TODO
                return [(0, channel, kwargs['from_nick'], '*Kremt*, kjører ingen quiz her.')]

    def _print_answer(self, channel, answer_tuple):
        if self.VERBOSE: print channel, answer_tuple
        return [(0, channel, answer_tuple[1]), 
                (0, channel, answer_tuple[2])]

    def quizNewRound(self, channel):
        """
        Starts cronjobs for current question. The cronjobs runs self.runQuiz

        @type channel: string
        @param channel: quiz channel

        @rtype: list
        @return: Info that new round is started
        """
        for i in self.jobs[channel]:
            self.del_job(i)
        self.jobs[channel] = []
        q = self.quizzes[channel].getNewQuestion()
        for i in range(q.tip_n() + 2):
            print("quizNewRound")
            if self.VERBOSE: print("tip {}:".format(i))
            self.jobs[channel].append(self.new_job((time.time() + (i+1)*self.quizzes[channel].getTipTime(), self.runQuiz, [channel, i])))
        return [(0, channel, 'New round started.')]

    def runQuiz(self, channel, i):
        """
        Run next step in quiz for channel.

        @type channel: string
        @param channel: quiz channel
        @type i: number
        @param i: question tip count (not currently in use)

        @rtype: list
        @return: Info that new round is started
        """
        if self.VERBOSE: print("self.jobs: {}".format(self.jobs[channel]))
        tmp = self.quizzes[channel].runQuiz() #channel, i)
        if self.VERBOSE: print tmp#("tmp: {}".format( tmp))
        if tmp[0] == 'finished':
            if self.VERBOSE: print("Finished! : {}".format( tmp))
            self.jobs[channel].append(self.new_job((time.time(), self._print_answer, [channel, tmp])))
            if self.VERBOSE: print "START NEW ROUND"
            self.quizNewRound(channel)
        else:
            return tmp

#
## For debugging
        
if __name__ == '__main__':

    print("")

