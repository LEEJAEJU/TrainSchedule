from flask import Flask, render_template, request
import requests  # pip install requests
from urllib.parse import urlencode, unquote
import json
import csv
from dotenv import load_dotenv
import os
import time


load_dotenv()
myTrain_KEY = os.environ.get("Train_KEY")
print(myTrain_KEY)
app = Flask(__name__)  # Initialise app

# Config
station_dict = {}

with open(
    "/home/ubuntu/train_test/train_sch/train_code.csv", mode="r"
) as inp:
    reader = csv.reader(inp)
    station_dict = {rows[0]: rows[1] for rows in reader}


def city_code_find(station):
    if station in station_dict:
        for key_v in station_dict.keys():
            if key_v == station:
                city_code_num = station_dict[station]
                return city_code_num
    else:
        return 1


def station_id_find(station_name, station_code):
    url = "https://apis.data.go.kr/1613000/TrainInfoService/getCtyAcctoTrainSttnList"
    queryString = "?" + urlencode(
        {
            "ServiceKey": unquote(myTrain_KEY),
            "pageNo": "1",
            "numOfRows": "300",
            "_type": "json",
            "cityCode": station_code,
        }
    )

    train_response = requests.get(url + queryString)
    train_dict = json.loads(train_response.text)
    train_response = train_dict.get("response")
    train_body = train_response.get("body")
    train_items = train_body.get("items")
    train_item = train_items.get("item")

    print(train_item)
    for item in train_item:
        if item.get("nodename") == station_name:
            city_id = item.get("nodeid")
            break

    return city_id


def route_find(start_station_id, end_station_id, train_number, today):
    global ttse
    ttse = []
    url = "https://apis.data.go.kr/1613000/TrainInfoService/getStrtpntAlocFndTrainInfo"
    queryString = "?" + urlencode(
        {
            "ServiceKey": unquote(myTrain_KEY),
            "pageNo": "1",
            "numOfRows": "300",
            "_type": "json",
            "depPlaceId": start_station_id,
            "arrPlaceId": end_station_id,
            "depPlandTime": today,
            "trainGradeCode": train_number,
        }
    )

    train_response = requests.get(url + queryString)
    train_dict = json.loads(train_response.text)
    train_response = train_dict.get("response")
    train_body = train_response.get("body")
    train_items = train_body.get("items")

    if train_items == "":
        print("없습니다.")
    else:
        train_item = train_items.get("item")
        ttse.append(train_item)
        test(train_item)


def time_cul(tt_table, start_time, end_time):
    global time_table
    tt_table.append(
        str(start_time)[8]
        + str(start_time)[9]
        + ":"
        + str(start_time)[10]
        + str(start_time)[11]
    )
    tt_table.append(
        str(end_time)[8]
        + str(end_time)[9]
        + ":"
        + str(end_time)[10]
        + str(end_time)[11]
    )


def time_make(tt_table, start_time, end_time):
    st_h = int(str(start_time)[8]) * 10 + int(str(start_time)[9])
    st_m = int(str(start_time)[10]) * 10 + int(str(start_time)[11])
    et_h = int(str(end_time)[8]) * 10 + int(str(end_time)[9])
    et_m = int(str(end_time)[10]) * 10 + int(str(end_time)[11])
    ft_h = 0
    ft_m = 0
    if et_h > st_h:
        ft_h = et_h - st_h
        ft_m = et_m - st_m
        if ft_m < 0:
            ft_h -= 1
            ft_m += 60
    else:
        ft_h = (et_h + 24) - st_h
        ft_m = et_m - st_m
        if ft_m < 0:
            ft_h -= 1
            ft_m += 60

    ft = ""
    if ft_m < 10:
        ft = str(ft_h) + ":" + "0" + str(ft_m)
    else:
        ft = str(ft_h) + ":" + str(ft_m)

    tt_table.append(ft)


def test(train_info):
    global time_table
    try:
        for tt in train_info:
            tt_table = []
            tt_table.append(tt.get("traingradename"))
            tt_table.append(tt.get("depplacename"))
            tt_table.append(tt.get("arrplacename"))
            start_time = tt.get("depplandtime")
            end_time = tt.get("arrplandtime")
            time_cul(tt_table, start_time, end_time)
            time_make(tt_table, start_time, end_time)

            time_table.append(tt_table)
    except:
        tt_table = []
        tt_table.append(train_info.get("traingradename"))
        tt_table.append(train_info.get("depplacename"))
        tt_table.append(train_info.get("arrplacename"))
        start_time = train_info.get("depplandtime")
        end_time = train_info.get("arrplandtime")
        time_cul(tt_table, start_time, end_time)
        time_make(tt_table, start_time, end_time)

        time_table.append(tt_table)


@app.route("/", methods=["GET", "POST"])
def index():
    global time_table
    today = time.strftime("%Y%m%d")
    time_table = []
    if request.method == "POST":
        start_station = request.form["start"]
        end_station = request.form["end"]
        data_check = request.form["ride"]
        if start_station != "" and end_station != "" and data_check != "":
            if data_check == "train":
                train_num = [
                    "00",
                    "01",
                    "02",
                    "03",
                    "04",
                    "06",
                    "07",
                    "08",
                    "09",
                    "10",
                    "16",
                    "17",
                ]
                start_city_code = city_code_find(start_station)
                end_city_code = city_code_find(end_station)

                if start_city_code == 1 or end_city_code == 1:
                    return render_template("index.html", valuecheck=1)

                start_station_id = station_id_find(start_station, start_city_code)
                end_station_id = station_id_find(end_station, end_city_code)
                for train_number in train_num:
                    route_find(start_station_id, end_station_id, train_number, today)

            elif data_check == "bus":
                start_city_code = city_code_find(start_station)
                end_city_code = city_code_find(end_station)

                start_station_id = station_id_find(start_station, start_city_code)
                end_station_id = station_id_find(end_station, end_city_code)
                route_find(start_station_id, end_station_id)
            else:
                return render_template("index.html")
        else:
            return render_template("index.html")
    else:
        return render_template("index.html")

    if not time_table:
        return render_template("index.html", valuecheck=1)
    else:
        time_table.sort(key=lambda x: x[3])
        print(time_table)
        return render_template("index.html", list=time_table)


@app.route("/")
def index2():
    return render_template("index.html")


@app.route("/select")
def index3():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
