# Bot module for https://github.com/vranki/hemppa

from modules.common.module import BotModule
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import logging
import os 
import time

NUM_CLIENTS_MARKER = 'workadventure_nb_clients_per_room'
METRICS_URL = "https://pusher.wa.binary-kitchen.de/metrics"
ROOM_PREFIX = "_/global/das-labor.github.io/workadv_das-labor/"
MAIN_ROOM_ID = os.environ["VLAB_MAIN_ROOM_ID"]
ANNOUNCEMENT_INTERVAL = int(os.environ["VLAB_ANNOUNCEMENT_INTERVAL"]) # seconds

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.last_intrinsic_announcement = None
        self.logger.info('vlab Bot inited')
        
    async def matrix_message(self, bot, room, event):
        num = self.number_of_clients('main')
        if num is None:
            await bot.send_text(room, 'Ich konnte die Anzahl der Entitäten leider nicht ermitteln. :(')
            return

        await self.announce(bot, room, num)

        # TODO num will be negative until WA instance has been upgraded
        # https://twitter.com/pintman/status/1371909456762638336
        if num < 0:
            await bot.send_text(room, 
                "Wenn die Zahl negativ ist, liegt dies an einem bekannten Problem auf der Instanz. Hier hilft nur abwarten. Techniker ist informiert :)")

    def help(self):
        return "Wieviele Entitäten sind im virtuellen Labor?"

    async def matrix_poll(self, bot, pollcount):
        'called every 10 seconds'
        if self.last_intrinsic_announcement is not None and \
            (time.time() - self.last_intrinsic_announcement) < ANNOUNCEMENT_INTERVAL:
            return

        room = bot.get_room_by_id(MAIN_ROOM_ID)
        if room is None:
            return

        num = self.number_of_clients('main')
        if num is not None and num > 0:
            await self.announce(bot, room, num)
            self.last_intrinsic_announcement = time.time()

    async def announce(self, bot, room, num_clients):
        await bot.send_html(
            room,
            f"{num_clients} Entitäten sind im " +
                "<a href='https://virtuallab.das-labor.org'>virtuellen " +
                "Labor</a>", 
            f"{num_clients} Entitäten sind im virtuellen Labor")            

    def number_of_clients(self, room, retries=5):
        'Return the numnber of clients in the given room inside a WA instance. Will return None on error.'

        for _ in range(retries):  
            # retrieve metrics and handle errors
            # https://docs.python.org/3/howto/urllib2.html
            try:
                response = urlopen(METRICS_URL)
                lines = response.readlines()
            except HTTPError as e:
                self.logger.error(f'The server couldnt fulfill the request. {e.code}')
            except URLError as e:
                self.logger.error(f'We failed to reach a server. {e.reason}')
            else:
                # no errors
                for line in lines:
                    line_str = line.decode()
                    if NUM_CLIENTS_MARKER in line_str and \
                        ROOM_PREFIX+room in line_str:

                        # line of format
                        # workadventure_nb_clients_per_room{room="_/global/das-labor.github.io/workadv_das-labor/main.json"} 20
                        number_of_clients_online = int(line_str.split('} ')[1])
                        return number_of_clients_online

        # no room found
        self.logger.warn(f'Room {room} not found in metrics after {retries} retries.')
        return None
