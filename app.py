# app.py
from flask import Flask, request, jsonify

from flask_restful import Resource, Api

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient import errors

from copy import deepcopy

app = Flask(__name__)



class Warmup:
    """
    Class to automatically compute and maintain warmup schedules
    """

    def __init__(
        target_daily_send_vol=650000,
        number_of_ips=2,
        initial_per_ip_vol=50,
        number_engaged_users=500000,
        warmup_factor=1.5,
        max_warmup_schedule_length=50,
    ):
        """
        Parameters
        ----------
        target_daily_send_vol: int, default=650000
            Number of daily sends targeted
        number_of_ips: int, default=2
            Number of IP addresses used for sending
        initial_per_ip_vol: int, default=50
            Initial number of messages to send per IP
        number_engaged_users: int, default=500000
            Number of engaged users (not currently used)
        warmup_factor: float, default=1.5
            Daily multiplier to sends
        max_warmup_schedule_length: int, default=50
            Maximum length of warmup schedule
        """
        self.target_daily_send_vol = target_daily_send_vol
        self.number_of_ips = number_of_ips
        self.initial_per_ip_vol = initial_per_ip_vol
        self.number_engaged_users = number_engaged_users
        self.warmup_factor = warmup_factor
        self.max_warmup_schedule_length = max_warmup_schedule_length
        self.current_day = 1
        self.overrides = {}
        self.factor_overrides = []
        self.schedule = {}
        self.end_day = -1

    def set_current_day(day: int):
        """Sets the current day to `day`. The schedule will be fixed (and not recomputed) for previous days"""
        self.current_day = day

    def get_current_day():
        """Return the current day"""
        return self.current_day

    def build_schedule():
        """Compute the schedule, taking into account overrides"""
        for day in range(1, self.max_warmup_schedule_length + 1):
            if day < current_day:
                assert day in self.schedule
            else:
                if day == 1:
                    emails = self.initial_per_ip_vol * self.initial_per_ip_vol
                else:
                    warmup_factor = self.warmup_factor
                    for start_day, end_day, factor in self.factor_overrides:
                        if start_day <= day <= end_day:
                            warmup_factor = factor
                            break
                    if day in self.overrides:
                        emails = self.overrides[day]
                    else:
                        emails = self.schedule[day - 1] * warmup_factor
                if emails >= target_daily_send_vol:
                    emails = target_daily_send_vol
                    self.schedule[day] = emails
                    self.end_day = day
                    break
                else:
                    self.schedule[day] = emails
        if self.end_day == -1:
            self.end_day = day
        assert self.schedule[self.end_day] == target_daily_send_vol

    def get_schedule():
        """Return a copy of the current schedule"""
        return deepcopy(self.schedule)

    def add_override(day, emails):
        """Set a specific number of emails to send on a particular `day`"""
        self.overrides[day] = emails

    def add_factor_override(start_day, end_day, factor):
        """Use `factor` instead of the `self.warmup_factor` between `start_day` and `end_day` (inclusive)"""
        self.factor_overries.append((start_day, end_day, factor))








@app.route('/getmsg/', methods=['GET'])
def respond():
    # Retrieve the name from url parameter
    name = request.args.get("name", None)

    # For debugging
    print(f"got name {name}")

    response = {}

    # Check if user sent a name at all
    if not name:
        response["ERROR"] = "no name found, please send a name."
    # Check if the user entered a number not a name
    elif str(name).isdigit():
        response["ERROR"] = "name can't be numeric."
    # Now the user entered a valid name
    else:
        response["MESSAGE"] = f"Welcome {name} to our awesome platform!!"

    # Return the response in json format
    return jsonify(response)

@app.route('/post/', methods=['POST'])
def post_something():
    param = request.form.get('name')
    print(param)
    # You can add the test cases you made in the previous function, but in our case here you are just testing the POST functionality
    if param:
        return jsonify({
            "Message": f"Welcome {param} to our awesome platform!!",
            # Add this option to distinct the POST request
            "METHOD" : "POST"
        })
    else:
        return jsonify({
            "ERROR": "no name found, please send a name."
        })

# A welcome message to test our server
@app.route('/')
def index():
    return "<h1>Welcome to our server !!</h1>"

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
