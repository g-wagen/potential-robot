import csv
import json
import os
import random
import time

import requests
from fake_http_header import FakeHttpHeader


def random_header():
    return FakeHttpHeader().as_header_dict()

def random_wait(a, b):
    time.sleep(round(random.uniform(a, b), 2))

def try_proxy(proxy, timeout=5):
    try:
        requests.get('https://httpbin.org/ip',
                     proxies={'http': proxy, 'https': proxy}, timeout=timeout)
        return proxy
    except:
        pass

def make_ip(li):
    out = []
    try:
        for ip, port in zip(li['IP Address'], li['Port']):
            out.append('{}:{}'.format(ip, int(port)))
        return out
    except:
        return ""

def read_json_list(filename, key=False):
    data = None
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data[key] if key else data
    except FileNotFoundError:
        print("File {} not found".format(filename))


def write_json_list(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except FileNotFoundError:
        print("File {} not found".format(filename))

def save_proxies_list(filename, proxies_list):
    existing_proxies = []

    try:
        with open(filename, 'r') as f:
            existing_proxies = f.readlines()

        with open(filename, 'a') as f:
            for item in proxies_list:
                item = '{}\n'.format(item)
                if item not in existing_proxies:
                    f.write('{}'.format(item))

    except FileNotFoundError:
        with open(filename, 'w') as f:
            for item in proxies_list:
                f.write('{}\n'.format(item))

