import pandas as pd
import json
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.distance import jensenshannon
from datetime import datetime, timedelta
import os
from glob import glob

###################### Real World Data ##########################

def checkin_time_duration():
    # Load data into a DataFrame
    df = pd.read_csv('TKY_filtered_traj.csv', parse_dates=['utcTimestamp'])

    # Sort the DataFrame by userId and utcTimestamp
    df = df.sort_values(by=['userId', 'utcTimestamp'])

    # Create a new DataFrame to hold results
    results = []

    # Iterate through each user's check-ins
    for user_id, group in df.groupby('userId'):
        # Iterate through successive rows in the group
        for i in range(len(group) - 1):
            current = group.iloc[i]
            next_checkin = group.iloc[i + 1]
            
            # Check if both check-ins are on the same day
            if current['utcTimestamp'].date() == next_checkin['utcTimestamp'].date():
                # Calculate the duration in seconds
                duration = (next_checkin['utcTimestamp'] - current['utcTimestamp']).total_seconds() / 60
                results.append({
                    'userId': current['userId'],
                    'venueId': current['venueId'],
                    'venueCategory': current['venueCategory'],
                    'duration_mins': duration,
                    'date': current['utcTimestamp'].date(),
                    'latitude': current['latitude'],
                    'longitude': current['longitude'],
                    'start': current['utcTimestamp'],
                    'end': next_checkin['utcTimestamp'],
                })

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Save results to CSV
    results_df.to_csv('checkin_durations.csv', index=False)

def plot_time_duration():
    # Load the calculated durations from the CSV file
    durations_df = pd.read_csv('checkin_durations.csv')

    # Extract the 'duration_minutes' column
    durations = durations_df['duration_mins']

    # Plot the distribution
    plt.figure(figsize=(10, 6))
    plt.hist(durations, bins=5, color='skyblue', edgecolor='black')
    plt.title('Distribution of Time Durations Between Successive Check-ins')
    plt.xlabel('Duration (minutes)')
    plt.ylabel('Frequency')
    plt.show()

def d(point1, point2):
    return np.sqrt(np.sum((np.array(point1) - np.array(point2)) ** 2))

def checkin_dist_duration():
    # Load data into a DataFrame
    df = pd.read_csv('Processed Data/TKY_filtered_traj.csv', parse_dates=['utcTimestamp'])

    # Sort the DataFrame by userId and utcTimestamp
    df = df.sort_values(by=['userId', 'utcTimestamp'])

    # Create a new DataFrame to hold results
    results = []

    # Iterate through each user's check-ins
    for user_id, group in df.groupby('userId'):
        # Iterate through successive rows in the group
        for i in range(len(group) - 1):
            current = group.iloc[i]
            next_checkin = group.iloc[i + 1]

            if current['utcTimestamp'].date() == next_checkin['utcTimestamp'].date():
                point1 = (current['latitude'], current['longitude'])
                point2 = (next_checkin['latitude'], next_checkin['longitude'])
                distance = d(point1, point2)
                
                # Append results
                results.append({
                    'userId': current['userId'],
                    'venueId1': current['venueId'],
                    'venueId2': next_checkin['venueId'],
                    'distance': distance,
                    'date': current['utcTimestamp'].date()
                })

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Save results to CSV
    results_df.to_csv('Processed Data/checkin_distance.csv', index=False)

def plot_dist_duration():
    # Load the calculated durations from the CSV file
    dist_df = pd.read_csv('checkin_distance.csv')

    # Extract the 'duration_minutes' column
    dist = dist_df['distance']

    # Plot the distribution
    plt.figure(figsize=(10, 6))
    plt.hist(dist, bins=200, color='skyblue', edgecolor='black')
    plt.title('Distribution of Distance Between Successive Check-ins')
    plt.xlabel('Distance')
    plt.ylabel('Frequency')
    plt.show()



#################################################################

def parse_time(time_str):
    """Convert time in 'HH:MM' format to a datetime object for easy calculations."""
    return datetime.strptime(time_str, "%H:%M")

def get_time_interval(timestamp):
    time_obj = datetime.strptime(timestamp, '%H:%M').time()
    interval = (time_obj.hour * 60 + time_obj.minute) // 10
    return int(interval)

