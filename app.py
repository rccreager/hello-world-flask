# app.py
from flask import Flask, request, jsonify
from copy import deepcopy
from math import floor
import json
from collections import namedtuple
import os

app = Flask(__name__)

config_filename = "config.txt"

def build_schedule(config):
    target_daily_send_vol = config['target_daily_send_vol']
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
            if day in ramp_rate_overrides:
                daily_ramp_rate = ramp_rate_overrides[day]
            if day in volume_overrides:
                emails = volume_overrides[day]
            else:
                emails = schedule[day - 1]["sendVolume"] * daily_ramp_rate
        #round values down to avoid fractional sends
        emails = floor(emails)
        if emails >= target_daily_send_vol:
            emails = target_daily_send_vol
            schedule[day] = {'sendVolume': emails, 'rampRate' : daily_ramp_rate}
            end_day = day
            break
        else:
            schedule[day] = {'sendVolume': emails, 'rampRate' : daily_ramp_rate}
    if end_day == -1:
        end_day = day
    assert schedule[end_day]['sendVolume'] == target_daily_send_vol
    print(f'schedule: {schedule}')
    return jsonify(schedule)

@app.route('/create_schedule/', methods=['POST'])
def create_schedule():
    json_data = request.json
    print(f'json_data: {json_data}')
    target_daily_send_vol = json_data['targetDailySendVolume']
    first_day_vol = json_data['firstDayVolume']
    ramp_rate = json_data['startingRampRate']
    max_schedule_length = json_data['maxScheduleLength']
    assert target_daily_send_vol and first_day_vol and ramp_rate and max_schedule_length
    config = {
        "target_daily_send_vol" : int(target_daily_send_vol),
        "first_day_vol" : int(first_day_vol),
        "ramp_rate" : float(ramp_rate),
        "max_schedule_length" : int(max_schedule_length),
        "ramp_rate_overrides" : {},
        "volume_overrides": {}
    }
    with open(config_filename, 'w') as outfile:
        json.dump(config, outfile)
    schedule = build_schedule(config)
    return schedule 

@app.route('/modify_schedule/', methods=['POST']) 
def modify_schedule():
    try:
        with open(config_filename, 'r') as infile:
            config = json.load(infile)
    except:
        return f"Schedule does not yet exist -- must create before modify\n", 404 
    json_data = request.json
    print(f"json_data: {json_data}")
    data = json.loads(converted_json_data)
    print(f"data: {data}")
    vol_str = "sendVolume"
    ramp_str = "rampRate"
    for override in data:
        day = override["day"]
        volume = int(override[vol_str]) if vol_str in override else None
        ramp_rate = float(override[ramp_str]) if ramp_str in override else None
        assert ramp_rate or volume
        if volume:
            config["volume_overrides"][day] = volume
        if ramp_rate:
            config["ramp_rate_overrides"][day] = ramp_rate
    print(f"new config: {config}")
    with open(config_filename, 'w') as outfile:
        json.dump(config, outfile)
    schedule = build_schedule(config)
    return schedule

