import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from fredapi import Fred
import pandas as pd
import datetime as dt
# import my fred api key, use your own
from fredkey import *
# from yield_curve_fig import Yieldcurve_fig


class UpdateYield(object):

    def __init__(self, ax, yield_dat, inflation, recessions):
        self.yield_dat = yield_dat
        self.inflation = inflation
        self.recessions = recessions
        self.infmax = inflation.max()
        self.infmin = inflation.min()
        self.infmean = inflation.mean()
        self.infrange = self.infmax - self.infmin
        y = self.yield_dat.iloc[0]
        x = [np.log2(6 * 30.), np.log2(365.), np.log2(2 * 365.),
             np.log2(3 * 365.), np.log2(5 * 365.), np.log2(10 * 365.),
             np.log2(20 * 365.), np.log2(30 * 365.)]
        self.line, = ax.plot(x, y, linewidth=4, marker='o')
        self.text = ax.text(np.log2(20 * 365.), 16.5, '', fontsize=16)
        self.ax = ax

        # set up axis format
        xticklabels = ['6-mo', '1-yr', '2-yr', '3-yr', '5-yr', '10-yr',
                       '20-yr', '30-yr']
        self.ax.set_xlabel('Maturity', fontsize=14)
        self.ax.set_ylabel('Annual percentage rate', fontsize=14)
        self.x = x
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['top'].set_visible(False)
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(xticklabels, fontsize=14)
        yticks = np.arange(0, 18, 2)
        self.ax.grid(alpha=0.5)
        self.ax.set_yticks(yticks)
        self.ax.set_yticklabels(yticks, fontsize=14)

    def init(self):
        y = self.yield_dat.iloc[0]
        self.line.set_data(self.x, y)
        self.text.set_text('')
        return self.line, self.text

    def __call__(self, i):
        y = self.yield_dat.iloc[i]
        idat = self.inflation.iloc[i]
        rec = self.recessions.iloc[i]
        t = self.yield_dat.index[i].to_pydatetime()
        month = t.month
        year = t.year
        message = str(month) + r'''/''' + str(year)
        print(message)
        self.line.set_data(self.x, y)
        self.text.set_text(message)
        cr = max(idat - self.infmean, 0)/(self.infmax - self.infmean)
        cb = max(self.infmean - idat, 0)/(self.infmean - self.infmin)
        cg = 1 - cr - cb
        color = (cr, cg, cb)
        self.line.set_color(color)
        fc = 1 - rec
        self.ax.set_facecolor((fc, fc, fc))
        return self.line, self.text

# set your own api_key
fred = Fred(api_key=caras_key)
yields = ['TB6MS', 'GS1', 'GS2', 'GS3', 'GS5', 'GS10', 'GS20', 'GS30']
end_date = dt.datetime.today()
start_date = dt.datetime(1953, 4, 1)
yield_ind_range = pd.date_range('1953-04-01', end_date, freq='MS')
unrate = fred.get_series('UNRATE')
inflation = fred.get_series('CPIAUCSL')
inflation = inflation.pct_change(periods=12)
recessions = fred.get_series('USREC')

yield_dat = pd.DataFrame(index=yield_ind_range, columns=yields)
for y in yields:
    s = fred.get_series(y)
    # need to correctly place values in DataFrame
    mask = yield_dat.index.isin(s.index)
    yield_dat.loc[mask, y] = s.values
inflation = inflation[inflation.index.isin(yield_dat.index)]
recessions = recessions[recessions.index.isin(yield_dat.index)]
runup = np.arange(0, 1, 0.125)
rn = len(runup)
for dind in np.arange(len(recessions)-1):
    if recessions.iloc[dind] > 0:
        if recessions.iloc[dind-1] < 1:
            if(len(recessions.iloc[dind-rn:dind])) > 0:
                recessions.iloc[dind-rn:dind] = runup
            else:
                recessions.iloc[0:4] = runup[rn-4:rn]

# linear interpolation for missing 2-years
for ind in yield_dat.index:
    s = yield_dat.loc[ind, ['GS1', 'GS2', 'GS3']]
    s = s.astype(float)
    s = s.interpolate()
    yield_dat.loc[ind, ['GS1', 'GS2', 'GS3']] = s

fig, ax = plt.subplots(figsize=(12, 6))
yc = UpdateYield(ax, yield_dat, inflation, recessions)
n = len(yield_dat)
anim = FuncAnimation(fig, yc, frames=n, init_func=yc.init,
                     interval=250, blit=False)
plt.show()
#anim.save('yield_movie.mp4')
