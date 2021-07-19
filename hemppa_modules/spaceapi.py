from modules.common.pollingservice import PollingService
from urllib.request import urlopen
import json
import time

class MatrixModule(PollingService):
    def __init__(self, name):
        super().__init__(name)
        self.poll_interval_min = 10
        self.poll_interval_random = 1
        self.accountroomid_lastsent = {}

    async def poll_implementation(self, bot, account, roomid, send_messages):
        self.logger.debug(f'polling space api {account}.')
        with urlopen(account, timeout=5) as response:
            js = json.load(response)

        space = js['space']
        open = 'open 🔓' if js['state']['open'] else 'closed 🔒'
        last_change = js['state']['lastchange']
        last_sent = self.accountroomid_lastsent.get(account+roomid, -1)
        self.logger.debug(f'seconds since last update {time.time()-last_change}')
        text = f'{space} is now {open}'

        if send_messages and last_sent < last_change:
            await bot.send_text(bot.get_room_by_id(roomid), text)
            self.accountroomid_lastsent[account+roomid] = time.time()
            bot.save_settings()

    def get_settings(self):
        data = super().get_settings()
        data['lastsent'] = self.accountroomid_lastsent
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('lastsent'):
            self.accountroomid_lastsent = data['lastsent']

    def help(self):
        return "Notify about Space-API (https://spaceapi.io/) status changes."

    def long_help(self, bot, event, **kwargs):
        return self.help() + \
            ' This is a polling service. Therefore there are additional ' + \
            'commands: list, debug, poll, clear, add URL, del URL\n' + \
            '!spaceapi add URL: to add a space-api endpoint\n' + \
            '!spaceapi list: to list the endpoint configured for this room.\n' + \
            f'I will look for changes roughly every {self.poll_interval_min} minutes.'