#@app.route('/create_schedule_config/', methods=['POST'])
#def create_schedule_config():
#    """ create a new schedule config and write it as json txt file """
#    id = request.form.get('id')
#    assert id, "You must set the id value"
#    filename = f'config{id}.txt'
#    if os.path.exists(filename) and os.path.isfile(filename):
#        return f"Schedule {filename} already exists\n", 409
#    target_daily_send_vol = request.form.get('target_daily_send_vol', "650000")
#    number_of_ips = request.form.get('number_of_ips', "2")
#    global_warmup_factor = request.form.get('warmup_factor', "1.5")
#    max_sched_length = request.form.get("max_sched_length", "50")
#    config = {
#        "target_daily_send_vol" : int(target_daily_send_vol),
#        "number_of_ips" : int(number_of_ips),
#        "global_warmup_factor" : float(global_warmup_factor),
#        "max_sched_length" : int(max_sched_length),
#        "factor_overrides" : [],
#        "volume_overrides": {}
#    }
#    with open(filename, 'w') as outfile:
#        json.dump(config, outfile)
#    return config
#
#def get_config_and_filename():
#    id = request.form.get('id')
#    assert id, "You must choose an id value"
#    filename = f'config{id}.txt'
#    try:
#        with open(filename) as f:
#            config = json.load(f)
#    except:
#        return f"Config file {filename} doesn't exist, you must create it\n", 404
#    return config, filename
#
#def get_factor_override_value():
#    start_day = request.form.get('start_day')
#    end_day = request.form.get('end_day')
#    factor = request.form.get('warmup_factor')
#    assert start_day, "You must choose a start day (int)"
#    assert end_day, "You must choose an end day (int)"
#    assert factor, "You must choose the new warmup factor"
#    return [start_day, end_day, factor]
#
#@app.route('/add_factor_override/', methods=['PUT'])
#def add_factor_override():
#    config, filename = get_config_and_filename()
#    factor_overrides = config["factor_overrides"]
#    override = get_factor_override_value()
#    if override not in factor_overrides:
#        factor_overrides.append(override)
#    else:
#        return f"Override {override} already exists\n", 409
#    config["factor_overrides"] = factor_overrides
#    with open(filename, 'w') as outfile:
#        json.dump(config, outfile)
#    return config
#
#@app.route('/remove_factor_override/', methods=['PUT'])
#def remove_factor_override():
#    config, filename = get_config_and_filename()
#    factor_overrides = config["factor_overrides"]
#    override = get_factor_override_value()
#    if override in factor_overrides:
#        factor_overrides.remove(override)
#    else:
#        return f"Override {override} does not exist, so it cannot be removed\n", 404
#    config["factor_overrides"] = factor_overrides
#    with open(filename, 'w') as outfile:
#        json.dump(config, outfile)
#    return config
#
## PUT
#@app.route('/clear_factor_overrides/', methods=['PUT'])
#def clear_factor_overrides():
#    config, filename = get_config_and_filename()
#    config["factor_overrides"] = []
#    with open(filename, 'w') as outfile:
#        json.dump(config, outfile)
#    return config
#
#
#def get_volume_override_value():
#    day = request.form.get('day')
#    volume = request.form.get('volume')
#    assert day, "You must choose a day whose send volume you want to override (int)"
#    assert volume, f"You must choose a send value to override for day {day}"
#    return day, volume
#
#@app.route('/add_volume_override/', methods=['PUT'])
#def add_volume_override():
#    config, filename = get_config_and_filename()
#    volume_overrides = config["volume_overrides"]
#    day, volume = get_volume_override_value()
#    volume_overrides[day] = volume
#    config["volume_overrides"] = volume_overrides
#    with open(filename, 'w') as outfile:
#        json.dump(config, outfile)
#    return config
#
#@app.route('/remove_volume_override/', methods=['PUT'])
#def remove_volume_override():
#    config, filename = get_config_and_filename()
#    volume_overrides = config["volume_overrides"]
#    day = request.form.get('day')
#    assert day, "You must choose a day to remove from your volume overrides (int)"
#    if day in volume_overrides:
#        del volume_overrides[day]
#    else:
#        return f"Day {day} does not appear in your volume overrides, so it cannot be removed\n", 404
#    config["volume_overrides"] = volume_overrides
#    with open(filename, 'w') as outfile:
#        json.dump(config, outfile)
#    return config
#
## PUT
#@app.route('/clear_volume_overrides/', methods=['PUT'])
#def clear_volume_overrides():
#    config, filename = get_config_and_filename()
#    config["volume_overrides"] = {}
#    with open(filename, 'w') as outfile:
#        json.dump(config, outfile)
#    return config
#
#
#
#
#
#
### GET
#@app.route('/get_schedule_config/', methods=['GET'])
#def get_schedule_config():
#    config, filename = get_config_and_filename()
#    return config
#
## GET
#@app.route('/build_schedule/', methods=['GET'])
#def build_schedule():
#    config, _ = get_config_and_filename()
#    target_daily_send_vol = config['target_daily_send_vol']
#    number_of_ips = config['number_of_ips']
#    global_warmup_factor = config['global_warmup_factor']
#    max_sched_length = config["max_sched_length"]
#    factor_overrides = config["factor_overrides"]
#    volume_overrides = config["volume_overrides"]
#    initial_per_ip_vol=50
#    current_day = 1
#    for day in range(1, max_sched_length + 1):
#        warmup_factor = global_warmup_factor
#        if day == 1:
#            emails = number_of_ips * initial_per_ip_vol
#        else:
#            for start_day, end_day, factor in factor_overrides:
#                if int(start_day) <= day <= int(end_day):
#                    warmup_factor = float(factor)
#                    break
#            if day in volume_overrides:
#                emails = int(volume_overrides[day])
#            else:
#                emails = schedule[day - 1]["send_volume"] * warmup_factor
#        #round values down to avoid fractional sends
#        emails = floor(emails)
#        if emails >= target_daily_send_vol:
#            emails = target_daily_send_vol
#            schedule[day] = {"day": day, "send_volume": emails, "warmup_factor": warmup_factor}
#            end_day = day
#            break
#        else:
#            schedule[day] = {"day": day, "send_volume": emails, "warmup_factor": warmup_factor}
#    if end_day == -1:
#        end_day = day
#    assert schedule[end_day]["send_volume"] == target_daily_send_vol
#    filename = f'schedule{id}.txt'
#    with open(filename, 'w') as outfile:
#        json.dump(schedule, outfile)
#    return jsonify(schedule)
#
#@app.route('/get_schedule/', methods=['GET'])
#def get_schedule():
#    id = request.form.get('id')
#    assert id, "You must choose an id value"
#    filename = f'schedule{id}.txt'
#    try:
#        with open(filename) as f:
#            schedule = json.load(f)
#    except:
#        return f"Schedule file {filename} doesn't exist, you must build it\n", 404
#    return schedule
#
#
#
#
#
#
#
#
##def set_current_day(day: int):
##    """Sets the current day to `day`. The schedule will be fixed (and not recomputed) for previous days"""
##    current_day = day
##
##def get_current_day():
##    """Return the current day"""
##    return current_day
#
##@app.route('/buildsched/', methods=['GET'])
##def build_schedule():
##    """Compute the schedule, taking into account overrides"""
##    print("schedule ID: 555")
##    for day in range(1, max_sched_length + 1):
##        if day < current_day:
##            assert day in schedule
##        else:
##            if day == 1:
##                emails = initial_per_ip_vol * initial_per_ip_vol
##            else:
##                warmup_factor = global_warmup_factor
##                for start_day, end_day, factor in factor_overrides:
##                    if start_day <= day <= end_day:
##                        warmup_factor = factor
##                        break
##                if day in overrides:
##                    emails = overrides[day]
##                else:
##                    emails = schedule[day - 1] * warmup_factor
##            #round values down to avoid fractional sends
##            emails = floor(emails)
##            if emails >= target_daily_send_vol:
##                emails = target_daily_send_vol
##                schedule[day] = emails
##                end_day = day
##                break
##            else:
##                schedule[day] = emails
##    if end_day == -1:
##        end_day = day
##    assert schedule[end_day] == target_daily_send_vol
##    with open('schedule555.txt', 'w') as outfile:
##        json.dump(schedule, outfile)
##    return jsonify(schedule)
#
##@app.route('/getsched/', methods=['GET'])
##def read_schedule(id = 555):
##    try:
##        with open(f'schedule{id}.txt') as json_file:
##            data = json.load(json_file)
##        print(data)
##        return data
##    except:
##        print("file not found!")
##        return "file not found"
##
##def add_override(day, emails):
##    """Set a specific number of emails to send on a particular `day`"""
##    overrides[day] = emails
##
##def add_factor_override(start_day, end_day, factor):
##    """Use `factor` instead of the `global_warmup_factor` between `start_day` and `end_day` (inclusive)"""
##    factor_overrides.append((start_day, end_day, factor))
#
#
#
#
#
#
#
#
##@app.route('/getmsg/', methods=['GET'])
##def respond():
##    # Retrieve the name from url parameter
##    name = request.args.get("name", None)
##
##    # For debugging
##    print(f"got name {name}")
##
##    response = {}
##
##    # Check if user sent a name at all
##    if not name:
##        response["ERROR"] = "no name found, please send a name."
##    # Check if the user entered a number not a name
##    elif str(name).isdigit():
##        response["ERROR"] = "name can't be numeric."
##    # Now the user entered a valid name
##    else:
##        response["MESSAGE"] = f"Welcome {name} to our awesome platform!!"
##
##    # Return the response in json format
##    return jsonify(response)
##
##@app.route('/post/', methods=['POST'])
##def post_something():
##    param = request.form.get('name')
##    print(param)
##    # You can add the test cases you made in the previous function, but in our case here you are just testing the POST functionality
##    if param:
##        return jsonify({
##            "Message": f"Welcome {param} to our awesome platform!!",
##            # Add this option to distinct the POST request
##            "METHOD" : "POST"
##        })
##    else:
##        return jsonify({
##            "ERROR": "no name found, please send a name."
##        })
#
#
#
#
#
#
#
#
#
#
#
#
## A welcome message to test our server
#@app.route('/')
#def index():
#    return "<h1>Welcome to our server !!</h1>"

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
