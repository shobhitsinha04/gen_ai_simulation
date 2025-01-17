import pickle
import json
from densmapClass import * 
import numpy as np
import pandas as pd

def compute_weight_gravity(user_loc, dens_matrix, poi_set, r=10000):
    # 获取密度矩阵的大小
    xSize, ySize = dens_matrix.shape
    
    # get user index
    user_idx = (np.array(latlng2meter(densmap.locO,user_loc))//densmap.partitionSize).astype(int)
    R = int(-((-r)//densmap.partitionSize))
    center = R//2
    R = center*2 + 1
    
    # if user loc out of range
    def handle_out_of_bounds(user_idx, xSize, ySize):
        x, y = user_idx
        
        # 情况1：完全超出范围 - 使用最近的边界点
        x = np.clip(x, 0, xSize-1)
        y = np.clip(y, 0, ySize-1)
        
        return np.array([x, y])
    
    # if out of range
    original_user_idx = user_idx.copy()
    user_idx = handle_out_of_bounds(user_idx, xSize, ySize)
    
    # 生成势能矩阵
    potential = np.zeros((R,R))
    for i in range(R):
        for j in range(R):
            if i == center and j == center:
                potential[i,j] = 1
            else:
                potential[i,j] = 1/(np.sqrt(abs(i-center)**2+abs(j-center)**2))**1.5
    
    # 处理flow矩阵的边界情况
    def get_valid_slice(idx, center, size):
        start = max(0, idx-center)
        end = min(size, idx+center+1)
        matrix_start = max(0, center-(idx-start))
        matrix_end = min(R, center+(end-idx))
        return slice(start, end), slice(matrix_start, matrix_end)
    
    # 获取有效的切片范围
    x_slice_dens, x_slice_pot = get_valid_slice(user_idx[0], center, xSize)
    y_slice_dens, y_slice_pot = get_valid_slice(user_idx[1], center, ySize)
    
    # 创建填充了0的完整大小流矩阵
    flow = np.zeros((R, R))
    flow[x_slice_pot, y_slice_pot] = densmap.densmap[x_slice_dens, y_slice_dens]
    
    # 应用势能
    flow = flow * potential
    
    # 获取top k网格
    k = 25
    flattened_flow = flow.flatten()
    top_k_indices_flat = np.argpartition(flattened_flow, -k)[-k:]
    top_k_values = flattened_flow[top_k_indices_flat]
    
    top_k_indices_2d = np.unravel_index(top_k_indices_flat, flow.shape)
    
    # 转换索引到原始矩阵
    top_k_indices_2d = list(top_k_indices_2d)
    top_k_indices_2d[0] = np.clip(top_k_indices_2d[0]-center+user_idx[0], 0, xSize-1)
    top_k_indices_2d[1] = np.clip(top_k_indices_2d[1]-center+user_idx[1], 0, ySize-1)
    
    # 筛选候选点
    candidate = poi_set[
        (poi_set['xIndex'].isin(top_k_indices_2d[0])) & 
        (poi_set['yIndex'].isin(top_k_indices_2d[1]))
    ].copy()
    
    # 如果候选集为空，选择最近的几个点
    if len(candidate) == 0:
        # 计算所有POI到用户的距离
        poi_coords = poi_set[['lat', 'lng']].values
        user_coord = np.array(user_loc)
        distances = np.sqrt(np.sum((poi_coords - user_coord)**2, axis=1))
        closest_indices = np.argsort(distances)[:k]
        candidate = poi_set.iloc[closest_indices].copy()
    
    # 重置索引并计算权重
    candidate = candidate.reset_index(drop=True)
    candidate['weight'] = candidate.apply(
        lambda x: calculate_weight(x, densmap.densmap, user_loc), 
        axis=1
    )
    
    # 标准化权重
    if candidate['weight'].sum() > 0:
        candidate['weight'] = candidate['weight']/candidate['weight'].sum()
    else:
        # 如果所有权重都是0，使用均匀分布
        candidate['weight'] = 1.0/len(candidate)
    
    # 添加距离信息供参考
    candidate['distance_to_user'] = candidate.apply(
        lambda x: geodesic(user_loc, (x['lat'], x['lng'])).m, 
        axis=1
    )
    
    return candidate

# 使用示例：
def recommend(user_loc, activity, densmap, model='gravity'):
    tag = activity[1]
    
    if model == 'gravity':
        dens_matrix = densmap[tag]
        poi_set = pd.read_csv(tag+'_ca_poi.csv')
        
        # 添加距离检查
        max_distance = 50000  # 最大推荐距离（米）
        
        candidate = compute_weight_gravity(user_loc, dens_matrix, poi_set)
        # 根据距离过滤
        candidate = candidate[candidate['distance_to_user'] <= max_distance]
        
        if len(candidate) > 0:
            random_row = candidate.sample(n=1, weights='weight')
            result = random_row['ID'].iloc[0], [random_row['lat'].iloc[0], random_row['lng'].iloc[0]]
        else:
            # 如果没有合适的POI，返回None或者自定义的默认值
            result = None, None
            
        return result