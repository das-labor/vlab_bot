from modules.common.pollingservice import PollingService
from urllib.request import urlopen

NUM_CLIENTS_MARKER = 'workadventure_nb_clients_per_room'

class MatrixModule(PollingService):
    def __init__(self, name):
        super().__init__(name)
        self.accountroomid_lastnumonline = {}

    async def poll_implementation(self, bot, account, roomid, send_messages):
        self.logger.debug(f'polling workadventure {account}.')
        room, url = account.split('@')
        self.logger.debug(f'looking for room {room} at {url}')

        with urlopen(url, timeout=5) as response:
            lines = response.readlines()

        for line in lines:
            line_str = line.decode()
            if NUM_CLIENTS_MARKER in line_str and room in line_str:
                # line of format
                # workadventure_nb_clients_per_room{room="_/global/das-labor.github.io/workadv_das-labor/main.json"} 20
                num_clients_online = int(line_str.split('} ')[1])
                self.logger.debug(f'found {num_clients_online} clients online')

                last_num_online = self.accountroomid_lastnumonline.get(account+roomid, 0)
                self.logger.debug(f'last num online {last_num_online}')

                if send_messages and num_clients_online != last_num_online:
                    await bot.send_text(bot.get_room_by_id(roomid), 
                        f'{num_clients_online} entities online')

                    self.accountroomid_lastnumonline[account+roomid] = num_clients_online
                    bot.save_settings()
                    break

    def get_settings(self):
        data = super().get_settings()
        data['last_num_online'] = self.accountroomid_lastnumonline
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('last_num_online'):
            self.accountroomid_lastsent = data['last_num_online']

    def help(self):
        return "Notify about entities in a work adventure instances."

    def long_help(self, bot, event, **kwargs):
        return self.help() + \
            ' This is a polling service. Therefore there are additional ' + \
            'commands: list, debug, poll, clear, add URL, del URL\n' + \
            '!wordadv add URL: to add a new endpoint. URL has the form\n' + \
            'ROOM@METRICS_URL e.g.\n' + \
            '_/global/das-labor.github.io/workadv_das-labor/main.json@https://pusher.wa.binary-kitchen.de/metrics\n' + \
            f'I will check for changes roughly every {self.poll_interval_min} minutes.'
