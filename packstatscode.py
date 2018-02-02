import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

from dateutil.relativedelta import relativedelta
from datetime import datetime

matplotlib.style.use('ggplot')


############################################## RegEx for Prep ###########################################
########## Change the path of the filename to your whatsapp textfile and you are good to go##############


filename = r'//solon.prd/files/P/Global/Users/C36116/UserData/Desktop/Project/Packstats/WhatsApp4.txt'
f = open(filename, encoding="utf8")
file_read = f.read()
#'24-01-18, 14:45 - ' %* '\n'
pieces = [x+'\n' for x in file_read.split('\n')]

#messages
messages = []
for i in range(len(pieces)):
    try:
        msg_pat = r'(\d{2}\-\d{2}\-\d{2}\,\ \d{2}\:\d{2}\ \-\ .*?\:\ )(.*?)(\n)'
        pattern = re.compile(msg_pat)
        messages.append(pattern.search(pieces[i])[2])
    except TypeError as e:
        messages.append('')
        

#Dates
date = []
for i in range(len(pieces)):
    try:
        datum_pat = r'\d{2}\-\d{2}\-\d{2}'
        datum_pattern = re.compile(datum_pat)
        date.append(datum_pattern.search(pieces[i])[0])
    except TypeError as e:
        date.append('')

#time     
time = []
for i in range(len(pieces)):
    try:
        tijd_pat = r'\d{2}\:\d{2}'
        tijd_pattern = re.compile(tijd_pat)
        time.append(tijd_pattern.search(pieces[i])[0])
    except TypeError as e:
        time.append('')

#names    
namen = []
for i in range(len(pieces)):
    try:
        naam_pat = r'(\d{2}\:\d{2}\ \-\ )(.*?)(\:\ )'
        naam_pattern = re.compile(naam_pat)
        namen.append(naam_pattern.search(pieces[i]).group(2))
    except Exception as e:
        namen.append('')


df = pd.DataFrame({'Date':date, "Time":time, "Name":namen, "Message":messages})
df = df[['Date', "Time","Name","Message"]]
df = df.replace('', np.nan)
df = df.dropna(axis=0)
############################## Data prep for analytics ##########################################

df['Date'] =  pd.to_datetime(df['Date'], format='%d-%m-%y').dt.date
df['Time'] =  pd.to_datetime(df['Time'], format='%H:%M').dt.time


poah = []
for i in range(len(df["Message"])):
    mydogshit = re.compile(r'(?:^|\s)(Poa\w+)|(?:^|\s)(Pooa\w+)|(?:^|\s)(Pooo\w+)|(?:^|\s)(Piu\w+)',re.IGNORECASE)
    poah.append(bool(mydogshit.findall(df["Message"].iloc[i])))
    
df["poah"] = poah
df["poah"] = df["poah"]*1

#Selecting the latest data month from whatsapp
today_date = df['Date'].max()
one_month_ago = today_date - relativedelta(months=1)
#one_month_ago = one_month_ago.date()

df_monthly = df[(df['Date'] > one_month_ago) & (df['Date'] <= today_date)]

df_counts = df_monthly[['Date', "Time","Name"]] 
df_counts["count"] = 1
df_counts = pd.DataFrame({'count' : df_counts.groupby( [ 'Date', 'Name'] ).size()}).reset_index()

df_daily = df_counts.pivot_table(index='Date',columns='Name',aggfunc=sum)
df_daily.columns = df_daily.columns.droplevel()
df_daily = df_daily.fillna(0)
df_daily["Total"] = df_daily.sum(axis=1)


df_daily["Total"].plot()
df_daily.drop("Total", axis=1).plot()

#correlation matrix to see who responds to who
corr = df_daily.drop("Total", axis=1).corr()
sns.cubehelix_palette(as_cmap=True, reverse=True)
sns.heatmap(corr, 
            xticklabels=corr.columns.values,
            yticklabels=corr.columns.values,
            cmap="YlGnBu")

#### Poah's over time

df_poah = df[['Date',"Name", "poah"]] 
df_poah = df_poah.pivot_table(index='Date',columns='Name',aggfunc=sum)
df_poah.columns = df_poah.columns.droplevel()
df_poah = df_poah.fillna(0)
df_poah["Total"] = df_poah.sum(axis=1)

df_poah.plot()
df_poah.drop("Total", axis=1).plot()
