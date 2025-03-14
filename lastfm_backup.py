#!/usr/bin/env python3

import json
import urllib.error
import urllib.request
import os.path
from sys import stdout, stderr
import logging

import backoff

__author__ = 'Alexander Popov'
__version__ = '1.0.0'
__license__ = 'Unlicense'


def get_pages(username, api_key):
    response = urllib.request.urlopen(
           'https://ws.audioscrobbler.com/2.0/'
           '?method=user.getrecenttracks&user={0}&api_key={1}&format=json'
           '&limit=200'.format(username, api_key)).read().decode("utf8")
    pages = int(json.loads(response)['recenttracks']['@attr']['totalPages'])
    return pages

# http://www.last.fm/api/show/user.getRecentTracks
@backoff.on_exception(backoff.expo, urllib.error.HTTPError, max_time=60 * 60) # 1 hr, whatever...
def get_scrobbles(username, api_key, page):
    response = json.loads(urllib.request.urlopen(
               'http://ws.audioscrobbler.com/2.0/'
               '?method=user.getrecenttracks&user={0}&api_key={1}&format=json'
               '&limit=200&page={2}'.format(username, api_key, page)
               ).read().decode("utf8"))['recenttracks']['track']
    return response

if __name__ == '__main__':
    import config
    username = config.USERNAME
    api_key = config.API_KEY
    total = get_pages(username, api_key)
    curPage = 1
    tracks = []
    while curPage <= total:
        stderr.write('\rpage %d/%d %d%%' % (curPage, total, curPage * 100 / total))
        response = get_scrobbles(username, api_key, curPage)

        for track in response:
            try:
                tracks.append({'artist': track['artist']['#text'],
                               'name': track['name'],
                               'album': track['album']['#text'],
                               'date': track['date']['uts']})
            except Exception as e:
                if 'nowplaying' in str(track):
                    # OK, it has no date, whatever
                    pass
                else:
                    logging.error('while processing %s', track)
                    raise e

        curPage += 1

    json.dump(tracks, stdout, indent=4, sort_keys=True, ensure_ascii=False)
