# main.py
# Written by:  Alejandro Cantarero
#              alejandro.cantarero@attensitymedia.com
#
# routine to pull down data
#

import pipeline_access

# example of a historical pull
if __name__ == '__main__':

    # attensitymedia
    account_number = '56'

    # admin API Key
    api_key = 'ed6bbf7'

    # topic id
    topic_id = '2304' # BIG 12

    start_time = {'month': 9, 'day': 10, 'hour': 0, 'minute': 0, 'year': 2013}
    end_time = {'month': 9, 'day': 11, 'hour': 22, 'minute': 0, 'year': 2013}

    filename = 'big12.json'

    pipeline_access.historical_pull(start_time, end_time, account_number, api_key, topic_id, filename)
    pipeline_access.start_reactor()
