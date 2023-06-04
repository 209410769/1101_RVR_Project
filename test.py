import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
from matplotlib.font_manager import FontProperties
import pandas as pd
import requests
import os
import zipfile
import time

from datetime import datetime
current_datetime = datetime.now()
current_date = current_datetime.date()  # 獲取日期部分
current_time = current_datetime.time()  # 獲取時間部分
# 將日期和時間轉換為字符串
date_string = current_date.strftime('%Y-%m-%d')
time_string = current_time.strftime('%H:%M')


parent_folder = "./RVR/" + date_string + " " + time_string+"/RVR"
zip_folder_path = "./RVR/" + date_string + " " + time_string+"/RVR_ZIP"


def real_estate_crawler(year, season):
    if year > 1000:
        year -= 1911
    if not os.path.isdir(zip_folder_path):
        os.makedirs(zip_folder_path)
    # download real estate zip file
    res = requests.get("https://plvr.land.moi.gov.tw//DownloadSeason?season=" +
                       str(year)+"S"+str(season)+"&type=zip&fileName=lvr_landcsv.zip")

    # save content to file
    fname = str(year)+str(season)+'.zip'
    file_path = os.path.join(zip_folder_path, fname)
    open(file_path, 'wb').write(res.content)

    # make additional folder for files to extract
    folder = 'real_estate' + str(year) + str(season)
    next_folder = os.path.join(parent_folder, folder)
    if not os.path.isdir(parent_folder):
        os.makedirs(next_folder)

    # extract files to the folder
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(next_folder)

    time.sleep(10)


for year in range(102, 110):
    for season in range(1, 5):
        print('crawl ', year, 'Q', season)
        real_estate_crawler(year, season)

# @title 縣市選擇
# @param ['台北市','苗栗縣','花蓮縣','台中市','台中縣','台東縣','基隆市','南投縣','澎湖縣','台南市','彰化縣','陽明山','高雄市','雲林縣','金門縣','台北縣','嘉義縣','連江縣','宜蘭縣','台南縣','嘉義市','桃園縣','高雄縣','新竹市','新竹縣','屏東縣']
location = "\u53F0\u4E2D\u5E02"

location_str = """台北市 A 苗栗縣 K 花蓮縣 U
台中市 B 台中縣 L 台東縣 V
基隆市 C 南投縣 M 澎湖縣 X
台南市 D 彰化縣 N 陽明山 Y
高雄市 E 雲林縣 P 金門縣 W
台北縣 F 嘉義縣 Q 連江縣 Z
宜蘭縣 G 台南縣 R 嘉義市 I
桃園縣 H 高雄縣 S 新竹市 O
新竹縣 J 屏東縣 T"""

locToLetter = dict(
    zip(location_str.split()[::2], location_str.lower().split()[1::2]))


# 歷年資料夾
dirs = [d for d in os.listdir() if d[:4] == 'real']

dfs = []

for d in dirs:
    df = pd.read_csv(os.path.join(parent_folder,
                                  d, locToLetter[location] + '_lvr_land_a.csv'), index_col=False)
    df['Q'] = d[-1]
    dfs.append(df.iloc[1:])

df = pd.concat(dfs, sort=True)

# 新增交易年份
df['year'] = pd.to_numeric(df['交易年月日'].str[:-4], errors='coerce') + 1911

# 平方公尺換成坪
df['單價元平方公尺'] = df['單價元平方公尺'].astype(float)
df['單價元坪'] = df['單價元平方公尺'] * 3.30579

# 建物型態
df['建物型態2'] = df['建物型態'].str.split('(').str[0]

# 刪除有備註之交易（多為親友交易、價格不正常之交易）
df = df[df['備註'].isnull()]

# 將index改成年月日
df.index = pd.to_datetime(df['year'].astype(
    str) + df['交易年月日'].str[-4:], errors='coerce')
df.sort_index(inplace=True)
df.head()

# @title 數據分析

plt.rcParams['figure.figsize'] = (10, 6)

# 自定義字體變數
myfont = FontProperties(fname=r'taipei_sans_tc_beta.ttf')
myfont.set_size(15)

prices = {}
for district in set(df['鄉鎮市區']):
    cond = (
        (df['主要用途'] == '住家用')
        & (df['鄉鎮市區'] == district)
        & (df['單價元坪'] < df["單價元坪"].quantile(0.95))
        & (df['單價元坪'] > df["單價元坪"].quantile(0.05))
    )
    groups = df[cond]['year']
    prices[district] = df[cond]['單價元坪'].astype(
        float).groupby(groups).mean().loc[2012:]

price_history = pd.DataFrame(prices)
price_history.plot()
plt.title('各區平均單價', fontproperties=myfont)
plt.legend(prop=myfont)
plt.show()

district_price = df.reset_index()[['鄉鎮市區', '單價元坪']].dropna()
district_price = district_price[district_price['單價元坪'] < 2000000]

fig = px.histogram(district_price, x="單價元坪", color="鄉鎮市區",
                   marginal="rug", nbins=50)  # can be `box`, `violin`)

# Overlay both histograms
fig.update_layout(barmode='overlay')
# Reduce opacity to see both histograms
fig.update_traces(opacity=0.75)
fig.show()

# '店面', '套房', '其他', '農舍', '倉庫', '廠辦', '透天厝', '工廠']
types = ['華廈', '公寓', '住宅大樓', '套房']

building_type_prices = {}
for building_type in types:
    cond = (
        (df['主要用途'] == '住家用')
        & (df['單價元坪'] < df["單價元坪"].quantile(0.8))
        & (df['單價元坪'] > df["單價元坪"].quantile(0.2))
        & (df['建物型態2'] == building_type)
    )
    building_type_prices[building_type] = df[cond]['單價元坪'].groupby(
        df[cond]['year']).mean().loc[2012:]
pd.DataFrame(building_type_prices).plot()
plt.title('不同建物的價格', fontproperties=myfont)
plt.legend(prop=myfont)
plt.show()

# @title 價格與漲跌的相關性
mean_value = price_history.mean()

gain = (price_history.iloc[-1] / price_history.iloc[0])
mean = price_history.mean()

compare = pd.DataFrame({'上漲幅度': gain, '平均價格': mean}).dropna()
corr = (compare.corr().iloc[0, 1])

print('相關性：', corr)
if corr > 0:
    print('意涵：價格越高越保值')
else:
    print('意涵：價格越低越保值')
print()
print('各區平均價格')
mean.sort_values()
