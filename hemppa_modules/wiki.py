import xml.etree.ElementTree as ET
from modules.common.module import BotModule
from urllib.request import urlopen
import urllib.parse
import json
import os
from datetime import datetime
from .db import Config

NUM_RESULTS = 3
WIKI_BASE_URL = "https://wiki.das-labor.org"
API_SEARCH_PREFIX = WIKI_BASE_URL + \
    f"/api.php?action=query&format=json&list=search&srlimit={NUM_RESULTS}&srsearch="
MAIN_ROOM_ID = os.environ["VLAB_BOT_MAIN_ROOM_ID"]
RECENT_CHANGES_URL = WIKI_BASE_URL + \
    '/api.php?action=feedrecentchanges&hidebots=1&hideminor=1&days=1&limit=10' + \
    '&namespace=0&feedformat=atom'

# TODO use settings property for last_sent instead of db

class MatrixModule(BotModule):
    def __init__(self,name):
        super().__init__(name)
        self.poll_interval = 6 * 60 * 24 # * 10 seconds
        self.config = Config()
        self.config_key = 'wiki_last_sent'
        if self._get_last_sent() is None:
            self._set_last_sent_now()
        self.last_sent = self._get_last_sent()

    def _set_last_sent_now(self):
        'remember last sent entry'
        now = datetime.now()
        self.config.set_value(self.config_key, now.isoformat())
        self.last_sent = now

    def _get_last_sent(self):
        'return datetime of last sent announcement'
        v = self.config.get_value(self.config_key)
        if v is not None:
            return datetime.fromisoformat(v)
        else:
            return v

    def get_settings(self):
        data = super().get_settings()
        data['last_sent'] = self.last_sent.isoformat()
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('last_sent'):
            self.last_sent = datetime.fromisoformat(data['last_sent'])

    async def matrix_message(self, bot, room, event):
        # !wiki some query
        args = event.body.split(' ', maxsplit=1)

        if len(args) == 1:
            await self._check_recent_changes(bot, room)

        elif len(args)==2:
            query = urllib.parse.quote(args[1])

            with urlopen(API_SEARCH_PREFIX + query, timeout=5) as resp:
                js = json.load(resp)

            answer = "🔎 Mal schauen, was ich im Wiki so gefunden habe.\n"
            results = js['query']['search']
            for result in results:
                answer += WIKI_BASE_URL + "/w/" + \
                    urllib.parse.quote(result["title"]) + "\n"

            if len(results) == 0:
                answer = 'Ich habe nichts gefunden. Sorry. ☹️ ' + \
                    'Ich habe mich aber auch nicht doll angestrengt. Schau ' + \
                    'selbst einmal nach.\n' + \
                    f'{WIKI_BASE_URL}?search=' + query

            await bot.send_text(room, answer)

    async def matrix_poll(self, bot, pollcount):
        'called every 10 seconds'
        if pollcount % self.poll_interval != 0:
            return

        self.logger.debug('checking changes in wiki')
        room = bot.get_room_by_id(MAIN_ROOM_ID)
        if room is None:
            return

        now = datetime.now()
        duration = now - self._get_last_sent()
        if duration.days >= 1:
            self.logger.debug('polling recent changes')
            await self._check_recent_changes(bot, room)

        self.logger.debug('finished checking wiki changes')
        
    async def _check_recent_changes(self, bot, room):
        'check for recent changes in wiki if necessary'
        self.logger.debug('Checking for recent changes')
        root = ET.parse(urlopen(RECENT_CHANGES_URL, timeout=5)).getroot()
        ns = '{http://www.w3.org/2005/Atom}'
        msg = ''
        for entry in root.iter(f'{ns}entry'):
            href = entry.find(f'{ns}link').attrib['href']
            title = entry.find(f'{ns}title').text
            msg += f'- {title}: {href}\n'

        if len(msg) > 0:
            self.logger.debug('posting recent changes')
            await bot.send_text(room, 
                '🔎 Im Wiki gab es ein paar Änderungen:\n' + msg)
            self._set_last_sent_now()
            bot.save_settings()

    def help(self):
        return "🔎 Durchsuche das Labor-Wiki. Berichte über Änderungen am Wiki."

    def long_help(self, bot, event, **kwargs):
        return self.help() + \
            f' Ich schaue alle {self.poll_interval * 10 // 60 // 60} Stunden ' + \
                'im Wiki nach ' + \
            f'Änderungen. Zuletzt habe ich darüber am {self.last_sent} informiert.'
