from time import sleep

import requests
import yaml
import vk
import logging
import time
import csv
import datetime
from tools import is_file_exists


class VKWrapper(object):
    def __init__(self, token):
        self.session = vk.Session(access_token=token)
        self.api = vk.API(self.session, v='5.85')
        self.last_command_access = time.time()
        self.command_pause = 0.3
        self.logger = logging.getLogger("VKWrapper")

    def get_user(self, user_id, fields=""):
        while True:
            try:
                result = self.api.users.get(user_ids=user_id, fields=fields)
                self.last_command_access = time.time()
                break
            except requests.exceptions.ReadTimeout:
                sleep(2)
                continue
            except requests.exceptions.RequestException:
                sleep(4)
                continue
            except vk.exceptions.VkAPIError as e:
                self.logger.error(e)
                if "invalid access_token" in e.message:
                    raise
                sleep(2)
                continue
        self.sleep()
        return result[0]

    def sleep(self):
        current_time = time.time()
        time_passed = current_time - self.last_command_access
        if time_passed < self.command_pause:
            time_to_sleep = self.command_pause - time_passed
            sleep(time_to_sleep)


class VKObserver(object):
    online_platform = {1: "Mobile web or undefined app",
                       2: "iPhone",
                       3: "iPad",
                       4: "Android",
                       5: "Windows Phone",
                       6: "Windows Metro",
                       7: "Full web or undefined app"}

    def __init__(self):
        self.logger = logging.getLogger("VKObserver")
        log_file = logging.FileHandler(filename="VKObserver.log")
        self.logger.addHandler(log_file)

        self.logger.info("Loading settings.")
        with open("./settings.yaml", "r") as file:
            settings = yaml.load(file)
        self.sleep_time = settings["sleep_time"]
        self.token = settings["token"]

        self.logger.info("Initializing VKWrapper.")
        self.vk_wrapper = VKWrapper(self.token)

        self.logger.info("Initializing targets information.")
        self.load_targets(settings["targets"])

        self.logger.info("LIFTOFF!!!")
        self.running = False

    def load_targets(self, targets):
        self.targets = []
        for target_id in targets:
            target = {}
            target["id"] = target_id
            user = self.vk_wrapper.get_user(target_id, "last_seen, online")
            target["last_status"] = user["online"]
            target["full_name"] = "{} {}".format(user['first_name'], user['last_name'])
            target["last_platform"] = user["last_seen"]["platform"]
            target["status_time"] = time.time()
            self.write_csv_header(target)
            self.targets.append(target)

    def write_csv_header(self, target):
        name = target["full_name"]
        if not is_file_exists("Results/{}.csv".format(name)):
            with open("Results/{}.csv".format(name), "w") as file:
                csvTable = csv.writer(file)
                csvTable.writerow(["Begin online period", "End online period", "Online time", "Platform ID",
                                   "Platform name"])

    def write_status(self, target):
        name = target["full_name"]
        platform = target["last_platform"]
        status_time = target["status_time"]
        platform_string = self.online_platform[platform]
        change_status_time = datetime.datetime.now().replace(microsecond=0)
        delta_time = change_status_time - datetime.datetime.fromtimestamp(status_time).replace(microsecond=0)

        with open("Results/{}.csv".format(name), "a") as file:
            writer = csv.writer(file)
            writer.writerow([datetime.datetime.fromtimestamp(status_time).strftime("%y/%m/%d %H:%M:%S"),
                             change_status_time.strftime("%y/%m/%d %H:%M:%S"), str(delta_time),
                             platform, platform_string])

    def observe(self):
        for target in self.targets:
            target_id = target["id"]
            last_status = target["last_status"]
            last_platform = target["last_platform"]
            user = self.vk_wrapper.get_user(target_id, "last_seen, online")
            # DEBUG BEGIN
            if "online" not in user:
                self.logger.critical("online is not in user dict:\n{}".format(user))
            if "last_seen" not in user:
                self.logger.critical("last_seen is not in user dict:\n{}".format(user))
            # DUDE, THIS PARTY SUCKS, I hugging HATE THOSE PEOPLE
            if "platform" not in user["last_seen"]:
                # HATRED GOES HERE
                self.logger.error("platform is not in user dict:\n{}".format(user))
                user["last_seen"]["platform"] = target["last_platform"]
            # DEBUG END
            current_status = user["online"]
            current_platform = user["last_seen"]["platform"]
            if last_status != current_status or last_platform != current_platform:
                if last_status == 1 and current_status == 0:
                    self.write_status(target)

                if last_platform != current_platform:
                    self.write_status(target)
                target["last_status"] = current_status
                target["last_platform"] = current_platform
                target["status_time"] = time.time()
                # self.write_status(target)
                self.logger.info("{} went ".format(target['full_name']) +
                                 "{}; ".format('online' if target['last_status'] == True else 'offline') +
                                 "Platform: {}".format(self.online_platform[target['last_platform']]))

    def run(self):
        self.running = True
        while self.running:
            self.observe()
            sleep(self.sleep_time)
