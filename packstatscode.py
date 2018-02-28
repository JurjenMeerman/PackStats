import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from dateutil.relativedelta import relativedelta
import datetime
import pickle
from fbprophet import Prophet
import pylab
matplotlib.style.use('ggplot')



def basedf(filename): ## this creates a fresh DF based on the freshest download of the .txt
    f = open(filename, encoding="utf8")
    file_read = f.read()
    #'24-01-18, 14:45 - ' %* '\n'
    pieces = [x+'\n' for x in file_read.split('\n')]
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
    
    return df
    

def dfmerge(dfnew):
  

    dfarchive = pd.read_pickle('packarchive')
    
    
    ## the pickle is the achive of the db, in its simplest form (date+time+name+msg)
    #it is equivalent to what comes out of the "basedf" function 
    ##loading a base dataframe that contains the old msgs
    
    dfcombined = dfarchive.append(dfnew) ##append the archive and the new df from the fresh file
    dfcombined = dfcombined.drop_duplicates(subset=['Date','Time','Name','Message'], keep='first') ## drop dups
    
    return dfcombined
    


def wordspotter(df,listofterms): ## provide a dataframe, lists of terms
    finalregex = ''
    for term in listofterms: ##prepare the regex string iteratively by adding the terms and wrapping them
        if term != listofterms[-1]: ## do not include "|" (pipe) in the last bit
            finalregex= finalregex+(r'(?:^|\s)('+term+r'\w+)|') 
        else:
            finalregex= finalregex+(r'(?:^|\s)('+term+r'\w+)')
    booleanchecks = []   
    for i in range(len(df["Message"])):
        mydogshit = re.compile(finalregex,re.IGNORECASE) ##passing the string we prepared above
        booleanchecks.append(bool(mydogshit.findall(df["Message"].iloc[i])))
    ##column name is provided when calling the function
    return booleanchecks ## return a list of bools

def predictive(df_counts):
    df_predict = df_counts[["Date", "count"]]
    df_predict['Date'] = pd.DatetimeIndex(df_predict['Date'])


    df_predict = df_predict.rename(columns={'Date': 'ds',
                            'count': 'y'})



    ax = df_predict.set_index('ds').plot(figsize=(12, 8))
    ax.set_ylabel('Monthly Number of Messages')
    ax.set_xlabel('Date')

    plt.show()

    my_model = Prophet(interval_width=0.50)
    my_model.fit(df_predict)

    future_dates = my_model.make_future_dataframe(periods=30)


    forecast = my_model.predict(future_dates)
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()

    my_model.plot(forecast,
                  uncertainty=True)
    my_model.plot_components(forecast)




dffresh = basedf(r'C:/Python/WhatsApp6.txt') ##running the function to get a fresh df based on new text file
df = dfmerge(dffresh)
df.reset_index()
## now we have a fresh df with merged deduped messages, we proceed with the old stuff
## but before we archive it in a pickle (once overtwriting our normal pickle, once with a date to avoid
##losing data in case of an error)

df.to_pickle('packarchive')
zedate = str(datetime.datetime.now().year)+'-'+str(datetime.datetime.now().month)+'-'+str(datetime.datetime.now().day)
df.to_pickle(zedate+'-'+'packarchive')

 
df['Month'] = df['Date'].apply(lambda x:x.strftime('%Y-%m'))
df['poah'] = wordspotter(df,['Poa','Pooa','Pooo','Piu']) ## passing a df and list to my function above
df['poah'] = df['poah']*1 ## changing bools to 0/1

#### Poah's over time

df_poah = df[['Date',"Name", "poah"]] 
df_poah = df_poah.pivot_table(index='Date',columns='Name',aggfunc=sum)
df_poah.columns = df_poah.columns.droplevel()
df_poah = df_poah.fillna(0)
df_poah["Total"] = df_poah.sum(axis=1)

df_poah["Total"].plot()
df_poah.drop("Total", axis=1).plot()
#Full historic Data plots

df_full = df[['Date', "Time","Name"]] 
df_full["count"] = 1
df_full = pd.DataFrame({'count' : df_full.groupby( [ 'Date', 'Name'] ).size()}).reset_index()
df_full = df_full.pivot_table(index='Date',columns='Name',aggfunc=sum)
df_full.columns = df_full.columns.droplevel()
df_full = df_full.fillna(0)
df_full["Total"] = df_full.sum(axis=1)
df_full["Total"].plot()
df_full.drop("Total", axis=1).plot()


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



