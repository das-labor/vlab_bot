# Bot module for https://github.com/vranki/hemppa

from modules.common.module import BotModule
from urllib.request import urlopen
import urllib.parse
import json

# https://www.mediawiki.org/wiki/API:Search
NUM_RESULTS = 3
WIKI_BASE_URL = "https://wiki.das-labor.org"
API_SEARCH_PREFIX = WIKI_BASE_URL + f"/api.php?action=query&format=json&list=search&srlimit={NUM_RESULTS}&srsearch="

class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        # !wiki some query
        args = event.body.split()

        if len(args) > 1:
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

            if len(results) > 0:
                await bot.send_text(room, answer)
        
    def help(self):
        return "Verlinke auf das Labor-Wiki."
