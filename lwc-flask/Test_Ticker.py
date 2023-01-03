import logging
from kiteext_2022 import KiteExt
import datetime
from time import sleep

from twisted.internet import reactor

logging.basicConfig(level=logging.DEBUG)

userid = "VT5229"
enctoken = "yzgAKGF63w0KJ2MZFk5UQnlg4r5haRVsTL0WFrM21gvdWiS2j33lQ0X6S+m2mVRO09HrIY6vcJLtIY330rJj/yUvdHUD2CGD+TuKvyuGD0kE2IcUvafIaA=="  # noqa: E501
# Initialise
kite = KiteExt(userid=userid)
kite.login_using_enctoken(userid=userid, enctoken=enctoken, public_token=None)
kws = kite.kws()

nifty = 256265
banknifty = 260105
watchlist = [256265, 260105, 738561, 5633]


def on_ticks(ws, ticks):
    global nifty, banknifty
    for tick in ticks:
        try:
            logging.info(f"Instrument Tick: {tick}")

        except Exception as e:
            logging.info("Tick Data Obtaining Errors: {}".format(e.message))


def on_connect(ws, response):
    global watchlist
    ws.subscribe(watchlist[:1])
    ws.set_mode(ws.MODE_LTP, watchlist[:1])


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
kws.connect(threaded=True)
# kws.connect(threaded=True)
sleep(10)
while True:
    for i, item in enumerate(watchlist):
        if i < len(watchlist) - 1:
            kws.UnsubSubSetMode(
                [watchlist[i]], [watchlist[i + 1]], kws.MODE_FULL
            )  # noqa: E501
        if i == len(watchlist) - 1:
            kws.UnsubSubSetMode(
                [watchlist[i]], [watchlist[0]], kws.MODE_FULL
            )  # noqa: E501
        sleep(15)
