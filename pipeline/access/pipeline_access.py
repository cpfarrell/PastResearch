# pipeline_access.py
# Written by:  Alejandro Cantarero
#              alejandro.cantarero@attensitymedia.com
#
# access Attensity pipeline, do historical pull of topic, store as json
#

import datetime
import json
import sys

import ws

from autobahn.websocket import WebSocketClientFactory, WebSocketClientProtocol, connectWS
from twisted.internet import reactor, ssl


def start_reactor():
    reactor.run()

# connect to live stream from topic
def add_ws_stream(url, process_function):
    factory = ws.AttensityFactory(url, msg_function=process_function)
    reactor.connectSSL(factory.host, factory.port, factory, ssl.ClientContextFactory())


# start_date, end date:  dicts with fields "month", "day", "hour", "minute", "year"
#                        hour is specified in 24 hours
#    time should be in EDT (pipeline use to not handle EST correctly)
# time_zone: one of 'edt' or 'est'
def historical_pull(start_date, end_date, account, api_key, topic_id, filename, time_zone='edt'):

    
    url = 'wss://pipeline.attensity.com/account/' + account + '/feed?api_key=' + api_key + '&topic_id[]=' + topic_id

    # need to generalize and make accessible as a tool
    if time_zone.lower() == 'edt':        
        time_shift = datetime.timedelta(hours=4)
    else:
        # I think, should double check
        time_shift = datetime.timedelta(hours=5)

    start_t = datetime.datetime(start_date['year'], start_date['month'], start_date['day'], start_date['hour'], start_date['minute']) + time_shift    
    start_timestamp = (start_t - datetime.datetime(1970, 1, 1)).total_seconds()

    end_t = datetime.datetime(end_date['year'], end_date['month'], end_date['day'], end_date['hour'], end_date['minute']) + time_shift
    end_timestamp = (end_t - datetime.datetime(1970, 1, 1)).total_seconds()

    if start_timestamp > end_timestamp:
        print 'Start Time is after End Time.'
        print 'Exiting...'
        sys.exit(1)

    url += '&starttime=' + str(int(start_timestamp)) + '&endtime=' + str(int(end_timestamp)) + '&stream_mode=historical'

    print url

    f = open(filename, 'w')

    factory = ws.AttensityFactory(url, file_handle=f)
    reactor.connectSSL(factory.host, factory.port, factory, ssl.ClientContextFactory())
