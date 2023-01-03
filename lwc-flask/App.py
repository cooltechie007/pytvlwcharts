from flask import (
    Flask,
    jsonify,
    request,
    Response,
    render_template,
)  # noqa: E501
import sys
import subprocess
import datetime as dt
from time import sleep
from KiteExtra import KiteExt
from datetime import timedelta as td
from datetime import datetime as dtdt
from flask_cors import CORS, cross_origin
from multiprocessing import shared_memory

# from flask import send_from_directory

app = Flask(__name__)


@app.route("/")
def home():
    global sharedList, wsServerInitiated
    args = request.args
    instrument = args.get("instrument")
    instToken = args.get("token")
    # print(instrument, instToken)
    if None not in (instrument, instToken):
        sharedList[2], sharedList[3] = instrument, int(instToken)
        # print(sharedList[2], sharedList[3])
        if not wsServerInitiated:
            subprocess.Popen(
                [sys.executable, "SyncWSserver.py", sharedList.shm.name]
            )  # noqa: E501
            wsServerInitiated = True
            sleep(3)
    return render_template("index.html")


@app.route("/chart", methods=["GET"])
@cross_origin()
def chart():
    global sharedList
    if (
        None not in (sharedList[2], sharedList[3])
        and sharedList[2] != "instrument"
        and sharedList[3] != 0
    ):
        return jsonify(
            kite.historical_data(
                instrument_token=sharedList[3],
                from_date=dtdt.combine(
                    dtdt.now().date() - td(days=7), dt.time(9, 15, 0)
                ),
                to_date=dtdt.now(),
                interval="minute",
                continuous=False,
                oi=False,
            )
        )
    else:
        return Response(
            status=401,
            response={
                "status": "Erroe",
                "message": "Intrument Name and Token Field Were Empty!",
            },  # noqa: E501
            content_type="application/json",
        )


if __name__ == "__main__":
    wsServerInitiated = True
    # https://68o9pf66q0.execute-api.ap-south-1.amazonaws.com/
    userid = "VT5229"
    enctoken = "exTwFgWuxQ63Ok6D1k8TJWDyW53cYl8iPvfxduK/jmtchdPGEBfbiZGASrzGYJ5Y4qRRsu3TOtX4JFJDdKigYQ0jYmNgPS07us7EIY2Fy5WYsW0X6rd06A=="  # noqa: E501
    sharedList = shared_memory.ShareableList(
        [userid, enctoken, "instrument", 0]
    )  # noqa: E501
    kite = KiteExt(userid=userid)
    kite.login_using_enctoken(userid, enctoken, public_token=None)
    print(
        "Open http://127.0.0.1:5000/?instrument=RELIANCE&token=738561"  # noqa: E501
    )  # noqa: E501
    app.run(host="0.0.0.0", port=5000, debug=True)
    sharedList.shm.close()
    sharedList.shm.unlink()
    del sharedList
