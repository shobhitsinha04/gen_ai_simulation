import json
import os

def load_topk(path = None):
    if path == None:
        # get parent directory path
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        path = os.path.join(parent_dir, 'POI_data', 'topk.json')
    else:
        path = os.path.join(path,'topk.json')
    try:
        with open(path, 'r') as f:
            topk_counter= json.load(f)
    except FileNotFoundError:
        topk_counter = {}
    return topk_counter

def save_topk(topk,path = None):
    if path == None:
        # get parent directory path
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        path = os.path.join(parent_dir, 'POI_data', 'topk.json')
    else:
        path = os.path.join(path,'topk.json')
    with open(path, 'w') as f:
        json.dump(topk, f)

def update_topk(topk_counter, daily_activities, bucket_size=5, persona_data=None):
    """
    Update top-k frequent locations using Lossy Counting algorithm
    
    Args:
        topk_counter (dict): Current counter state
        daily_activities (dict): Activities data structured as {persona_id: {date: [activities]}}
        bucket_size (int): Size of the bucket (⌈1/ε⌉)
        persona_data (dict, optional): Additional persona information for filtering
    
    Returns:
        dict: Updated topk_counter
    """
    for persona_id, dates in daily_activities.items():
        for date, activities in dates.items():
            for activity in activities:
                # Filter conditions
                is_basic_location = activity[1] in ['Home', 'Workplace']
                is_student_education = (persona_data and 
                                     persona_id in persona_data and 
                                     activity[0] == 'education' and 
                                     persona_data[persona_id].get("occupation") == 'student')
                
                if not is_basic_location and not is_student_education:
                    # Initialize counter structures if needed
                    if persona_id not in topk_counter:
                        topk_counter[persona_id] = {}
                    
                    activity_type = activity[1]
                    location_id = activity[4]
                    
                    if activity_type not in topk_counter[persona_id]:
                        # Initialize new location type with bucket counter
                        # [-1] key stores [current_bucket_number, elements_in_current_bucket]
                        topk_counter[persona_id][activity_type] = {-1: [1, 0]}
                    
                    if location_id not in topk_counter[persona_id][activity_type]:
                        # Add new location with [count, delta]
                        current_bucket = topk_counter[persona_id][activity_type][-1][0]
                        topk_counter[persona_id][activity_type][location_id] = [1, current_bucket - 1]
                    else:
                        # Increment existing location counter
                        topk_counter[persona_id][activity_type][location_id][0] += 1
                    
                    # Update bucket counter
                    topk_counter[persona_id][activity_type][-1][1] += 1
                    
                    # Check if current bucket is full
                    if topk_counter[persona_id][activity_type][-1][1] == bucket_size:
                        # Reset bucket counter and start cleaning
                        topk_counter[persona_id][activity_type][-1][1] = 0
                        current_bucket = topk_counter[persona_id][activity_type][-1][0]
                        
                        # Identify items to remove
                        items_to_remove = [
                            key for key, value in topk_counter[persona_id][activity_type].items()
                            if key != -1 and value[0] + value[1] <= current_bucket
                        ]
                        
                        # Remove items
                        for key in items_to_remove:
                            del topk_counter[persona_id][activity_type][key]
                        
                        # Increment bucket number
                        topk_counter[persona_id][activity_type][-1][0] += 1
    
    return topk_counter