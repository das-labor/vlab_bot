import xml.etree.ElementTree as ET
from modules.common.module import BotModule
from urllib.request import urlopen
import urllib.parse
import json
import os
import datetime

NUM_RESULTS = 3
WIKI_BASE_URL = "https://wiki.das-labor.org"
API_SEARCH_PREFIX = WIKI_BASE_URL + f"/api.php?action=query&format=json&list=search&srlimit={NUM_RESULTS}&srsearch="
MAIN_ROOM_ID = os.environ["VLAB_BOT_MAIN_ROOM_ID"]
RECENT_CHANGES_URL = WIKI_BASE_URL + '/api.php?action=feedrecentchanges&hidebots=1&hideminor=1&days=1&limit=10&namespace=0&feedformat=atom'

class MatrixModule(BotModule):
    def __init__(self,name):
        super().__init__(name)
        self.poll_interval = 6*60*24 # * 10 seconds

    async def matrix_message(self, bot, room, event):
        # !wiki some query
        args = event.body.split()

        if len(args) == 1:
            await self._check_recent_changes(bot, room)

        elif len(args) > 1:
            query = urllib.parse.quote(
                ' '.join(args[1:])
                )

            with urlopen(API_SEARCH_PREFIX + query, timeout=5) as resp:
                js = json.load(resp)

            answer = "Mal schauen, was ich im Wiki so gefunden habe.\n"
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

        room = bot.get_room_by_id(MAIN_ROOM_ID)
        if room is None:
            return

        self.logger.debug('polling recent changes')
        await self._check_recent_changes(bot, room)

    async def _check_recent_changes(self, bot, room):
        msg = '🔎 Im Wiki gab es ein paar Änderungen\n'
        root = ET.parse(urlopen(RECENT_CHANGES_URL, timeout=5)).getroot()

        ns = '{http://www.w3.org/2005/Atom}'
        num_entries = 0
        for entry in root.iter(f'{ns}entry'):
            href = entry.find(f'{ns}link').attrib['href']
            title = entry.find(f'{ns}title').text
            msg += f'- {title}: {href}\n'
            num_entries += 1

        if num_entries > 0:
            self.logger.debug('posting recent changes')
            await bot.send_text(room, msg)

    def help(self):
        update_hours = int((self.poll_interval * 10) / 60 / 60)
        return "🔎 Durchsuche das Labor-Wiki. Berichte alle " + \
            f"{update_hours} Stunden über Änderungen am Wiki."
