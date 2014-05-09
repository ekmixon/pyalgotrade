# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import urllib
import urllib2
import datetime
import os
from pyalgotrade import bar
from pyalgotrade.barfeed import quandlfeed

from pyalgotrade.utils import dt
import pyalgotrade.logger


# http://www.quandl.com/help/api

def download_csv(sourceCode, tableCode, begin, end, frequency, authToken):
    params = {
        "trim_start": begin.strftime("%Y-%m-%d"),
        "trim_end": end.strftime("%Y-%m-%d"),
        "collapse": frequency
    }
    if authToken is not None:
        params["auth_token"] = authToken

    url = "http://www.quandl.com/api/v1/datasets/%s/%s.csv" % (sourceCode, tableCode)
    url = "%s?%s" % (url, urllib.urlencode(params))

    f = urllib2.urlopen(url)
    if f.headers['Content-Type'] != 'text/csv':
        raise Exception("Failed to download data: %s" % f.getcode())
    buff = f.read()

    # Remove the BOM
    while not buff[0].isalnum():
        buff = buff[1:]

    return buff

def download_daily_bars(sourceCode, tableCode, year, csvFile, authToken=None):
    """Download daily bars from Quandl for a given year.

    :param sourceCode: The dataset's source code.
    :type sourceCode: string.
    :param tableCode: The dataset's table code.
    :type tableCode: string.
    :param year: The year.
    :type year: int.
    :param csvFile: The path to the CSV file to write.
    :type csvFile: string.
    :param authToken: Optional. You will need an authentication token unless you are doing less than 50 calls per day.
    :type authToken: string.
    """

    bars = download_csv(sourceCode, tableCode, datetime.date(year, 1, 1), datetime.date(year, 12, 31), "daily", authToken)
    f = open(csvFile, "w")
    f.write(bars)
    f.close()


def download_weekly_bars(sourceCode, tableCode, year, csvFile, authToken=None):
    """Download weekly bars from Quandl for a given year.

    :param sourceCode: The dataset's source code.
    :type sourceCode: string.
    :param tableCode: The dataset's table code.
    :type tableCode: string.
    :param year: The year.
    :type year: int.
    :param csvFile: The path to the CSV file to write.
    :type csvFile: string.
    :param authToken: Optional. You will need an authentication token unless you are doing less than 50 calls per day.
    :type authToken: string.
    """

    begin = dt.get_first_monday(year) - datetime.timedelta(days=1) # Start on a sunday
    end = dt.get_last_monday(year)  - datetime.timedelta(days=1) # Start on a sunday
    bars = download_csv(sourceCode, tableCode, begin, end, "weekly", authToken)
    f = open(csvFile, "w")
    f.write(bars)
    f.close()


def build_feed(sourceCode, tableCodes, fromYear, toYear, storage, frequency=bar.Frequency.DAY, timezone=None, skipErrors=False, noAdjClose=False, authToken=None):
    logger = pyalgotrade.logger.getLogger("quandl")
    ret = quandlfeed.Feed(frequency, timezone)
    if noAdjClose:
        ret.setNoAdjClose()

    if not os.path.exists(storage):
        logger.info("Creating %s directory" % (storage))
        os.mkdir(storage)

    for year in range(fromYear, toYear+1):
        for tableCode in tableCodes:
            fileName = os.path.join(storage, "%s-%s-%d-quandl.csv" % (sourceCode, tableCode, year))
            if not os.path.exists(fileName):
                logger.info("Downloading %s %d to %s" % (tableCode, year, fileName))
                try:
                    if frequency == bar.Frequency.DAY:
                        download_daily_bars(sourceCode, tableCode, year, fileName, authToken)
                    elif frequency == bar.Frequency.WEEK:
                        download_weekly_bars(sourceCode, tableCode, year, fileName, authToken)
                    else:
                        raise Exception("Invalid frequency")
                except Exception, e:
                    if skipErrors:
                        logger.error(str(e))
                        continue
                    else:
                        raise e
            ret.addBarsFromCSV(tableCode, fileName)
    return ret