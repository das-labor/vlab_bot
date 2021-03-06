import abc
import sqlite3
from modules.common.module import BotModule

MAIN_DB_FILE = 'vlab_bot.db'

class MatrixModule(BotModule):
    def __init__(self,name):
        super().__init__(name)
        self.db = Config()

    async def matrix_message(self, bot, room, event):
        msg = "Ich sehe folgende Tabellen:\n"
        query = 'select name from sqlite_master where type="table"'
        tables = ['- ' + row['name'] for row in self.db.query(query)]
        msg += '\n'.join(tables)

        await bot.send_text(room, msg)

    def help(self):
        return '✍ Ich kann mir gut Dinge in Tabellen merken.'

class Database(abc.ABC):
    def __init__(self):
        self.dbconn = sqlite3.connect(MAIN_DB_FILE)
        self.dbconn.row_factory = sqlite3.Row
        self.dbconn.execute('PRAGMA foreign_keys=on')
        self.init_tables()

    def query(self, query, params=None):
        # https://docs.python-guide.org/writing/gotchas/
        if params is None: params=[]

        with self.dbconn:
            result = self.dbconn.execute(query, params)
            self.dbconn.commit()
            return list(result)

    @abc.abstractmethod
    def init_tables(self):
        pass

class Config(Database):
    def init_tables(self):
        with self.dbconn:
            self.dbconn.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT NOT NULL PRIMARY KEY,
                value TEXT NOT NULL
            )
            ''')
            self.dbconn.commit()

    def get_value(self, key, default=None):
        'read config, return default value if no value present.'

        query = "SELECT value FROM config WHERE key=?"
        rows = self.query(query, (key,))

        if len(rows)==0:
            return default
        else:
            return rows[0]['value']

    def set_value(self, key, value):
        if self.get_value(key) is None:
            query = "INSERT INTO config (value,key) VALUES (?,?)"
        else:
            query = "UPDATE config SET value=? WHERE key=?"

        self.query(query, (value,key))
