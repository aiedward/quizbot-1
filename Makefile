# Makefile for INF3331 project
# - Clones DasBot
# - Installs plugin Quiz
# - Imports questions

SHELL = /bin/sh

DASBOT = 'https://github.com/subfusc/DasBot.git'
PROJECTFILES = __init__.py Quiz.py Question.py plugin.cfg

install: $(PROJECTFILES)
	git clone --recursive $(DASBOT)
	mkdir DasBot/src/plugins/Quiz
	cp $(PROJECTFILES) DasBot/src/plugins/Quiz/
	chmod u+x DasBot/src/plugins/Quiz/*.py
	wget http://trondth.at.ifi.uio.no/quizdata.tar.gz
	tar zxf quizdata.tar.gz
	mv quizdata DasBot/src/plugins/Quiz/

quizdata: 
	wget http://trondth.at.ifi.uio.no/quizdata.tar.gz
	tar zxf quizdata.tar.gz
	mv quizdata DasBot/src/plugins/Quiz/
