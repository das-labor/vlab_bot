from modules.common.module import BotModule
from urllib.request import urlopen
import datetime
import json
import os
from .db import Database, Config

MAIN_ROOM_ID = os.environ["VLAB_BOT_MAIN_ROOM_ID"]

class FrabDB(Database):
    def init_tables(self):
        with self.dbconn:
            self.dbconn.executescript('''
            CREATE TABLE IF NOT EXISTS frab_announcements (
                date_time DATE NOT NULL DEFAULT (datetime('now','localtime')),
                url TEXT NOT NULL,
                roomid TEXT,
                PRIMARY KEY (url)
            );
            CREATE TABLE IF NOT EXISTS frab_subscriptions (
                url TEXT PRIMARY KEY
            )
            ''')
            self.dbconn.commit()

    def remember_announcement(self, url, roomid):
        query = 'INSERT INTO frab_announcements (url,roomid) VALUES (?,?)'
        self.query(query, (url, roomid))

    def add_subscription(self, url):
        query = 'INSERT INTO frab_subscriptions (url) VALUES (?)'
        self.query(query, (url,))

    def delete_subscription(self, url):
        query = 'DELETE FROM frab_subscriptions WHERE url=?'
        self.query(query, (url,))

    def read_subscriptions(self):
        return [row[0] for row in self.query(
            "SELECT url FROM frab_subscriptions"
        )]

    def already_sent(self, url):
        q = 'SELECT url FROM frab_announcements WHERE url=?'
        rows = self.query(q, (url,))
        return len(rows)>0


class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.poll_interval = 6 * 30  # * 10 seconds
        self.look_minutes_in_future = 60 # minutes
        self.main_room = MAIN_ROOM_ID
        self.db = FrabDB()

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
                for row in self.db.query('SELECT url FROM frab_subscriptions'):
                    msg += f'👁️ {row["url"]}\n'

        elif len(args) == 3:
            bot.must_be_owner(event)
            cmd, param = args[1], args[2]
            if cmd=='add':
                msg = f'adding {param}'
                self.db.add_subscription(param)
            elif cmd=='rm':
                msg = f'removing {param}'
                self.db.delete_subscription(param)
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
                        not self.db.already_sent(re_url):

                        self.logger.debug(f'sending annnouncement about {re_title} to {room.room_id}')
                        await bot.send_text(room, 
                            f'{re_title.upper()} startet in {int(minutes_left)} Minuten \n{re_url}')
                        self.db.remember_announcement(re_url, room.room_id)

        self.logger.debug('finished event check')

    async def matrix_poll(self, bot, pollcount):
        'called every 10 seconds'
        return
        
        if pollcount % self.poll_interval != 0:
            return

        room = bot.get_room_by_id(self.main_room)
        if room is None:
            return

        for url in self.db.read_subscriptions():
            await self.check_events(bot, room, url)

    def help(self):
        return "📅 Ankündigung von Events aus dem Fahrplan (add, rm, ls)"

