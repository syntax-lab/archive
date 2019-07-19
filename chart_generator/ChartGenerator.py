import matplotlib
import matplotlib.axes
import matplotlib.pyplot as plt
import pylab
import time
import math
import random
import json
import urllib.request
import datetime
import itertools

#rethink logic...done! ~kinda

##random_data = {'A': [1, 2, 5, 2, 6, 1],
##               'B': [2, 5, 1, 10, 2, 4],
##               'C': [4, 3, 3],
##               'D': [2, 1, 7, 9, 1],
##               'E': [1, 9, 9, 1, 5, 5],
##               'F': [7, 7, 5, 1]}

#parser should format data output like:
#dict of (Unique ids as string: [data, ...] as list)
#explanation: each entry in single list represent value at given time quantity(important: look into notice reference!!!)
#notice: all lists should be filled with zeros if no values at this time quantity occurred(if no values at the end of list no action needed)

colors = {} 
MAX_VALUES = 10
    
fig, ax = plt.subplots()
ax.set_facecolor((0.95, 0.95, 0.95, 0.50)) #background color

def randColors():
    threshold = 0.05
    rgb = [*ax.get_facecolor()]
    colors = []
    for c in rgb[:3]:
        color = random.random()
        while(abs(color - c) < threshold):
            color = random.random()
        colors.append(color)
    return colors

def getDataFromUrl(url, fun, **args):
    urlcnt = urllib.request.urlopen(url)
    data = json.loads(urlcnt.read().decode())
    fun(data, **args)

###put url here
url = 'http://api.nbp.pl/api/exchangerates/tables/B/{}/{}/?format=json'

###write your own json parser here
day_rates = {} #check content
dates = [] #check content

def parseJson(data, **args):
    day_rates = args['day_rates']
    dates = args['dates']
    for day in data:
        dates.append(day['effectiveDate']) # assume that effectiveDate is given from each request
        duplicate_guard = set()
        for rate in day['rates']:
            if(rate['code'] not in duplicate_guard):
                duplicate_guard.add(rate['code'])
            else:
                continue
            daily_rate = day_rates.get(rate['code'])
            if(daily_rate == None):
                day_rates.update({rate['code']: [0] * (len(dates) - 1) + [rate['mid']]})
            else:
                daily_rate.extend([0] * (len(dates) - len(daily_rate) - 1) + [rate['mid']])
    #return (dates, day_rates)

def getDataRange(url, start, end, fun, **args):
    start_date = map(int, start.split('-'))
    end_date = map(int, end.split('-'))
    start_date = datetime.datetime.date(datetime.datetime(*start_date))
    end_date = datetime.datetime.date(datetime.datetime(*end_date))
    begin = start_date
    while(True):
        end = begin + min(end_date - begin, datetime.timedelta(93))
        getDataFromUrl(url.format(begin, end), fun, **args)
        begin = end
        if(begin == end_date):
            return
    #return fun(data, **args)
        
print('Collecting data...', end='')

getDataRange(url, '2002-01-02', str(datetime.date.today()), parseJson, day_rates = day_rates, dates = dates)

m_length = max([len(x) for x in day_rates.values() if len(x) > 0]) 

#print(data.items() == m_length) # both must equal

for d in day_rates.values():
    if(len(d) < m_length):
        d.extend([0 for _ in range(m_length - len(d))])

for label in day_rates.keys():
    color = randColors()
    colors.update({label: color})

t = [*day_rates.items()]

print(f'done!({m_length}) objects gathered!')

for i in range(m_length):
    t.sort(key = lambda x: x[1][i]) #imporve this
    values = []
    labels = []
    for label, l in t[-MAX_VALUES:]:
        if(l[i] == 0): continue #check what if 0 in the middle of data
        values.append(l[i])
        labels.append(label)
        
    barlist = ax.barh(labels, values)
    
    ax.set_ylabel('Currency')
    ax.set_xlabel('Value(PLN)')

    ax.set_title('Date: {}'.format(dates[i]))

    for idx, label in enumerate(labels):
        barlist[idx].set_color(colors.get(label))
        x = barlist[idx].get_width()
        y = barlist[idx].get_y() + barlist[idx].get_height() / 2

        plt.annotate('{:.2f}'.format(values[idx]), (x, y), xytext = (0, 0), textcoords='offset points', va='center', ha='right')

    plt.pause(0.01)
    ax.clear()

print('Done.')
