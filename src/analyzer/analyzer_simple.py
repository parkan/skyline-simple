import sys
from os.path import dirname, abspath, isdir
sys.path.insert(0, dirname(dirname(abspath(__file__))))

import logging
from time import time, sleep
from collections import defaultdict
from multiprocessing import Process, Manager, Lock
from os import path, kill, getpid, system
from math import ceil
import traceback
import operator
import settings
from pprint import pprint

import simplejson
import urllib2

from algorithms import run_selected_algorithm
from algorithm_exceptions import *

logger = logging.getLogger("AnalyzerLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s :: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler = logging.FileHandler('analyzer.log')
handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.addHandler(stream_handler)

url = "https://www.hostedgraphite.com/da236f21/c913974c-38df-4afd-a543-7edd9fe531e8/graphite/render/?from=04%3A25_20130714&until=04%3A22_20130716&format=json&target=stats.hypem.track_fail.SC"
req = urllib2.Request(url);
opener = urllib2.build_opener()
j = simplejson.load(opener.open(req))

timeseries = j[0]["datapoints"]
clean_timeseries = [ t for t in timeseries if type(t[0]) is float ]

exceptions = defaultdict(int)

start = 0
end = 288
while end < len(clean_timeseries):
    s = clean_timeseries[start:end]
    try:
        anomalous, ensemble, datapoint = run_selected_algorithm(clean_timeseries)

        # If it's anomalous, add it to list
        if anomalous:
            metric = [datapoint, metric_name]
            logger.debug('anomalous at ' . datapoint)
            logger.debug(metric)
            logger.debug(ensemble)
            #self.anomalous_metrics.append(metric)

            # Get the anomaly breakdown - who returned True?
            for index, value in enumerate(ensemble):
                if value:
                    algorithm = settings.ALGORITHMS[index]
                    anomaly_breakdown[algorithm] += 1

    # It could have been deleted by the Roomba
    except AttributeError:
        exceptions['DeletedByRoomba'] += 1
    except TooShort:
        exceptions['TooShort'] += 1
    except Stale:
        exceptions['Stale'] += 1
    except Incomplete:
        exceptions['Incomplete'] += 1
    except Boring:
        exceptions['Boring'] += 1
    except:
        exceptions['Other'] += 1
        logger.debug(traceback.format_exc())
    finally:
        start += 1
