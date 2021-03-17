import time
import asyncio
import config
from nio import AsyncClient, MatrixRoom, RoomMessageText
import wa_status
import logging
import sqlite3

LOGFILE = 'vlab_bot.log'
DBFILE = 'vlab_bot.db'
DBCON = sqlite3.connect(DBFILE)


def init_db():
    c = DBCON.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS usersinlab
    (
        id INTEGER PRIMARY KEY,
        `date` DATE DEFAULT CURRENT_TIMESTAMP,
        number_of_clients INTEGER
    )
    ''')
    DBCON.commit()

def remember_users(numusers):
    with DBCON:
        DBCON.execute('INSERT INTO usersinlab (number_of_clients) VALUES (?)',
            (numusers,))

def get_last_num_clients(num):
    'Get last "num" clients seen and remembered.'
    with DBCON:
        rows = DBCON.execute('''
            SELECT number_of_clients FROM usersinlab
            ORDER BY date DESC LIMIT ?
            ''', (num,))
        return [r[0] for r in rows]

# unused so far
async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    logging.debug('msg recvd')
    logging.debug(
        f"Message received in room {room.display_name}\n"
        f"{room.user_name(event.sender)} | {event.body}"
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
        
        clients_history = get_last_num_clients(num=2)
        logging.debug(f'number of clients in vlab history: {clients_history}')

        # check if history unchanged
        if clients_history[0]>0 and clients_history[0] != clients_history[1]:
            logging.debug('Sending msg to channel')
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
