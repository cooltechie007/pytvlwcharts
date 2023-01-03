import os
import sys
import json
import logging
import asyncio
import websockets
from time import sleep
from datetime import datetime
from KiteExtra import KiteExt
from multiprocessing import shared_memory

# logging.basicConfig(level=logging.DEBUG)


sharedList = shared_memory.ShareableList(name=sys.argv[1])
userid, enctoken, instrument, instToken = (
    sharedList[0],
    sharedList[1],
    sharedList[2],
    sharedList[3],
)  # noqa: E501
kite = KiteExt(userid=userid)
kite.login_using_enctoken(
    userid=userid, enctoken=enctoken, public_token=None
)  # noqa: E501
kws = kite.kws()
watchlist = [256265 if instToken == 0 else instToken]
tickdata = ""


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return {"TimeStr": o.strftime("%Y-%m-%dT%H:%M:%S.%f%z")}
        return json.JSONEncoder.default(self, o)


class DateTimeDecoder(json.JSONDecoder):
    def default(self, o):
        TimeStr = o.get("TimeStr")
        if TimeStr is not None:
            try:
                return datetime.strptime(TimeStr, "%Y-%m-%dT%H:%M:%S.%f%z")
            except ValueError:
                return datetime.strptime(TimeStr, "%Y-%m-%dT%H:%M:%S.%f")
        return json.JSONDecoder.default(self, o)


def on_ticks(ws, ticks):
    global tickdata
    tickdata = json.dumps(ticks, sort_keys=False, cls=DateTimeEncoder)


def on_connect(ws, response):
    global watchlist
    ws.subscribe(watchlist)
    ws.set_mode(ws.MODE_FULL, watchlist)


# Callback when current connection is closed.
def on_close(ws, code, reason):
    logging.info(
        "Connection closed: {code} - {reason}".format(code=code, reason=reason)
    )
    ws.stop()


# Callback when connection closed with error.
def on_error(ws, code, reason):
    logging.info(
        "Connection error: {code} - {reason}".format(code=code, reason=reason)
    )  # noqa: E501


# Callback when reconnect is on progress
def on_reconnect(ws, attempts_count):
    logging.info("Reconnecting: {}".format(attempts_count))


# Callback when all reconnect failed (exhausted max retries)
def on_noreconnect(ws):
    logging.info("Reconnect failed.")


# Callback when order update is there
def on_order_update(ws, data):
    logging.info("Order Update: {}".format(data))


# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_close = on_close
kws.on_error = on_error
kws.on_connect = on_connect
kws.on_reconnect = on_reconnect
kws.on_noreconnect = on_noreconnect
kws.on_order_update = on_order_update
# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.


async def handler(websocket, path):
    global watchlist, tickdata, prevtickdata
    while True:
        if tickdata != "":
            await websocket.send(tickdata)
        if watchlist != [256265] and watchlist != [sharedList[3]]:
            kws.UnsubSubSetMode(watchlist, [sharedList[3]], kws.MODE_FULL)
            watchlist = [sharedList[3]]
        await asyncio.sleep(0.25)


if __name__ == "__main__":
    kws.connect(threaded=True)
    sleep(5)
    start_server = websockets.serve(handler, "127.0.0.1", 5001)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

    sharedList.shm.close()
    sharedList.shm.unlink()
