# -*- coding: utf-8 -*-

import codecs
import glob
import re
import sqlite3
import string
import datetime
import time
from random import randint # TODO kan slettes
from random import choice

import Question

COMMENT_RE = re.compile(r'^\s*#')
VERBOSE = True

class Quiz(object):
    """
    To save stat
    """

    def __init__(self, args, channel, pluginconf):
        """
        If channel exists in db, then load statistics and questions for that quiz. TODO
        Else starts new quiz

        @param args: Args from irc command
        @type args: string
        @param channel: Channel name
        @type channel: string
        @param pluginconf: Configparser object
        @type pluginconf: ConfigParser
        """
        self.channel = channel
        self.cfg = {
            'tip_time' : pluginconf.getint('tips','tip_time'),
            'tip_freq' : pluginconf.getint('tips','tip_freq'),
            'max_tips' : pluginconf.getint('tips','max_tips'),
            'quizdata' : pluginconf.get('quizdata','folder'),
            'lang' : pluginconf.get('quizdata','lang')
        }
        #print("CFG {}".format( self.cfg))
        self.args = args
        #self.kwargs = kwargs
        self.questions = []
        self.question_sources = []
        self.active = None
        self.quiz_started = None
        self.question_started = None
        self.count = 0
        self.files = {}
        self.file_re = re.compile(r'(questions.)([^\.]+)')
        self.score = {}

    def __str__(self):
        return "Quiz i: {}".format(self.channel)

    def setLang(self, lang):
        """
        Sets language in Quiz. Unloads questions in wrong lang.
        Not implemented. TODO

        @type lang: string
        @param lang: Language code used in questions-extentions
        """

    def exportQuestions(self, source, filename=False):
        """
        Exports questions as questions.source.lang, or as filename if applied
        Not implemented. TODO

        @type source: string
        @param source: source of questions to be exported
        @type filename: string
        @param filename: optional filename
        """
    
    def createQuestion(self, user, question, answer, regex):
        """
        Exports questions as questions.source.lang, or as filename if applied
        Not implemented. TODO
        """

    def listQuestion(self, question):
        """
        List questions matching question
        Not implemented. TODO

        @return: list with id's
        """

    def getQuestion(self, qid):
        """
        Deletes question with id.
        Not implemented. TODO
        """
        
    def deleteQuestion(self, questionobject):
        """
        Deletes question.
        Not implemented. TODO
        """
    
    def getTipTime(self):
        """
        @return: 
        """
        return self.cfg['tip_time']
    
    def setTipTime(self, seconds):
        """
        Sets time between tips and between answering a question and next question.
        Not implemented. TODO

        @type seconds: number
        @param seconds: time in seconds
        
        @return: time in seconds
        """

    def quiz_status(self):
        """
        In a question, the stages are 'new', 1 ... tip_n ''
        
        @return: status
        """
        if VERBOSE: print "quiz-status - len . {}".format(len(self.q))
        if self.active:
            if VERBOSE: print "quiz-status: {}".format(self.active.status())
            return self.active.status()
        else:
            return 'new'
        
    def runQuiz(self):
        """
        Runs through the question loop

        @return: Question, tip or correct answer.
        """
        if VERBOSE: print "runQuiz status: {}".format(self.active.getStatus())
        if self.active.getStatus() == 'finished':
            if VERBOSE: print "RQ finished"
            return 'finished'
        if self.active.getStatus() == 'new':
            if VERBOSE: print "RQ new"
            self.question_started = time.time()
            self.count += 1
            return self.active.askQuestion(self.channel, self.count)
        elif isinstance(self.active.getStatus(), int):
            if VERBOSE: print "RQ int"
            tip = self.active.giveTip()
            if self.active.getStatus() == 'finished':
                #d = datetime.timedelta(time.time() - self.question_started)
                time_used = time.time() - self.question_started
                return [('finished'), ('Question answered automatically after {} min and {} sec'.format((time_used - (time_used % 60)) / 60, time_used % 60)), ('Correct answer was: {}'.format(tip))]
            else:
                return [(0, self.channel, "Tip nr {}. {}".format(self.active.getStatus(), tip))]
        return [(0, self.channel, "TIP status: {}".format(self.active.getStatus()))]

    def getRank(self):
        """
        @rtype: list
        @return: score
        """
        return self.score
    
    def correctAnswer(self, nick):
        """
        TODO. Implement saving stats to db.
        """
        if VERBOSE: print "add to DB"
        if nick in self.score.keys(): 
            self.score[nick] += 1
        else:
            self.score[nick] = 1
        
    def listen(self, msg, channel, nick):
        """
        Checks if answer is correct

        @type msg: string
        @param msg: message from nick
        @type channel: string
        @param channel: channel of quiz
        @type nick: string
        @param nick: nick of user answering

        @rtype: tuple
        @return: first element boolean, second element formatted message from bot.
        """
        if self.active and self.active.regex.search(msg):
            self.correctAnswer(nick)
            answer = self.active.data['Answer']
            return (True, [(0, channel, nick, 'Du svarte rett! Svaret var: {}'.format(answer))])
        return (False, [(0, channel, nick, 'Feil svar!')])
        
    def getNewQuestion(self):
        """
        Returns random question from db.

        TODO avoid recently given questions
        TODO avoid giving question active in another channel

        @rtype: Question
        @return: Random question object
        """
        self.active = choice(self.questions)
        self.active.reset()
        return self.active

    def getQuestionSources(self):
        """
        Returns sources for questions.

        @rtype: list
        @return: Question sources
        """
        if VERBOSE: print("QUESTIONSOURCES: {}".format(self.question_sources))
        return self.question_sources

    def loadQuestions(self, filename=None):
        """
        Adds questions from the file questions.filename.lang in questiondata folder. If no filename is given, adds questions from random file.

        @type filename: string
        @param filename: Filename (source), without prefix and postfix.
        
        @return: Total number of questions loaded 
        """

        if filename in self.question_sources:
            return

        if len(self.files) == 0:
            self.quizdata_list()
            if len(self.files) == 0:
                return "No files found"

        if filename == None:
            filename = choice(list(self.files.keys()))

        if not filename in self.files.keys():
            print "not {}".format(filename)
            return "File not found"

        if VERBOSE: print("FILENAME {}".format(filename))
        f = codecs.open(self.files[filename], mode='r', encoding='utf-8')
        #f = open(self.files[filename])
        if VERBOSE: print("File opened: {}:{}".format(filename, self.files[filename]))
        tmp = r''
        for line in f:
            #print line
            if COMMENT_RE.search(line) != None:
                if False: print line

            elif line.strip() != "":
                tmp += line.encode('utf-8', 'ignore')
                #print("LINE: {}".format( line.encode('utf-8', 'ignore')))

            #print("TMP {}".format( len(tmp)))
            #print("TMP {}".format( tmp))

            if line.strip() == "" and tmp.strip() != "":
                if VERBOSE: print("TMP: {}".format(tmp))
                self.questions.insert(0, Question.Question(self.cfg))
                self.questions[0].stringToQuestion(tmp, filename)
                tmp = ""

        self.question_sources.append(filename)
        if VERBOSE: print("Sources: {} with length {}.".format(self.question_sources, len(self.questions)))
        return len(self.questions)
            
    def quizdata_list(self):
        """
        Returns list of available sources in quizdata.

        @return: list of available sources in quizdata.
        """
        if VERBOSE: print glob.glob(self.cfg['quizdata'] + '/*.' + self.cfg['lang'])
        if VERBOSE: print self.cfg['quizdata'] + '/*.' + self.cfg['lang']
        for file in glob.glob(self.cfg['quizdata'] + '/*.' + self.cfg['lang']):
            self.files[self.file_re.findall(file)[0][1]] = file
        return self.files.keys()

    def quizdata_load(self, args):
        if VERBOSE: print("quizdata_load: {}".format(args))
        self.loadQuestions(args)
        return "TODO. quizdata_load"
