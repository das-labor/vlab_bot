from .db import Database
import datetime
import os
from modules.common.module import BotModule

MAIN_ROOM_ID = os.environ["VLAB_BOT_MAIN_ROOM_ID"]

class RememberDB(Database):
    def init_tables(self):
        with self.dbconn:
            self.dbconn.execute('''
            CREATE TABLE IF NOT EXISTS remember_things (
                date DATE,
                thing TEXT 
            )
            ''')
            self.dbconn.commit()

    def add_remembering(self, date:datetime.datetime, thing:str):
        query = 'INSERT INTO remember_things (date, thing) VALUES (?,?)'
        self.query(query, (date.isoformat(),thing))

    def get_things_until(self, date:datetime.datetime):
        'Return list of remembered things until given date'
        return [row[0] for row in self.query(
            """
            SELECT thing 
            FROM remember_things
            WHERE date <= ?
            """,
            (date.isoformat(),)
        )]

    def get_all_things(self):
        'return all things (date, thing) I have remembered'
        return [
            (datetime.datetime.fromisoformat(row['date']), row['thing']) 
            for row in self.query(
                'SELECT date,thing FROM remember_things ORDER BY date')
        ]

    def remove_things_until(self, date_until:datetime.datetime):
        'remove things in until given date'
        self.query('''
            DELETE FROM remember_things
            WHERE date <= ?
            ''', (date_until.isoformat(),))

class MatrixModule(BotModule):
    def __init__(self,name):
        super().__init__(name)
        self.poll_interval = 6 # * 10 seconds
        self.db = RememberDB()

    async def matrix_message(self, bot, room, event):
        args = event.body.split(' ')

        msg = ''
        if len(args)==1:
            msg = 'z.B. so: !remember 2042-01-01T00:01 Sylvester'
        elif len(args)==2 and args[1]=='ls':
            bot.must_be_owner(event)
            for date,thing in self.db.get_all_things():
                msg += f'- {date}: {thing}\n'

        elif len(args)>=3:
            try:
                date = datetime.datetime.fromisoformat(args[1])
                thing = ' '.join(args[2:])
                if date > datetime.datetime.now():
                    self.db.add_remembering(date, thing)
                    msg += f"Termin gemerkt: {date}"
                else:
                    msg += 'Das Datum muss in der Zukunft liegen.'
            except Exception as e:
                msg += str(e)

        if msg:
            await bot.send_text(room, msg)

    async def matrix_poll(self, bot, pollcount):
        'called every 10 seconds'
        if pollcount % self.poll_interval != 0:
            return

        room = bot.get_room_by_id(MAIN_ROOM_ID)
        if room is None:
            return

        duntil = datetime.datetime.now() + \
            datetime.timedelta(seconds=self.poll_interval*10)
        msg = ''
        for thing in self.db.get_things_until(duntil):
            msg += f"⏰ Erinnerung: {thing}\n"

        if msg:
            self.logger.debug(f'notify: {msg}')
            await bot.send_text(room, msg)
            self.db.remove_things_until(duntil)

    def help(self):
        return "📅 Ich erinnere an Dinge."
