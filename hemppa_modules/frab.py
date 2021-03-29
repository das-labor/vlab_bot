from modules.common.module import BotModule
from urllib.request import urlopen
import datetime
import json
import os
import sqlite3

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
            self.dbconn.executescript('''
            CREATE TABLE IF NOT EXISTS announcements (
                date_time DATE NOT NULL DEFAULT (datetime('now','localtime')),
                url TEXT NOT NULL,
                roomid TEXT,
                PRIMARY KEY (url)
            );
            CREATE TABLE IF NOT EXISTS subscriptions (
                url TEXT PRIMARY KEY
            )
            ''')
            self.dbconn.commit()

    def remember_announcement(self, url, roomid):
        query = 'INSERT INTO announcements (url,roomid) VALUES (?,?)'
        self._query(query, (url, roomid))

    def add_subscription(self, url):
        query = 'INSERT INTO subscriptions (url) VALUES (?)'
        self._query(query, (url,))

    def delete_subscription(self, url):
        query = 'DELETE FROM subscriptions WHERE url=?'
        self._query(query, (url,))

    def read_subscriptions(self):
        return [row[0] for row in self._query(
            "SELECT url FROM subscriptions"
        )]

    def _query(self, query, params=[]):
        with self.dbconn:
            result = self.dbconn.execute(query, params)
            self.dbconn.commit()
            return list(result)

    def already_sent(self, url):
        query = 'SELECT url FROM announcements WHERE url=?'
        rows = self._query(query, (url,))
        return len(rows)>0

    def _read_frab(self, url):
        with urlopen(url, timeout=5) as resp:
            js = json.load(resp)

        return js

    async def matrix_message(self, bot, room, event):
        self.logger.debug(f'processing {event.body}')
        args = event.body.split()

        if len(args) == 1:
            msg = "Ich schaue regelmäßig in den Fahrplan und erinnere " + \
                f"{self.look_minutes_in_future} Minuten vor Beginn " + \
                "einer Veranstaltung."

        elif len(args)== 2:
            cmd = args[1]
            if cmd=='ls':
                msg = f'Subscriptions, bei denen ich regelmäßig vorbeischaue:\n'
                for row in self._query('SELECT url FROM subscriptions'):
                    msg += f'👁️ {row[0]}\n'

        elif len(args) == 3:
            bot.must_be_owner(event)
            cmd, param = args[1], args[2]
            if cmd=='add':
                msg = f'adding {param}'
                self.add_subscription(param)
            elif cmd=='rm':
                msg = f'removing {param}'
                self.delete_subscription(param)
        else:
            return

        await bot.send_text(room, msg)

    async def check_events(self, bot, room, frab_url):
        self.logger.debug(f'checking url {frab_url}')
        frab = self._read_frab(frab_url)
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
                    minutes_left = time_left.total_seconds() / 60

                    if minutes_left < self.look_minutes_in_future and \
                        not self.already_sent(re_url):

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

        for url in self.read_subscriptions():
            await self.check_events(bot, room, url)

    def help(self):
        return "Ankündigung von Events aus dem Fahrplan"

