import time
import asyncio
import config
from nio import AsyncClient, MatrixRoom, RoomMessageText
import wa_status
import logging

LOGFILE = 'vlab_bot.log'

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

    # last two entries measured
    clients_history = [0,0]

    logging.info(f'starting loop with loop sleeptime {config.SLEEP_TIME}')
    while True:
        logging.debug(f'number of clients in vlab: history: {clients_history}')
        clients_history.pop(0)
        clients_history.append(wa_status.number_of_clients('main'))
        # do nothing if history unchanged
        if clients_history[0]>0 and clients_history[0] == clients_history[1]:
            logging.debug('Sending msg to channel')
            await client.room_send(
                # Watch out! If you join an old room you'll see lots of old messages
                room_id=config.ROOM,
                message_type="m.room.message",
                content = {
                    "msgtype": "m.text",
                    "body": f"{clients_history[0]} Entitäten sind derzeit im virtuellen Labor. https://virtuallab.das-labor.org"
                }
            )

        if not config.RUN_IN_LOOP:
            logging.debug('Stopping loop')
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

asyncio.get_event_loop().run_until_complete(main())
