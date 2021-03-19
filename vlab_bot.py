import time
import asyncio
import config
from nio import AsyncClient, MatrixRoom, RoomMessageText
import wa_status
import logging
import sqlite3
import sys

LOGFILE = 'vlab_bot.log'
DBFILE = 'vlab_bot.db'
DBCON = sqlite3.connect(DBFILE)


def init_db():
    c = DBCON.cursor()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS usersinlab
    (
        id INTEGER PRIMARY KEY,
        -- using datetime function to respect timezone
        `date` DATETIME DEFAULT (datetime('now','localtime')),
        number_of_clients INTEGER
    );
    CREATE TABLE IF NOT EXISTS messages 
    (
        id INTEGER PRIMARY KEY,
        `date` DATETIME DEFAULT (datetime('now','localtime')),
        announced_number INTEGER
    );
    DROP VIEW IF EXISTS usersinlab_delta;
    CREATE VIEW IF NOT EXISTS usersinlab_delta AS
    SELECT 
      u2.id, u2.date, u2.number_of_clients, 
      u2.number_of_clients-u1.number_of_clients AS number_of_clients_delta
    FROM usersinlab u1, usersinlab u2
    WHERE u2.id = u1.id + 1;
    ''')
    DBCON.commit()

def remember_users(numusers):
    with DBCON:
        DBCON.execute('INSERT INTO usersinlab (number_of_clients) VALUES (?)',
            (numusers,))

def remember_message(numusers):
    with DBCON:
        DBCON.execute('INSERT INTO messages (announced_number) VALUES (?)',
            (numusers,))

def get_num_clients(timeperiod_minutes): 
    'return number of clients seen in the given time period'
    now_local = 'datetime("now","localtime")'
    query = f'''
        SELECT SUM(number_of_clients)
        FROM usersinlab
        WHERE date BETWEEN 
            datetime({now_local}, '-{timeperiod_minutes} minutes') 
            AND
            {now_local}            
    '''
    with DBCON:
        num = DBCON.execute(query).fetchone()[0]
        return num if num is not None else 0

# unused so far, TODO remove
async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    logging.debug('msg recvd')
    logging.debug(
        f"Message received in room {room.display_name}\n"
        f"{room.user_name(event.sender)} | {event.body}"
    )

def seconds_since_last_msg():
    'retrieve number of seconds since last message sent.'

    # %s will transform datetime value into unixepoch (seconds sincs 1970-01-01)
    # https://sqlite.org/lang_datefunc.html
    query = '''
        SELECT strftime("%s",datetime('now','localtime'))-strftime("%s",date) 
        FROM messages ORDER BY date DESC LIMIT 1
        '''
    with DBCON:
        row = DBCON.execute(query).fetchone()
        return row[0] if row else sys.maxsize

async def announce(client:AsyncClient, clients_in_room):
    logging.debug('Sending msg to channel')
    remember_message(clients_in_room)
    await client.room_send(
        room_id=config.ROOM,
        message_type="m.room.message",
        content = {
            "msgtype": "m.text",
            "format": "org.matrix.custom.html",
            "formatted_body": f'Ich habe <b>{clients_in_room}</b> Entitäten im <a href="https://virtuallab.das-labor.org">virtuellen Labor</a> gesichtet.',
            "body": f"Ich habe {clients_in_room} Entitäten im virtuellen Labor gesichtet. https://virtuallab.das-labor.org"
        }
    )


async def main() -> None:
    logging.info(f'connecting {config.USERNAME}')
    client = AsyncClient(config.SERVER, config.USERNAME)
    #client.add_event_callback(message_callback, RoomMessageText)

    await client.login(config.PASSWORD)

    logging.info(f'joining room {config.ROOM}')    
    await client.join(config.ROOM)

    logging.info(f'starting loop with loop sleeptime {config.SLEEP_TIME}')
    while True:
        clients_in_room = wa_status.number_of_clients(room='main')
        # Sometimes room is missing (None) or an incorrect number of 0 is
        # returned from the metrics. Ignoring these values.
        if clients_in_room is None or clients_in_room==0:
            continue
        remember_users(clients_in_room)
        logging.debug(f'{clients_in_room} clients in room')
        
        # check if message should be send
        if seconds_since_last_msg()>config.MIN_SECONDS_SINCE_LAST_MESSAGE and \
            get_num_clients(config.TIME_PERIOD_MINUTES) > config.MIN_NUM_CLIENTS_SEEN and \
            config.SEND_MESSAGES:

            await announce(client, clients_in_room)

        if not config.RUN_IN_LOOP:
            logging.debug('Stoping loop')
            break

        time.sleep(config.SLEEP_TIME)

    await client.close()
    #await client.sync_forever(timeout=30000) # milliseconds

logging.basicConfig(filename=LOGFILE, 
    format='%(asctime)s [%(levelname)s] %(message)s', 
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG)
# add stream handler for logging to console, too
logging.getLogger().addHandler(logging.StreamHandler())
logging.info("Starting bot")

init_db()

asyncio.get_event_loop().run_until_complete(main())