df_monthly_poah = df_monthly[['Date',"Name", "poah"]] 
df_monthly_poah = df_monthly_poah.pivot_table(index='Date',columns='Name',aggfunc=sum)
df_monthly_poah.columns = df_monthly_poah.columns.droplevel()
df_monthly_poah = df_monthly_poah.fillna(0)
df_monthly_poah["Total"] = df_monthly_poah.sum(axis=1)

df_monthly_poah["Total"].plot()
df_monthly_poah.drop("Total", axis=1).plot()

#correlation matrix to see who responds to who
corr = df_daily.drop("Total", axis=1).corr()
sns.cubehelix_palette(as_cmap=True, reverse=True)
sns.heatmap(corr, 
            xticklabels=corr.columns.values,
            yticklabels=corr.columns.values,
            cmap="YlGnBu")
plt.yticks(rotation=45) 
plt.xticks(rotation=25) 
plt.show()




## % of msg per month per packer

totalmonthlypacker = pd.pivot_table(df,values=['Message'],index=['Month','Name'],aggfunc='count').reset_index(level=1)
totalmonthly = pd.pivot_table(df,values=['Message'],index=['Month'],aggfunc='count') ## do the same table totaled

totalmonthlypacker = totalmonthlypacker.join(totalmonthly,rsuffix=' total') ## join totals to packer to calc %
totalmonthlypacker['pctg_monthly_msg'] = totalmonthlypacker['Message']/totalmonthlypacker['Message total'] ##calc %


## get a df with msg per month and graph it
permonth = totalmonthlypacker.pivot_table(index='Month',values='Message',aggfunc=np.sum)
ax = permonth.plot(kind='bar',figsize=(10,10), title='Pack msgs per month',width=0.89, legend=False)
vals = ax.get_yticks()
for p in ax.patches:
    ax.annotate(str(p.get_height()), (p.get_x() * 1.01, p.get_height() * 1.005))
pylab.savefig('totalpack.png')
plt.show()


## get 6 dfs per month and per poster and graph them
for packer in list(totalmonthlypacker['Name'].unique()):
    packerdf = totalmonthlypacker.loc[totalmonthlypacker['Name']==packer].pivot_table(index='Month',values='Message',aggfunc=np.sum)
    ax = packerdf.plot(kind='bar',figsize=(10,10), title=packer+' msg per month',width=0.89, legend=False)
    vals = ax.get_yticks()
    for p in ax.patches:
        ax.annotate(str(p.get_height()), (p.get_x() * 1.01, p.get_height() * 1.005))
    pylab.savefig(packer+'.png')
plt.show()


## graph percentage of msg per packer last month
totalmonthlypacker_2 = totalmonthlypacker[["Name","Message", "pctg_monthly_msg"]].tail(6)
ax = totalmonthlypacker_2['pctg_monthly_msg'].plot(kind='bar',figsize=(10,10), title='% of msg',width=0.89)
vals = ax.get_yticks()
ax.set_yticklabels(['{:3.1f}%'.format(x*100) for x in vals])
for p in ax.patches:
    ax.annotate(str(p.get_height()), (p.get_x() * 1.005, p.get_height() * 1.005))
    
plt.show()
        
        

        
#for packer in list(totalmonthlypacker['Name'].unique()):
#    totalmonthlypacker['pctg_monthly_msg'].loc[totalmonthlypacker['Name']==packer].plot(kind='bar',figsize=(12,12), title=packer+' %msg per month',width=0.75)
#    plt.show()

### Predictive Modelling




df_coins = df.copy()
df_coins['coin'] = wordspotter(df,['coin','bitcoin','dennis','ark', 'shitcoin', 'btc', 'ripple', 'xrp','stellar', 'xlm', 'alt' ]) ## passing a df and list to my function above
df_coins['coin'] = df_coins['coin']*1 ## changing bools to 0/1

df_coins = df_coins[['Date',"Name", "coin"]] 
df_coins = df_coins.pivot_table(index='Date',columns='Name',aggfunc=sum)
df_coins.columns = df_coins.columns.droplevel()
df_coins = df_coins.fillna(0)
df_coins["Total"] = df_coins.sum(axis=1)

df_coins["Total"].plot()
df_coins.drop("Total", axis=1).plot()

#Share of POAHS's per month

df_relative = pd.DataFrame(
    {'Total all msg': list(df_full["Total"].values),
     'Total Poah': list(df_poah["Total"].values)
    })


df_relative = df_relative.set_index(df_full.index)
df_relative["Relative"] =  df_relative["Total Poah"]/df_relative["Total all msg"]
df_relative["Relative"].plot()

