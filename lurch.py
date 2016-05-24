#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages
# This program is dedicated to the public domain under the CC0 license.

"""
This Bot uses the Updater class to handle the bot.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import telegram
from telegram.ext import Updater
from telegram import InlineQueryResultArticle, ParseMode

import logging
from enum import Enum     # for enum34, or the stdlib version

HEADERS= {'Accept': 'application/json'}
URL="http://158.109.8.75:8080/capture_telegram/v1.0/logs"
data={
        'data': {
                'logs': [{'username':'testtelegramclient', 'textlog':'texxxt 1'}]
        }
}

import json
class ClientRest(object):
    def __init__(self):
        self.buffer_msgs=[]
        self.SIZE_BUFFER=1

    def add_message(self,username,msg):
        self.buffer_msgs.append([username,msg])
        if self.SIZE_BUFFER == len(self.buffer_msgs):
            response=self.push()
            self.buffer_msgs = []

    def new_entry_log(self,username,msg):
        return {'username':str(username),'textlog':str(msg)}

    def push(self):
        import requests
        data = {'data': {'logs': [self.new_entry_log(entry[0],entry[1]) for entry in self.buffer_msgs]}}
        return requests.post(URL,data=json.dumps(data),headers=HEADERS)

class States(Enum):
    # Define the different states a chat can be in
    MENU, AWAIT_CONFIRMATION, AWAIT_INPUT, BUSY = range(4)

class Bot(object):
    def __init__(self, token=''):
        self.token = "165496302:AAFY-AxHFD60qMPBly7_dZdhQmzouBnQOZU"

        # Create the EventHandler and pass it your bot's token.
        self.updater = Updater(self.token)

        # Get the dispatcher to register handlers
        self.dp = self.updater.dispatcher

        # on different commands - answer in Telegram
        self.dp.addTelegramCommandHandler("start", self.start)
        self.dp.addTelegramCommandHandler("help", self.help)
        self.dp.addTelegramCommandHandler("wikipedia", self.wikipedia)
        self.dp.addTelegramCommandHandler("stop", self.stop)
        self.dp.addTelegramCommandHandler("state", self.state)

        # on noncommand i.e message - echo the message on Telegram
        self.dp.addTelegramMessageHandler(self.echo)

        # log all errors
        self.dp.addErrorHandler(self.error)


        # Enable logging
        logging.basicConfig(
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                level=logging.INFO)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        self.logger = logging.getLogger(__name__)

        # States are saved in a dict that maps chat_id -> state
        self._state = dict()
        # Sometimes you need to save data temporarily
        self._context = dict()
        # This dict is used to store the settings value for the chat.
        # Usually, you'd use persistence for this (e.g. sqlite).
        self._values = dict()

        self.clientRest = ClientRest()

    # Define a few command handlers. These usually take the two arguments bot and
    # update. Error handlers also receive the raised TelegramError object in error.
    def start(self, bot, update):
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        self._state[chat_id] = States.MENU
        self._context[chat_id] = user_id # save the user id to context

        bot.sendMessage(chat_id=chat_id, text="You rang, Sir? I'm Lurch and I will serve you.")

    # Handler for the /stop command.
    # Sets the state back to MENU and clears the context
    def stop(self, bot, update):
        chat_id = update.message.chat_id
        self._state[chat_id] = States.MENU
        self._context[chat_id] = None
        bot.sendMessage(chat_id=chat_id, text='Okay, Sir. I will wait in my room.')

    # Handler for the /start command.
    # Sets the state back to MENU and clears the context
    def state(self, bot, update):
        chat_id = update.message.chat_id
        state = self._state[chat_id]

        if state is States.MENU:
            text_message = 'I am available, Sir. What is your desire?'
        elif state is States.AWAIT_INPUT:
            text_message = 'I am waiting for you answer, Sir.'

        bot.sendMessage(chat_id=chat_id, text=('You rang? %s' % text_message))

    def help(self, bot, update):
        bot.sendMessage(update.message.chat_id, text='You rang?')


    def echo(self, bot, update):
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        chat_state = self._state[chat_id]
        chat_context = self._context[chat_id]

        if chat_state == States.AWAIT_INPUT and chat_context == user_id:
            self._state[chat_id] = States.MENU
            self._context[chat_id] = None

            # search on wikipedia
            query = update.message.text
            text_message = self.search_wikipedia(user_id, query)
            bot.sendMessage(chat_id=chat_id, text=text_message)
            return

        text_message = 'May I help you, Sir?'
        audio_file = open('groan.mp3', 'rb')

        bot.sendMessage(
            chat_id=update.message.chat_id,
            text=text_message)

        bot.sendAudio(update.message.chat_id, audio_file)


    def wikipedia(self, bot, update, args):
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        text = update.message.text
        chat_state = self._state[chat_id]
        context = self._context[chat_id]

        if args:
            # search on wikipedia
            text_message = self.search_wikipedia(user_id, query)
            bot.sendMessage(chat_id=chat_id, text=text_message)
            return

        # Since the handler will also be called on messages, we need to check if
        # the message is actually a command
        if chat_state == States.MENU and text[0] == '/':
            self._state[chat_id] = States.AWAIT_INPUT  # set the state
            self._context[chat_id] = user_id   # save the user id to context
            bot.sendMessage(chat_id,
                            text="What do you want to search on Wikipedia, Sir?")
        elif chat_state == States.AWAIT_INPUT:
            bot.sendMessage(chat_id,
                            text="You already asked for this, Sir.")


    # calls wikipedia API and launch the query
    def search_wikipedia(self, user_id, query):
        import wikipedia as wp
        # log query into API rest
        self.clientRest.add_message(user_id, query)

        try:
            message = wp.summary(query, sentences=1)
        except wp.exceptions.DisambiguationError as e:
            print e.options
            message = wp.summary(e.options[0], sentences=1)

        return message


    def error(self, bot, update, error):
        self.logger.warn('Update "%s" caused error "%s"' % (update, error))

    def run(self):
        # Start the Bot
        self.updater.start_polling()

        # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()

if __name__ == '__main__':

    lurch = Bot()
    lurch.run()