def calculate_durations(data):
    """Calculate duration between successive activities in minutes."""
    durations = []
    for i in range(1, len(data)):
        prev_act = data[i - 1]
        curr_act = data[i]
        
        if (prev_act[0] == 'sleep'):
            continue

        # Get end time of the previous activity and start time of the current activity
        prev_end_time = parse_time(prev_act[2][0])
        current_start_time = parse_time(curr_act[2][0])

        # If the activities occur on the same day
        if prev_end_time <= current_start_time:
            # Calculate the duration in minutes
            duration = (current_start_time - prev_end_time).total_seconds() / 60
            durations.append(duration)
        else:
            print("ERROR")

    return durations

def calculate_distance(data):
    """Calculate distance between successive activities in minutes."""
    distance = []
    for i in range(1, len(data)):
        prev_act = data[i - 1]
        curr_act = data[i]
        
        # if (prev_act[0] == 'sleep'):
        #     continue
        
        distance.append(d(prev_act[4], curr_act[4]))

    return distance

def calculate_DARD(data):
    # for m in data:
    #     m[2] = data['timestamp'].apply(get_time_interval)

    #     # Step 2: Generate (t, c) tuples
    #     tuples = list(zip(data['time_interval'], data['activity_category']))

    #     # Step 3: Create a 2D histogram
    #     # Determine unique intervals and categories
    #     time_bins = np.arange(0, 145)  # Intervals from 0 to 144
    #     categories = data['activity_category'].unique()
    #     category_map = {cat: i for i, cat in enumerate(categories)}

    #     # Initialize the histogram with zeros
    #     histogram = np.zeros((len(time_bins), len(categories)))

    #     # Populate the histogram
    #     for t, c in tuples:
    #         category_idx = category_map[c]
    #         histogram[t, category_idx] += 1

    # # Step 4: Visualize the histogram
    # plt.figure(figsize=(12, 6))
    # plt.imshow(histogram.T, aspect='auto', cmap='hot', interpolation='nearest')
    # plt.colorbar(label='Activity Frequency')
    # plt.xlabel('Time Interval (10-min segments)')
    # plt.ylabel('Activity Category')
    # plt.xticks(ticks=np.arange(0, 145, 24), labels=[f'{int(x/6):02d}:00' for x in np.arange(0, 145, 24)])
    # plt.yticks(ticks=np.arange(len(categories)), labels=categories)
    # plt.title('Daily Activity Routine Distribution (DARD)')
    # plt.show()
    return

