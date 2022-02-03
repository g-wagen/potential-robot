# coding=utf-8

import multiprocessing
from functools import partial

import pandas as pd
import requests
import utils

first_proxies_list = []
page_counter = 1


# Grab the proxies
print('Gathering proxies from freeproxylist.cc')
while True:
    try:
        url = "https://freeproxylist.cc/servers/{}.html".format(page_counter)
        r = requests.get(url, headers=utils.random_header()).text
        tables = pd.read_html(r)
        print(url)

        if len(tables[0]) > 1:
            print('Scraping Page {} of freeproxylist.cc'.format(page_counter))
            dataframe = tables[0]
            filtered_proxies = dataframe[(dataframe['Https'] == 'Yes') &
                                         (dataframe['Anonymity'] == 'Elite')]
            filtered_proxies = filtered_proxies.drop(
                ['Country', 'Code', 'Https', 'Last Checked', 'Anonymity'],
                axis=1)

            first_proxies_list += utils.make_ip(filtered_proxies)

            page_counter += 1
            utils.random_wait(1, 4)
        else:
            break
    except:
        print('bad url')
        utils.random_wait(1, 3)


print('Gathering proxies from hidemy.name')
page_counter = 0
while True:
    try:
        url = 'https://hidemy.name/en/proxy-list/?start={}'.format(page_counter)
        params = {'type': 'hs5', 'anon': 4}
        r = requests.get(url, headers=utils.random_header(), params=params).text
        tables = pd.read_html(r)
        print(url)

        if len(tables[0]) > 1:
            real_page_number = int(((page_counter / 64) + 1))
            print('Scraping Page {} of hidemy.name'.format(real_page_number))
            dataframe = tables[0]
            filtered_proxies = dataframe[((dataframe['Type'] == 'HTTPS') |
                                         (dataframe['Type'] == 'HTTP, HTTPS'))
                                         & (dataframe['Anonymity'] == 'High')]
            filtered_proxies = filtered_proxies.drop(
                ['Country, City', 'Speed', 'Type', 'Anonymity', 'Latest update'],
                axis=1)

            first_proxies_list += utils.make_ip(filtered_proxies)

            page_counter += 64
            utils.random_wait(2, 7)
        else:
            break
    except:
        print('bad url')
        utils.random_wait(2, 4)


print('Gathering proxies from free-proxy-list.net')
while True:
    try:
        r = requests.get("https://free-proxy-list.net/",
                         headers=utils.random_header()).text
        tables = pd.read_html(r)

        dataframe = tables[0]
        filtered_proxies = dataframe[(dataframe['Https'] == 'yes') &
                                     (dataframe['Anonymity'] == 'elite proxy')]
        filtered_proxies = filtered_proxies.drop(
            ['Code', 'Https', 'Country', 'Anonymity', 'Last Checked', 'Google'],
            axis=1)

        first_proxies_list += utils.make_ip(filtered_proxies)
        break
    except:
        print('bad url')
        utils.random_wait(1, 3)


print('Gathering proxies from proxyscan.io')
while True:
    try:
        url = 'https://www.proxyscan.io/api/proxy?type=https&limit=10000&level=elite'
        r = requests.get(url, headers=utils.random_header()).json()
        first_proxies_list += ["{}:{}".format(x['Ip'], x['Port']) for x in r]
        break
    except:
        pass

# Read existing proxies
proxies_filename = 'working_proxies.json'
existing_proxies = utils.read_json_list(proxies_filename, key='proxies')


# Test existing proxies together with the new proxies
try:
    first_proxies_list = first_proxies_list + [x for x in existing_proxies]
except NameError:
    print("Can't find {}. Skipping.".format(proxies_filename))


# Test if the proxies work
pool = multiprocessing.Pool()
tested_proxies = pool.map(
    partial(utils.try_proxy, timeout=7), first_proxies_list)
working_proxies_list = [x for x in tested_proxies if x is not None]


# Write proxies to file
json_data = {'proxies': working_proxies_list}
utils.write_json_list(proxies_filename, json_data)
print('Output working proxies list to {}'.format(proxies_filename))