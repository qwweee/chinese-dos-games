import hashlib
import inspect
import os
import json
import urllib.request
import ssl

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, wait

root = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

ssl._create_default_https_context = ssl._create_unverified_context

PREFIX = "https://dos_bin.zczc.cz/"
DESTINATION = os.path.join(root, 'bin')
BUF_SIZE = 65536
THREAD_SIZE = 10

with open(os.path.join(root, 'games.json'), encoding='utf8') as f:
    content = f.read()
    game_infos_ordered = json.loads(content, object_pairs_hook=OrderedDict)
    game_infos = json.loads(content)


def update_json(ordered_dict):
    with open(os.path.join(root, 'games.json'), encoding='utf8', mode='w') as f:
        f.write(json.dumps(ordered_dict, indent=2, ensure_ascii=False))


def generate_sha256(file):
    """
    generate file's sha256 checksum

    :param file: file's location
    :return: sha256 string
    """
    sha256 = hashlib.sha256()
    with open(file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()

def download(identifier, url, file):
    print('Downloading {} game file'.format(identifier))
    urllib.request.urlretrieve(url, file)

def main(prefix=PREFIX, destination=DESTINATION):
    """
    check game archives whether exists and their checksum, download from target.

    :return: the list of downloaded file
    """
    # create folder
    folder = os.path.isdir(destination)
    if not folder:
        os.makedirs(destination)

    executor = ThreadPoolExecutor(max_workers=THREAD_SIZE)
    all_task = list()

    downloaded = list()
    for identifier in game_infos['games'].keys():
        file = os.path.normcase(os.path.join(destination, identifier + '.zip'))
        url = prefix + urllib.parse.quote(identifier) + '.zip'
        if os.path.isfile(file) and generate_sha256(file) == game_infos['games'][identifier]['sha256']:
            print('skip {}'.format(identifier))
        else:
            downloaded.append(identifier)
            task = executor.submit(download, identifier, url, file)
            all_task.append(task)

    wait(all_task)
    return downloaded

def files_sha256():
    """
    print existing game archives' sha256

    :return: a dict of sha256 string
    """
    result = dict()
    for identifier in game_infos_ordered['games'].keys():
        file = os.path.normcase(os.path.join(DESTINATION, identifier + '.zip'))
        if os.path.isfile(file):
            result[identifier] = generate_sha256(file)
    return result


def update_sha256():
    """
    update sha256 to the json

    :return: the updated json
    """
    sha256_dict = files_sha256()
    for identifier, sha256 in sha256_dict.items():
        game_infos_ordered['games'][identifier]['sha256'] = sha256
    update_json(game_infos_ordered)
    return


if __name__ == '__main__':
    main()
