import sys
import json
from time import sleep
from datetime import datetime
from twisted.python import log
from KiteExtra import KiteExt
from multiprocessing import shared_memory
from autobahn.twisted.websocket import listenWS
from twisted.internet.protocol import ReconnectingClientFactory
from autobahn.twisted.websocket import (
    WebSocketServerFactory,
    WebSocketServerProtocol,
    WebSocketClientProtocol,
)


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


class BroadcastClientProtocol(WebSocketClientProtocol):
    def onMessage(self, payload, isBinary):
        if not isBinary:
            print(
                "Tick Received: {}".format(
                    json.loads(payload.decode("utf8"), cls=DateTimeDecoder)
                )
            )


class BroadcastServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        self.factory.register(self)

    def onConnect(self, request):
        print("Client connecting: {}".format(request.peer))

    def onMessage(self, payload, isBinary):
        if not isBinary:
            # msg = "{} from {}".format(payload.decode("utf8"), self.peer)
            # self.factory.broadcast(msg)
            self.factory.broadcast(payload.decode("utf8"))

    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)


class BroadcastServerFactory(WebSocketServerFactory, ReconnectingClientFactory):
    def __init__(self, ws_url):
        self.clients = []
        WebSocketServerFactory.__init__(self, ws_url)
        # WebSocketServerFactory.protocol = BroadcastServerProtocol

    def register(self, client):
        if client not in self.clients:
            print("registered client {}".format(client.peer))
            self.clients.append(client)

    def unregister(self, client):
        if client in self.clients:
            print("unregistered client {}".format(client.peer))
            self.clients.remove(client)

    def broadcast(self, msg, optimized=True):
        if optimized:
            # print("broadcasting '{}' ..".format(msg))
            preparedMsg = self.prepareMessage(msg.encode("utf8"))
            [c.sendPreparedMessage(preparedMsg) for c in self.clients]
            # print("prepared message sent to {}".format(c.peer))
        else:
            # print("broadcasting '{}' ..".format(msg))
            [c.sendMessage(msg.encode("utf8")) for c in self.clients]
            # print("message sent to {}".format(c.peer))


class LocalWsBroadCast:
    def __init__(self, ws_url, threaded, tokens, **kwargs):
        kwargs_keys = list(kwargs.keys())
        log.startLogging(sys.stdout)
        opts = {"installSignalHandlers": False}
        self.ServerFactory = BroadcastServerFactory
        self.factory = self.ServerFactory(ws_url)
        self.factory.protocol = BroadcastServerProtocol
        self.tokens = tokens if tokens is not None else [256265]
        listenWS(self.factory)
        if "userid" in kwargs_keys:
            self.kitex = KiteExt(userid=userid)
            if "enctoken" in kwargs_keys:
                self.kitex.login_using_enctoken(
                    userid=userid, enctoken=enctoken, public_token=None
                )
            if "password" in kwargs_keys and "pin" in kwargs_keys:
                self.kitex.login_with_credentials(
                    userid=userid, password=password, pin=pin
                )
            self.kws = self.kitex.kws()
            self.kws.on_ticks = self.on_ticks
            self.kws.on_connect = self.on_connect
            self.kws.on_close = self.on_close
            self.kws.connect(threaded=threaded)

    def on_ticks(self, ws, ticks):
        self.factory.broadcast(
            json.dumps(ticks, sort_keys=False, cls=DateTimeEncoder)
        )  # noqa: E501

    def on_connect(self, ws, response):
        ws.subscribe(self.tokens)
        ws.set_mode(ws.MODE_FULL, self.tokens)

    def on_close(self, ws, code, reason):
        ws.stop()

    def UnsubSubSetMode(self, tokens):
        if self.tokens != [256265] and self.tokens != tokens:
            self.kws.UnsubSubSetMode(self.tokens, tokens, self.kws.MODE_FULL)
            self.tokens = tokens


if __name__ == "__main__":
    sharedList = shared_memory.ShareableList(name=sys.argv[1])
    userid, enctoken, instrument, instToken = (
        sharedList[0],
        sharedList[1],
        sharedList[2],
        sharedList[3],
    )  # noqa: E501
    z = LocalWsBroadCast(
        ws_url="ws://127.0.0.1:5001",
        threaded=True,
        userid=userid,
        enctoken=enctoken,
        tokens=[instToken],  # noqa: E501
    )
    sleep(5)
    while True:
        try:
            z.UnsubSubSetMode([instToken])
            sleep(1)
        except KeyboardInterrupt:
            sharedList.shm.close()
            sharedList.shm.unlink()
            sys.exit(0)
