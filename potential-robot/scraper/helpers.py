import hashlib
import json
import os
import pickle
import random
import time


def generate_dict_md5hash(input_dict):
    """Generate an md5 hash for a dictionary"""
    # # Remove an existing hash if there is one
    # if input_dict.get('md5'):
    #     input_dict.pop('md5')

    # To generate a hash for input_dict it
    # has to be converted to text form.
    # Let's use json to help us.
    input_dict_text = json.dumps(input_dict).encode('utf-8')
    input_dict_hash = hashlib.md5(input_dict_text).hexdigest()

    return input_dict_hash

def insert_md5hash_to_dict(input_dict, hash):
    input_dict['md5'] = hash
    return input_dict

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

def random_list_choice(list_input):
    random_index = random.randint(0, len(list_input) - 1)
    return list_input[random_index]

def random_wait(a, b):
    time.sleep(round(random.uniform(a, b), 2))

def pickler(filename, data):
    unpickled = None
    def save_pickle(filename):
        with open(filename, 'wb') as f:
            pickle.dump(data, f)

    def load_pickle(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)

    if not os.path.exists(filename):
        print(f'File does not exists: {filename}. Generating ...')
        save_pickle(filename)

    try:
        unpickled = load_pickle(filename)
        print(f'Read existing file: {filename}')
    except:
        print(f'Broken file: {filename}. Regenerating ...')
        save_pickle(filename)
        unpickled = load_pickle(filename)

    return unpickled
