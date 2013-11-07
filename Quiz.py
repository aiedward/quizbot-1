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
        self.utable = "users"
        self.db_open = False
        self.sql_db = None
        self.connect(pluginconf.get('db','path') + channel + pluginconf.get('db','file'))
        
    def connect(self, database_name=None):
        """
        Connect to a quiz database.

        @type database_name: string
        @param database_name: Path to the database.

        @rtype: None
        """
        if (database_name):
            self.sql_db = sqlite3.connect(database_name) if database_name else None
            self.db_open = True if self.sql_db else False
        
        if self.db_open:
            self._conditionalCreateOverview()
        else:
            raise DatabaseIsNotOpenError('The database is not open')

    def __exe(self, string, values=None):
        if VERBOSE: print((string + " " + str(values) if values else string + " --") + "\n")
        if values:
            return self.sql_db.execute(string, values)
        else:
            return self.sql_db.execute(string)

    def exe(self, string, values=None):
        if VERBOSE: print((string + " " + str(values) if values else string + " --") + "\n")
        if values:
            return self.sql_db.execute(string, values)
        else:
            return self.sql_db.execute(string)
            
    def __com(self):
        self.sql_db.commit()
            
    def _conditionalCreateOverview(self):
        """
        users","questions","session
        """
        self.__exe("CREATE TABLE IF NOT EXISTS " + self.utable
                       + " (uid INTEGER PRIMARY KEY, entity TEXT UNIQUE NOT NULL);")
        self.__exe("CREATE TABLE IF NOT EXISTS " + "questions" #self.utable
                       + " (qid INTEGER PRIMARY KEY, \
                            source TEXT NOT NULL, \
                            question TEXT NOT NULL, \
                            answer TEXT NOT NULL, \
                            category TEXT, \
                            regex TEXT, \
                            author TEXT, \
                            level TEXT, \
                            comment TEXT, \
                            value INTEGER, \
                            tips TEXT \
                       );")
        self.__exe("CREATE TABLE IF NOT EXISTS " + "session" #self.utable
                       + " (sid INTEGER PRIMARY KEY, \
                            active INTEGER, \
                            qid INTEGER, \
                            uid INTEGER, \
                            time INTEGER NOT NULL);")
        self.__exe("CREATE TABLE IF NOT EXISTS " + "allstars" #self.utable
                       + " (uid INTEGER PRIMARY KEY, \
                            sessioncount INTEGER, \
                            questioncount INTEGER \
                            );")
        self.__com()

    def _userExists(self, entity):
        #if self.lowercase: entity.lower()
        r = self.__exe("SELECT * FROM {table} WHERE entity = ? ;".format(table = self.utable),
                       (entity.lower(), )).fetchone() #if self.lowercase else entity
        if not r:
            self.__exe("INSERT INTO {table} (entity) VALUES (?) ;".format(table = self.utable), (entity.lower(), ))
            r = self.__exe("SELECT * FROM {table} WHERE entity = ? ;".format(table = self.utable),
                           (entity.lower(), )).fetchone() #if self.lowercase else entity
            self.__exe("INSERT INTO allstars (uid, sessioncount, questioncount) VALUES (?, 0, 0)", (r[0], ))

        # stderr.write(str(r) + "\n")
        print r
        return r[0] if r else False
        
    def disconnect(self):
        """
        Clean up and Disconnect from the database. Call this before exiting to ensure
        that all changes are commited.

        @rtype: None
        """
        if self.db_open:
            self.sql_db.close()
            self.db_open = False
        
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
        try:
            return [ row for row in self.__exe("SELECT a.questioncount,u.entity from users AS u JOIN allstars AS a ON u.uid=a.uid;") ]
        except Exception:
            return []
        
        #return self.score
    
    def correctAnswer(self, nick):
        """
        TODO. Implement saving stats to db.
        """
        if VERBOSE:
            print "add to DB"
        if self.db_open:
            uid = self._userExists(nick)
            self.__exe("INSERT INTO session (active, qid, uid, time) VALUES (1, ?, ?, ?)",
                       (self.active.getID(), uid, time.time()))
            self.__exe("UPDATE allstars SET questioncount=questioncount + 1 WHERE uid=?", (uid, ))
        
            
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

    
if __name__ == '__main__':
    import ConfigParser
    config = ConfigParser.ConfigParser()
    config.readfp(open("plugin.cfg"))
    q = Quiz("", "foobar", config)
    q.loadQuestions()
    q.getNewQuestion()
    q.runQuiz()
