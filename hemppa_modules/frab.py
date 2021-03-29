from modules.common.module import BotModule
from urllib.request import urlopen
import datetime
import json
import os
import sqlite3

FRAB_URL = os.environ["FRAB_URL"]
MAIN_ROOM_ID = os.environ["VLAB_MAIN_ROOM_ID"]


class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.poll_interval = 6 * 30  # * 10 seconds
        self.look_minutes_in_future = 60 # minutes
        self.main_room = MAIN_ROOM_ID
        self.dbconn = sqlite3.connect('frab.db')
        self.initdb()

    def initdb(self):
        with self.dbconn:
            self.dbconn.execute('''
            CREATE TABLE IF NOT EXISTS announcements (
                date_time DATE NOT NULL DEFAULT (datetime('now','localtime')),
                url TEXT NOT NULL,
                roomid TEXT,
                PRIMARY KEY (url)
            )
            ''')
            self.dbconn.commit()

    def remember_announcement(self, url, roomid):
        query = 'INSERT INTO announcements (url,roomid) VALUES (?,?)'
        with self.dbconn:            
            self.dbconn.execute(query, (url,roomid))
            self.dbconn.commit()

    def already_sent(self, url):
        query = 'SELECT url FROM announcements WHERE url=?'
        with self.dbconn:
            c = self.dbconn.cursor()
            c.execute(query, (url,))
            if c.fetchone():
                return True
            else:
                return False
            c.close()

    def _read_frab(self):
        with urlopen(FRAB_URL, timeout=5) as resp:
            js = json.load(resp)

        return js

    async def matrix_message(self, bot, room, event):
        msg = "Ich schaue regelmäßig in den Fahrplan und erinnere " + \
            f"{self.look_minutes_in_future} Minuten vor Beginn " + \
            "einer Veranstaltung."

        await bot.send_text(room, msg)

    async def check_events(self, bot, room):
        frab = self._read_frab()
        for day in frab['schedule']['conference']['days']:
            for conf_room in day['rooms']:
                for room_ev in day['rooms'][conf_room]:
                    if 'date' not in room_ev or \
                        'title' not in room_ev or \
                        'url' not in room_ev:
                        continue

                    re_title, re_url = room_ev['title'], room_ev['url']
                    re_date = room_ev['date']

                    evt_time = datetime.datetime.fromisoformat(re_date)
                    # remove time zone in order to allow time substraction
                    evt_time = evt_time.replace(tzinfo=None)
                    time_left = evt_time - datetime.datetime.now()
                    minutes_left = time_left.seconds / 60

                    if minutes_left < self.look_minutes_in_future and \
                        not self.already_sent(url):

                        self.logger.debug(f'sending annnouncement about {re_title} to {room.room_id}')
                        await bot.send_text(room, 
                            f'{re_title.upper()} startet in {int(minutes_left)} Minuten \n{re_url}')
                        self.remember_announcement(re_url, room.room_id)
                        return

        self.logger.debug('finished event check')

    async def matrix_poll(self, bot, pollcount):
        'called every 10 seconds'

        if pollcount % self.poll_interval != 0:
            return

        room = bot.get_room_by_id(self.main_room)
        if room is None:
            return

        await self.check_events(bot, room)

    def help(self):
        return "Ankündigung von Events aus dem Fahrplan"

