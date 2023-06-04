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

# 父資料夾名稱
parent_folder = "./RVR/" + date_string + " " + time_string+"/RVR"
zip_folder_path = "./RVR/" + date_string + " " + time_string+"/RVR_ZIP"


def real_estate_crawler(year, season):
    if year > 1000:
        year -= 1911

    if not os.path.isdir(zip_folder_path):
        os.makedirs(zip_folder_path)

    # 下載不動產 zip 檔案
    res = requests.get("https://plvr.land.moi.gov.tw//DownloadSeason?season=" +
                       str(year) + "S" + str(season) + "&type=zip&fileName=lvr_landcsv.zip")

    # 儲存檔案內容到指定位置
    fname = str(year) + str(season) + '.zip'
    file_path = os.path.join(zip_folder_path, fname)
    open(file_path, 'wb').write(res.content)

    # 建立資料夾用於存放解壓縮檔案
    folder = 'real_estate' + str(year) + str(season)
    next_folder = os.path.join(parent_folder, folder)
    if not os.path.isdir(parent_folder):
        os.makedirs(next_folder)  # 使用 os.makedirs() 建立資料夾

    # 解壓縮檔案到資料夾中
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(next_folder)

    time.sleep(10)


for year in range(102, 110):
    for season in range(1, 5):
        print('crawl ', year, 'Q', season)
        real_estate_crawler(year, season)

# 縣市選擇
location = "\u53F0\u4E2D\u5E02"  # 變數選擇

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

dfs = []

# 遞迴搜索資料夾並讀取符合條件的 CSV 檔案
for root, dirs, files in os.walk(parent_folder):
    for file in files:
        if file.endswith('.csv') and locToLetter[location] in file:
            csv_file = os.path.join(root, file)
            try:
                df = pd.read_csv(csv_file, index_col=False, dtype=str,
                                 encoding='utf-8')
                df['Q'] = os.path.basename(root)[-1]
                dfs.append(df.iloc[1:])
            except pd.errors.ParserError:
                print(f"Error parsing CSV file: {csv_file}")

if dfs:
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
    print(df.head())
else:
    print("No CSV files found.")
