# app.py
from flask import Flask, request, jsonify
from copy import deepcopy
from math import floor
import json
from collections import namedtuple
import os

app = Flask(__name__)


target_daily_send_vol=650000
number_of_ips=2
initial_per_ip_vol=50
global_warmup_factor=1.5
max_sched_length=50
current_day = 1
overrides = {}
factor_overrides = []
schedule = {}
end_day = -1

@app.route('/create_schedule_config/', methods=['POST'])
def create_schedule_config():
    """ create a new schedule config and write it as json txt file """
    id = request.form.get('id')
    assert id, "You must set the id value"
    filename = f'config{id}.txt'
    if os.path.exists(filename) and os.path.isfile(filename):
        return f"Schedule {filename} already exists", 409
    target_daily_send_vol = request.form.get('target_daily_send_vol', "650000")
    number_of_ips = request.form.get('number_of_ips', "2")
    global_warmup_factor = request.form.get('warmup_factor', "1.5")
    max_sched_length = request.form.get("max_sched_length", "50")
    config = {
        "target_daily_send_vol" : int(target_daily_send_vol),
        "number_of_ips" : int(number_of_ips),
        "global_warmup_factor" : float(global_warmup_factor),
        "max_sched_length" : int(max_sched_length),
        "factor_overrides" : []
    }
    with open(filename, 'w') as outfile:
        json.dump(config, outfile)
    return config

@app.route('/add_factor_override/', methods=['PUT'])
def add_factor_override():
    id = request.form.get('id')
    assert id, "You must choose an id value"
    filename = f'config{id}.txt'
    try:
        with open(filename) as f:
            config = json.load(f)
    except:
        return f"Config file {filename} doesn't exist, you must create it", 404
    print(f"old config: {config}")
    factor_overrides = config["factor_overrides"]
    start_day = request.form.get('start_day')
    end_day = request.form.get('end_day')
    factor = request.form.get('warmup_factor')
    assert start_day, "You must choose a start day (int)"
    assert end_day, "You must choose an end day (int)"
    assert factor, "You must choose the new warmup factor"
    override = [start_day, end_day, factor]
    if override not in factor_overrides:
        factor_overrides.append(override)
    else:
        return f"Override {override} already exists", 409
    config["factor_overrides"] = factor_overrides
    print(f"new config: {config}")
    with open(filename, 'w') as outfile:
        json.dump(config, outfile)
    return config

@app.route('/remove_factor_override/', methods=['PUT'])
def remove_factor_override():
    id = request.form.get('id')
    assert id, "You must choose an id value"
    filename = f'config{id}.txt'
    try:
        with open(filename) as f:
            config = json.load(f)
    except:
        return f"Config file {filename} doesn't exist, you must create it", 404
    print(f"old config: {config}")
    factor_overrides = config["factor_overrides"]
    start_day = request.form.get('start_day')
    end_day = request.form.get('end_day')
    factor = request.form.get('warmup_factor')
    assert start_day, "You must choose a start day (int)"
    assert end_day, "You must choose an end day (int)"
    assert factor, "You must choose the new warmup factor"
    override = [start_day, end_day, factor]
    if override in factor_overrides:
        factor_overrides.remove(override)
    else:
        return f"Override {override} does not exist, so it cannot be removed", 404
    config["factor_overrides"] = factor_overrides
    print(f"new config: {config}")
    with open(filename, 'w') as outfile:
        json.dump(config, outfile)
    return config

# PUT
@app.route('/clear_factor_overrides/', methods=['PUT'])
def clear_factor_overrides():
    id = request.form.get('id')
    assert id, "You must choose an id value"
    filename = f'config{id}.txt'
    try:
        with open(filename) as f:
            config = json.load(f)
    except:
        return f"Config file {filename} doesn't exist, you must create it", 404
    print(f"old config: {config}")
    config["factor_overrides"] = []
    print(f"new config: {config}")
    with open(filename, 'w') as outfile:
        json.dump(config, outfile)
    return config

## GET
@app.route('/get_schedule_config/', methods=['GET'])
def get_schedule_config():
    id = request.form.get('id')
    assert id, "You must choose an id value"
    filename = f'config{id}.txt'
    try:
        with open(filename) as f:
            config = json.load(f)
    except:
        return f"Config file {filename} doesn't exist, you must create it", 404
    return config

## GET
#def build_schedule():
#
#
## GET
#def get_schedule():
#









def set_current_day(day: int):
    """Sets the current day to `day`. The schedule will be fixed (and not recomputed) for previous days"""
    current_day = day

def get_current_day():
    """Return the current day"""
    return current_day

@app.route('/buildsched/', methods=['GET'])
def build_schedule():
    """Compute the schedule, taking into account overrides"""
    print("schedule ID: 555")
    for day in range(1, max_sched_length + 1):
        if day < current_day:
            assert day in schedule
        else:
            if day == 1:
                emails = initial_per_ip_vol * initial_per_ip_vol
            else:
                warmup_factor = global_warmup_factor
                for start_day, end_day, factor in factor_overrides:
                    if start_day <= day <= end_day:
                        warmup_factor = factor
                        break
                if day in overrides:
                    emails = overrides[day]
                else:
                    emails = schedule[day - 1] * warmup_factor
            #round values down to avoid fractional sends
            emails = floor(emails)
            if emails >= target_daily_send_vol:
                emails = target_daily_send_vol
                schedule[day] = emails
                end_day = day
                break
            else:
                schedule[day] = emails
    if end_day == -1:
        end_day = day
    assert schedule[end_day] == target_daily_send_vol
    with open('schedule555.txt', 'w') as outfile:
        json.dump(schedule, outfile)
    return jsonify(schedule)

@app.route('/getsched/', methods=['GET'])
def read_schedule(id = 555):
    try:
        with open(f'schedule{id}.txt') as json_file:
            data = json.load(json_file)
        print(data)
        return data
    except:
        print("file not found!")
        return "file not found"

def add_override(day, emails):
    """Set a specific number of emails to send on a particular `day`"""
    overrides[day] = emails

def add_factor_override(start_day, end_day, factor):
    """Use `factor` instead of the `global_warmup_factor` between `start_day` and `end_day` (inclusive)"""
    factor_overrides.append((start_day, end_day, factor))








#@app.route('/getmsg/', methods=['GET'])
#def respond():
#    # Retrieve the name from url parameter
#    name = request.args.get("name", None)
#
#    # For debugging
#    print(f"got name {name}")
#
#    response = {}
#
#    # Check if user sent a name at all
#    if not name:
#        response["ERROR"] = "no name found, please send a name."
#    # Check if the user entered a number not a name
#    elif str(name).isdigit():
#        response["ERROR"] = "name can't be numeric."
#    # Now the user entered a valid name
#    else:
#        response["MESSAGE"] = f"Welcome {name} to our awesome platform!!"
#
#    # Return the response in json format
#    return jsonify(response)
#
#@app.route('/post/', methods=['POST'])
#def post_something():
#    param = request.form.get('name')
#    print(param)
#    # You can add the test cases you made in the previous function, but in our case here you are just testing the POST functionality
#    if param:
#        return jsonify({
#            "Message": f"Welcome {param} to our awesome platform!!",
#            # Add this option to distinct the POST request
#            "METHOD" : "POST"
#        })
#    else:
#        return jsonify({
#            "ERROR": "no name found, please send a name."
#        })












# A welcome message to test our server
@app.route('/')
def index():
    return "<h1>Welcome to our server !!</h1>"

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
