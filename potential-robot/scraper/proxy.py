import json
import multiprocessing
import os
import pickle
import random
import time
from functools import partial

import pandas as pd
import requests
from fake_http_header import FakeHttpHeader

### Helper functions

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


### Main proxy functions

def scrape_proxies():
    """
    Scrapes https proxies from different websites using pandas and requests.

    Returns proxy servers as a list of ip_address:port strings
    for further processing.
    """

    # This is for handling pagination
    page_counter = 1
    scraped_proxies = []

    # Grab the proxies
    print('Gathering proxies from freeproxylist.cc')
    while True:
        try:
            url = "https://freeproxylist.cc/servers/{}.html".format(page_counter)
            r = requests.get(url, headers=random_header()).text
            tables = pd.read_html(r)

            if len(tables[0]) > 1:
                dataframe = tables[0]
                filtered_proxies = dataframe[(dataframe['Https'] == 'Yes') &
                                            (dataframe['Anonymity'] == 'Elite')]
                filtered_proxies = filtered_proxies.drop(
                    ['Country', 'Code', 'Https', 'Last Checked', 'Anonymity'],
                    axis=1)

                scraped_proxies += make_ip(filtered_proxies)

                page_counter += 1
                # random_wait(1, 3)
            else:
                break
        except:
            pass
            # random_wait(1, 3)

    print('Gathering proxies from hidemy.name')
    page_counter = 0
    while True:
        try:
            url = 'https://hidemy.name/en/proxy-list/?start={}'.format(page_counter)
            params = {'type': 'hs5', 'anon': 4}
            r = requests.get(url, headers=random_header(), params=params).text
            tables = pd.read_html(r)

            if len(tables[0]) > 1:
                # real_page_number = int(((page_counter / 64) + 1))
                dataframe = tables[0]
                filtered_proxies = dataframe[(dataframe['Type'] == 'HTTPS') &
                                            (dataframe['Anonymity'] == 'High')]
                filtered_proxies = filtered_proxies.drop(
                    ['Country, City', 'Speed', 'Type', 'Anonymity', 'Latest update'],
                    axis=1)

                scraped_proxies += make_ip(filtered_proxies)

                page_counter += 64
                # random_wait(1, 3)
            else:
                break
        except:
            pass
            # random_wait(1, 3)

    print('Gathering proxies from free-proxy-list.net')
    while True:
        try:
            r = requests.get("https://free-proxy-list.net/",
                            headers=random_header()).text
            tables = pd.read_html(r)

            dataframe = tables[0]
            filtered_proxies = dataframe[(dataframe['Https'] == 'yes') &
                                        (dataframe['Anonymity'] == 'elite proxy')]
            filtered_proxies = filtered_proxies.drop(
                ['Code', 'Https', 'Country', 'Anonymity', 'Last Checked', 'Google'],
                axis=1)

            scraped_proxies += make_ip(filtered_proxies)
            break
        except:
            pass
            # random_wait(1, 3)

    print('Gathering proxies from proxyscan.io')
    while True:
        try:
            url = 'https://www.proxyscan.io/api/proxy?type=https&limit=10000&level=elite'
            r = requests.get(url, headers=random_header()).json()
            scraped_proxies += [f"{x['Ip']}:{x['Port']}" for x in r]
            break
        except:
            pass

    return scraped_proxies

def test_proxies(proxies_list):
    print('Testing proxies')
    # Test if the proxies work
    pool = multiprocessing.Pool()
    with multiprocessing.Pool(os.cpu_count()) as pool:
        tested_proxies = pool.map(partial(try_proxy, timeout=7), proxies_list)
    working_proxies_list = [x for x in tested_proxies if x is not None]

    return working_proxies_list

def perform_proxy_request(url, proxies):
    start_time = time.time()
    while True and time.time() - start_time < 20:
        # Choose a random proxy
        proxy_chooser = proxies[random.randint(0, len(proxies) - 1)]
        # Try if it actually works ...
        try:
            req = requests.get(
                url, # The URL
                headers=random_header(), # Random Header
                timeout=3, # 3 second timeout because time is money
                proxies={'https': proxy_chooser}) # Use https proxy
            # Break out of the while if it worked!
            return req
            break
        except:
            # In case it doesn't work just wait a little bit and retry
            random_wait(1, 3)
    print("No response within 20 seconds. Terminating!")
    return None

def pickler(filename):
    unpickled = None
    def prox_pickle(filename):
        with open(filename, 'wb') as f:
            generate_proxies = test_proxies(scrape_proxies())
            pickle.dump(generate_proxies, f)

    def prox_unpickle(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)

    if not os.path.exists(filename):
        print(f'Proxies file does not exists: {filename}. Generating ...')
        prox_pickle(filename)

    try:
        unpickled = prox_unpickle(filename)
        print(f'Read existing proxies file: {filename}')
    except:
        print(f'Broken proxies file: {filename}. Regenerating ...')
        prox_pickle(filename)
        unpickled = prox_unpickle(filename)

    return unpickled