def calculate_STVD(data, bin_size=10):
    """
    Generates the Spatial-Temporal Visits Distribution (STVD) as a histogram.
    
    Parameters:
        data (list of lists): Each sublist should be structured as
                              [activity_type, location, [start_time, end_time], venue_id, [latitude, longitude]]
        bin_size (int): Size of each time interval in minutes (default is 10).
    
    Returns:
        None. Displays a heatmap of the STVD.
    """
    # Define time intervals and grid for spatial distribution
    time_bins = np.arange(0, 1440 // bin_size)  # Total bins in a day (e.g., 0 to 144 for 10-minute intervals)
    latitudes = [entry[4][0] for entry in data]
    longitudes = [entry[4][1] for entry in data]
    
    # Set up latitude and longitude ranges for histogram
    lat_range = np.linspace(min(latitudes), max(latitudes), 50)  # 50 bins for latitude
    lon_range = np.linspace(min(longitudes), max(longitudes), 50)  # 50 bins for longitude
    
    # Initialize histogram matrix
    histogram = np.zeros((len(time_bins), len(lat_range) - 1, len(lon_range) - 1))
    
    # Process each entry in the data
    for entry in data:
        _, _, time_range, _, coordinates = entry
        latitude, longitude = coordinates
        start_time, end_time = time_range
        start_interval = get_time_interval(start_time)
        end_interval = get_time_interval(end_time)
        
        # Fill histogram between start and end intervals for each latitude and longitude bin
        lat_idx = np.digitize(latitude, lat_range) - 1
        lon_idx = np.digitize(longitude, lon_range) - 1
        
        # for t in range(start_interval, end_interval + 1):
        #     if 0 <= lat_idx < len(lat_range) - 1 and 0 <= lon_idx < len(lon_range) - 1:
        #         histogram[t, lat_idx, lon_idx] += 1
        if 0 <= lat_idx < len(lat_range) - 1 and 0 <= lon_idx < len(lon_range) - 1:
            histogram[lat_idx, lon_idx] += (end_interval - start_interval + 1)  # Count all intervals between start and end

    return histogram, lat_range, lon_range

def process_json_files(path, metrics='SI'):
    """Load JSON data from each file, calculate durations, and save to output JSON file."""
    res = []  # Dictionary to store durations for each file

    files = glob(os.path.join(path, "*.json"))

    stvd = None

    for file_path in files:
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        if metrics == 'SI':
            # Calculate durations for the current file
            durations = calculate_durations(data)
            
            # Store the durations using the filename as the key
            res.append(durations)
        elif metrics == 'SD':
            res.append(calculate_distance(data))
        else:
            histogram, lat_range, lon_range = calculate_STVD(data)
            
            if stvd is None:
                stvd = histogram
            else:
                stvd += histogram


    if metrics == 'SI':
        # Save all durations to the output JSON file
        with open('generated_durations.json', 'w') as out_file:
            json.dump(sum(res, []), out_file, indent=4)
    elif metrics == 'SD':
        # Save all durations to the output JSON file
        with open('generated_distance.json', 'w') as out_file:
            json.dump(sum(res, []), out_file, indent=4)
    else:
        aggregated_stvd = stvd.sum(axis=0)
        print("Min value in stvd_aggregated:", np.min(aggregated_stvd))
        print("Max value in stvd_aggregated:", np.max(aggregated_stvd))
        # Plot combined histogram
        plt.figure(figsize=(10, 6))
        plt.imshow(aggregated_stvd, aspect='auto', cmap='hot', vmin=0, vmax=2000, extent=[lon_range[0], lon_range[-1], lat_range[0], lat_range[-1]])
        plt.colorbar(label='Visit Frequency')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title('Aggregated Spatial-Temporal Visits Distribution (STVD) Across Multiple Files')
        plt.show()

def distribution(data, bins=5):
    hist, _ = np.histogram(data, bins=bins, density=True)  # Normalize histogram to create PDF
    distribution = hist / hist.sum()  # Normalize to ensure sum of probabilities = 1
    return distribution

def jsd(expected, ref):
    # Calculate the JSD using jensenshannon()
    jsd = jensenshannon(expected, ref)
    print(f"Jensen-Shannon Divergence: {jsd:.4f}")
    return jsd

def jsd_step_dist():
    df = pd.read_csv('checkin_distance.csv')

    # Extract and normalize distances for JSD calculation
    dist = df['distance'].values
    normalized_dist = distribution(dist)

    process_json_files('../res/phy', 'SD')
    with open('generated_distance.json', 'r') as f:
        data = json.load(f)

    normalized_data = distribution(data)

    jsd_SD = jsd(normalized_dist, normalized_data)

    plt.figure(figsize=(10, 6))
    plt.hist(data, bins=150, color='skyblue', edgecolor='black')
    plt.title('Distribution of Step Distance Between Successive Activities (Physical Model for 5 days)')
    plt.xlabel('Duration (minutes)')
    plt.ylabel('Frequency')
    plt.show()

    return jsd_SD

def jsd_step_time():
    df = pd.read_csv('checkin_durations.csv')

    # Extract and normalize distances for JSD calculation
    duration = df['duration_mins'].values
    normalized_duration = distribution(duration)

    process_json_files('../res/phy')
    with open('generated_durations.json', 'r') as f:
        data = json.load(f)

    # ref = np.tile(data, int(np.ceil(len(normalized_duration) / len(data))))[:len(normalized_duration)]
    normalized_data = distribution(data)

    jsd_SI = jsd(normalized_duration, normalized_data)

    plt.figure(figsize=(10, 6))
    plt.hist(data, bins=150, color='skyblue', edgecolor='black')
    plt.title('Distribution of Time Durations Between Successive Activities (Physical Model for 5 days)')
    plt.xlabel('Duration (minutes)')
    plt.ylabel('Frequency')
    plt.show()

    return jsd_SI


routine_path = '../res/phy'
process_json_files(routine_path, 'SD')

# checkin_time_duration()
# plot_time_duration()

# checkin_dist_duration()
# plot_dist_duration()

jsd_step_dist()