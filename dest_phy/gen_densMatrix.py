# %load gen_densMatrix.py
#libaraies
import pandas as pd
import numpy as np
import json
import time
import pickle as pkl
from densmapClass import *



        
###############################
# ----- read data （待改动）----#
###############################
# TODO change path
path = 'POI_data\\'
column_names = ['ID',  'Category','lat', 'lng',]
PoiData = pd.read_csv(path+'TKY_POIs.csv',header=None, names=column_names,skiprows=1)

###############################################
#               tag file 待改动              #
###############################################

# TODO change path
with open(path+'cat_map.json', 'r') as f:
    tag_dict = json.load(f)

tag_dict = eval(str(tag_dict))


###############################################
#                calculate matrix                   #
###############################################
start_time = time.time()
locO = PoiData['lat'].min(), PoiData['lng'].min()
partitionSize = 200
r=1000

## >>>>> to do
# save parameters to file
densmap_instance = {}

tag_list = list(tag_dict)

for tag in list(tag_dict):
    # time1 = time.time()
    df = PoiData[PoiData['Category'].isin(tag_dict[tag])].copy()
    pois = df[['lat','lng']].values
    # time2 = time.time()
    # print(f"time 1-2(取得对应df): {format_time(time2-time1)}")
    try:
        poiIndex = loc2Index(locO,pois,partitionSize)
    except ValueError:
        print(tag,'cannnot find corresponding POI in dataset')
        continue
    df['xIndex'], df['yIndex'] = poiIndex[:, 0], poiIndex[:, 1]
    df.to_csv(path+tag+'_ca_poi.csv')
    # time3 = time.time()
    # print(f"time 2-3(save对应df): {format_time(time3-time2)}")
    densmap = densMap(partitionSize, r, poiIndex,locO)
    densmap_instance[tag] = densmap
    # time4 = time.time()
    # print(f"time 3-4(计算densmap): {format_time(time4-time3)}")

# TODO 存储路径待改动    
with open(path + 'densMaps.pkl', 'wb') as f:
    pkl.dump(densmap_instance, f)

end_time = time.time()
print(f"总运行时间: {format_time(end_time-start_time)}")

