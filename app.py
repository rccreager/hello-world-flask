# app.py
from flask import Flask, request, jsonify
from copy import deepcopy
from math import floor
import json
from collections import namedtuple
import os

app = Flask(__name__)

config_filename = "config.txt"
schedule_filename = "schedule.txt"


def build_schedule(config):
    """
    Given a config dictionary, create a schedule, write it to schedule.txt as 
    json, and return the json-ified schedule.

    Args:
        config: dictionary with the following keys and values:
            'target_daily_send_volume': (int) number of sends you want to reach
            'first_day_volume': (int) number of sends for day 0
            'ramp_rate': (float) daily ramp rate. overrides are handled separately
            'max_schedule_length': (int) longest possible length of schedules
            'ramp_rate_overrides': (dict) map days to overridden ramp rates
            'volume_overrides': (dict) map days to volume overrides
    """
    target_daily_send_vol = config["target_daily_send_vol"]
    first_day_vol = config["first_day_vol"]
    ramp_rate = config["ramp_rate"]
    max_schedule_length = config["max_schedule_length"]
    ramp_rate_overrides = config["ramp_rate_overrides"]
    volume_overrides = config["volume_overrides"]
    current_day = 0
    schedule = {}

    for day in range(0, max_schedule_length + 1):
        daily_ramp_rate = ramp_rate
        if day == 0:
            emails = first_day_vol
        else:
            # if the ramp rate was overridden, get the overrideen value
            if day in ramp_rate_overrides:
                daily_ramp_rate = ramp_rate_overrides[day]
            # if your email volume was override, use overridden value. Else calculate using ramp rate and previous day's value
            if day in volume_overrides:
                emails = volume_overrides[day]
            else:
                emails = schedule[day - 1]["sendVolume"] * daily_ramp_rate
        # round values down to avoid fractional sends
        emails = floor(emails)
        # if you overshot your target daily send volume, then set final day's volume to target and end
        if emails >= target_daily_send_vol:
            emails = target_daily_send_vol
            schedule[day] = {"sendVolume": emails, "rampRate": daily_ramp_rate}
            break
        else:
            schedule[day] = {"sendVolume": emails, "rampRate": daily_ramp_rate}
    print(f"schedule: {schedule}")
    with open(schedule_filename, "w") as outfile:
        json.dump(schedule, outfile)
    return jsonify(schedule)


@app.route("/create_schedule/", methods=["POST"])
def create_schedule():
    """
    Create a new schedule configuration and schedule, and return the json-ified 
    schedule.

    Expected request JSON payload:
        'targetDailySendVolume': (int)
        'firstDayVolume': (int)
        'startingRampRate': (float)
        'maxScheduleLength': (int)
    """
    json_data = request.json
    print(f"json_data: {json_data}")
    target_daily_send_vol = json_data["targetDailySendVolume"]
    first_day_vol = json_data["firstDayVolume"]
    ramp_rate = json_data["startingRampRate"]
    max_schedule_length = json_data["maxScheduleLength"]
    assert target_daily_send_vol and first_day_vol and ramp_rate and max_schedule_length
    config = {
        "target_daily_send_vol": int(target_daily_send_vol),
        "first_day_vol": int(first_day_vol),
        "ramp_rate": float(ramp_rate),
        "max_schedule_length": int(max_schedule_length),
        "ramp_rate_overrides": {},
        "volume_overrides": {},
    }
    with open(config_filename, "w") as outfile:
        json.dump(config, outfile)
    schedule = build_schedule(config)
    return schedule


@app.route("/get_schedule/", methods=["GET"])
def get_schedule():
    """
    Geturn the most recent schedule.
    """
    try:
        with open(schedule_filename, "r") as infile:
            schedule = json.load(infile)
    except Exception as e:
        print(e)
        return f"Schedule does not yet exist -- must create before getting\n", 404
    return schedule


@app.route("/modify_schedule/", methods=["POST"])
def modify_schedule():
    """
    Modify an existing schedule config, rebuild the schedule, and return the 
    json-ified schedule.

    Expecting JSON array as payload, formatted like so:
    [
      {
        day: number (day offset of starting date)
        sendVolume: number representing new volume for the day
        rampRate: number (number representing new ramp rate e.g. 2 would be 2x)
      },
      {
        day: number (day offset of starting date)
        sendVolume: number representing new volume for the day
        rampRate: number (number representing new ramp rate e.g. 2 would be 2x)
      }
    ]
    You only need to specify either sendVolume or rampRate; if you specify both,
    then the override for sendVolume will be used.
    """
    try:
        with open(config_filename, "r") as infile:
            config = json.load(infile)
    except Exception as e:
        print(e)
        return f"Schedule does not yet exist -- must create before modify\n", 404
    # when writing out config as json, all keys are automatically converted to strings
    # so let's first convert them back to ints
    ramp_rate_overrides = {}
    volume_overrides = {}
    for key, value in config["ramp_rate_overrides"].items():
        ramp_rate_overrides[int(key)] = float(value)
    for key, value in config["volume_overrides"].items():
        volume_overrides[int(key)] = int(value)
    config["ramp_rate_overrides"] = ramp_rate_overrides
    config["volume_overrides"] = volume_overrides
    # next, let's add the new overrides to our config
    data = request.json
    print(f"initial config: {config}")
    print(f"json data: {data}")
    vol_str = "sendVolume"
    ramp_str = "rampRate"
    for _, override in data.items():
        day = int(override["day"])
        volume = int(override[vol_str]) if vol_str in override else None
        ramp_rate = float(override[ramp_str]) if ramp_str in override else None
        print(f"day: {day}, volume: {volume}, ramp_rate: {ramp_rate}")
        assert ramp_rate or volume
        if volume:
            config["volume_overrides"][day] = volume
        if ramp_rate:
            config["ramp_rate_overrides"][day] = ramp_rate
    print(f"new config: {config}")
    with open(config_filename, "w") as outfile:
        json.dump(config, outfile)
    schedule = build_schedule(config)
    return schedule


if __name__ == "__main__":
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
