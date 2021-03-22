# Bot module for https://github.com/vranki/hemppa

from modules.common.module import BotModule
from urllib.request import urlopen
import logging
import os 
import time

NUM_CLIENTS_MARKER = 'workadventure_nb_clients_per_room'
METRICS_URL = "https://pusher.wa.binary-kitchen.de/metrics"
ROOM_PREFIX = "_/global/das-labor.github.io/workadv_das-labor/"
MAIN_ROOM_ID = os.environ["VLAB_MAIN_ROOM_ID"]
ANNOUNCEMENT_INTERVAL = 60 * 30 # seconds

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.last_intrinsic_announcement = None
        
    async def matrix_message(self, bot, room, event):
        num = self.number_of_clients('main')
        await self.announce(bot, room, num)

    def help(self):
        return "Ein Bot für das virtuelle Labor"

    async def matrix_poll(self, bot, pollcount):
        'called every 10 seconds'
        # TODO remove 'True' if WA instance has been upgraded
        # https://twitter.com/pintman/status/1371909456762638336
        if self.last_intrinsic_announcement is not None and \
            (time.time() - self.last_intrinsic_announcement) < ANNOUNCEMENT_INTERVAL:
            return

        room = bot.get_room_by_id(MAIN_ROOM_ID)
        if room is None:
            return

        # try to fetch metric
        num = 0
        tries = 5
        while num==0 and tries > 0:
            num = self.number_of_clients('main')
            tries -= 1

        if num > 0:
            await self.announce(bot, room, num)
            self.last_intrinsic_announcement = time.time()

    async def announce(self, bot, room, num_clients):
        await bot.send_html(
            room,
            f"{num_clients} Entitäten sind im <a href='https://virtuallab.das-labor.org'>virtuellen Labor</a>", 
            f"{num_clients} Entitäten sind im virtuellen Labor")

    def number_of_clients(self, room):
        'Return the numnber of clients in the given room inside a WA instance.'
        with urlopen(METRICS_URL) as f:
            lines = f.readlines()

        for line in lines:
            line_str = line.decode()
            if NUM_CLIENTS_MARKER in line_str and \
                ROOM_PREFIX+room in line_str:

                # line of format
                # workadventure_nb_clients_per_room{room="_/global/das-labor.github.io/workadv_das-labor/main.json"} 20
                number_of_clients_online = int(line_str.split('} ')[1])
                return number_of_clients_online

        # no room found
        self.logger.warn(f'Room {room} not found in metrics')
        return None
