import pandas as pd
import json
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.distance import jensenshannon
from datetime import datetime, timedelta
import os
from glob import glob

act_loc = {
    "meal": ["Restaurant", "Cafe", "Casual Dining"],
    "sleep": ["Hotel"],
    "shopping": ["Grocery", "Other Shopping"],
    "sports and exercise": ["Gym", "Field", "Outdoors"],
    "leisure activities": ["Home", "Art and Performance", "Entertainment", "Pub and Bar", "Outdoors", "Stadium", "Museum", 
        "Library", "Drink and Dessert Shop", "Social Event"],
    "education": ["College and University", "Vocational Training", "Primary and Secondary School", "Preschool"],
    "religious activities": ["Church", "Shrine", "Temple", "Synagogue", "Spiritual Center", "Mosque"],
    "trifles": ["Legal and Financial Service", "Automotive Service", "Health and Beauty Service", "Medical Service", "Other Service"],
}

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
    # durations_df = pd.read_csv('checkin_durations.csv')
    durations_df = pd.read_csv('valid_duration_with_cate_5min.csv')

    # Extract the 'duration_minutes' column
    # durations = durations_df['duration_mins']
    durations = durations_df['duration_minutes']

    # Plot the distribution
    plt.figure(figsize=(10, 6))
    plt.hist(durations, bins=100, color='skyblue', edgecolor='black')
    plt.title('Distribution of Time Durations Between Successive Check-ins')
    plt.xlabel('Duration (minutes)')
    plt.ylabel('Frequency')
    plt.show()

def d(point1, point2):
    return np.sqrt(np.sum((np.array(point1) - np.array(point2)) ** 2))

def normalize_to_4am(timestamp):
    return (timestamp - timedelta(hours=4)).date()

def checkin_dist_duration():
    # Load data into a DataFrame
    # df = pd.read_csv('Processed Data/TKY_filtered_traj.csv', parse_dates=['utcTimestamp'])
    df = pd.read_csv('valid_duration_with_cate_1min.csv', parse_dates=['localTime'])

    # Sort the DataFrame by userId and utcTimestamp
    # df = df.sort_values(by=['userId', 'utcTimestamp'])
    df = df.sort_values(by=['userId', 'localTime'])

    # Create a new DataFrame to hold results
    results = []

    '''
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
                })'''
    
    for user_id, group in df.groupby('userId'):
        # Iterate through successive rows in the group
        for i in range(len(group) - 1):
            current = group.iloc[i]
            next_checkin = group.iloc[i + 1]

            # Normalize timestamps to 4 AM boundary
            current_normalized_date = normalize_to_4am(current['localTime'])
            next_normalized_date = normalize_to_4am(next_checkin['localTime'])

            # Compare normalized dates
            if current_normalized_date == next_normalized_date:
                point1 = (current['latitude'], current['longitude'])
                point2 = (next_checkin['latitude'], next_checkin['longitude'])
                distance = d(point1, point2)
                
                # Append results
                results.append({
                    'userId': current['userId'],
                    'curr_cate': current['category'],
                    'next_cate': next_checkin['category'],
                    'distance': distance,
                    'date': current['localTime'].date()
                })

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Save results to CSV
    results_df.to_csv('checkin_distance.csv', index=False)

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

def checkin_dard():
    data = pd.read_csv('valid_duration_with_cate_1min.csv', parse_dates=['localTime'])
    data['time_interval'] = data['localTime'].dt.hour * 6 + data['localTime'].dt.minute // 10  # 10-minute bins

    # Create the (time_interval, category) tuples
    data['time_category_tuple'] = list(zip(data['time_interval'], data['category']))

    # Count the occurrences of each (time_interval, category) pair
    time_category_counts = data['time_category_tuple'].value_counts().sort_index()

    # Extract the unique time intervals and categories
    time_intervals = sorted(data['time_interval'].unique())
    categories = sorted(data['category'].unique())

    # Create a matrix to represent the histogram
    hist_matrix = np.zeros((len(time_intervals), len(categories)))

    # Populate the histogram matrix with counts
    for (time_interval, category), count in time_category_counts.items():
        time_index = time_intervals.index(time_interval)
        category_index = categories.index(category)
        hist_matrix[time_index, category_index] = count

    # Plot the histogram (heatmap) of the daily activity routine distribution
    plt.figure(figsize=(10, 8))
    plt.imshow(hist_matrix, aspect='auto', cmap='Blues', interpolation='nearest')
    plt.colorbar(label='Frequency')
    plt.xticks(np.arange(len(categories)), categories, rotation=90)
    # plt.yticks(np.arange(len(time_intervals)), time_intervals)
    plt.xlabel('Activity Category')
    plt.ylabel('Time Interval (10-minutes)')
    plt.title('Daily Activity Routine Distribution (DARD)')
    plt.tight_layout()
    plt.show()

def checkin_stvd():
    """
    Evaluate Spatial-Temporal Visits Distribution (STVD) from the given data.
    
    Parameters:
        data (pd.DataFrame): Input data containing 'latitude', 'longitude', and 'localTime' columns.

    Returns:
        None: Displays the histogram of the spatial-temporal visits distribution.
    """

    data = pd.read_csv('valid_duration_with_cate_1min.csv', parse_dates=['localTime'])
    data['time_interval'] = data['localTime'].dt.hour * 6 + data['localTime'].dt.minute // 10  # 10-minute bins

    # Extract tuples (t, latitude, longitude)
    st_tuples = list(zip(data['time_interval'], data['latitude'], data['longitude']))

    # Generate histogram data
    time_bins = range(0, 145)  # 144 intervals (10-minute bins) in a day
    spatial_bins_lat = np.linspace(data['latitude'].min(), data['latitude'].max(), 50)
    spatial_bins_lon = np.linspace(data['longitude'].min(), data['longitude'].max(), 50)

    # Create 2D histogram for spatial-temporal data
    hist, xedges, yedges = np.histogram2d(
        data['latitude'], data['longitude'], bins=[spatial_bins_lat, spatial_bins_lon]
    )

    # Plot histogram (heatmap for spatial distribution)
    plt.figure(figsize=(10, 6))
    plt.title("Spatial Distribution of Visits")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.hist2d(
        data['longitude'], data['latitude'], bins=[spatial_bins_lon, spatial_bins_lat], cmap='Blues', alpha=0.7
    )
    plt.colorbar(label="Visit Frequency")
    plt.show()

    # Time distribution
    plt.figure(figsize=(10, 6))
    plt.title("Temporal Distribution of Visits")
    plt.xlabel("Time Interval (10-min bins)")
    plt.ylabel("Visit Frequency")
    plt.hist(data['time_interval'], bins=time_bins, color="orange", alpha=0.7, rwidth=0.85)
    plt.grid(axis='y', alpha=0.75)
    plt.show()

    # Create 3D histogram using np.histogramdd
    hist, edges = np.histogramdd(
        np.array(st_tuples), bins=[time_bins, spatial_bins_lat, spatial_bins_lon]
    )

    # Get the coordinates for the histogram bars
    xpos, ypos, zpos = np.meshgrid(edges[0][:-1] + 0.25, edges[1][:-1] + 0.25, edges[2][:-1] + 0.25, indexing="ij")
    xpos = xpos.flatten()
    ypos = ypos.flatten()
    zpos = zpos.flatten()

    # Get the height of each bar (corresponding to the count in the histogram)
    dx = np.ones_like(xpos) * 0.5  # bar width for time interval
    dy = np.ones_like(ypos) * (spatial_bins_lat[1] - spatial_bins_lat[0])  # bar width for latitude
    dz = hist.flatten()  # height of the bars (frequency)

    # Create 3D plot
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Plot bars (time, latitude, longitude frequency)
    ax.bar3d(xpos, ypos, zpos, dx, dy, dz, color='b', zsort='average', alpha=0.7)

    # Labels
    ax.set_xlabel('Time Interval (10-min bins)')
    ax.set_ylabel('Latitude')
    ax.set_zlabel('Longitude')
    ax.set_title('3D Histogram: Spatial-Temporal Distribution of Visits')

    # Show plot
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
    """Calculate duration between successive activities in minutes. (for generated data)"""
    durations = []
    for i in range(1, len(data)):
        prev_act = data[i - 1]
        curr_act = data[i]
        
        if (prev_act[0] == 'sleep'):
            continue
        elif (prev_act[0] == 'work'):
            continue

        # Get end time of the previous activity and start time of the current activity
        prev_start_time = parse_time(prev_act[2][0])
        current_start_time = parse_time(curr_act[2][0])

        # If the activities occur on the same day
        if prev_start_time <= current_start_time:
            # Calculate the duration in minutes
            duration = (current_start_time - prev_start_time).total_seconds() / 60
            durations.append(duration)

            # if 115 <= duration <= 130:
            #     print(f"{prev_act[0]} {prev_act[1]}")

            # if duration <= 30:
            #     print(f"{prev_act[0]} {prev_act[1]}")

        else:
            print("ERROR: Prev time: {}, Curr time: {}".format(prev_start_time, current_start_time))
            # print(data)
            # print(data[i - 1])
            # print(data[i])


    return durations

def calculate_distance(data):
    """Calculate distance between successive activities in minutes."""
    distance = []
    for i in range(1, len(data)):
        prev_act = data[i - 1]
        curr_act = data[i]
        
        if (prev_act[0] == 'sleep'):
            continue

        dist = d(prev_act[4], curr_act[4])

        # if dist == 0:
        #     continue

        distance.append(dist)

    return distance

def check_interval_visit(data):
    """Calculate distance between successive activities in minutes."""
    res = []
    for i in range(1, len(data)):
        curr_act = data[i]
        curr_time = datetime.strptime(curr_act[2][0], '%H:%M')
        interval = curr_time.hour * 6 + curr_time.minute // 10
        
        res.append([interval, curr_act[0], curr_act[1], curr_act[-1]])

    return res

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

def calculate_STVD(data):
    res = []
    for i in range(1, len(data)):
        curr_act = data[i]
        
        # if (prev_act[0] == 'sleep'):
        #     continue
        
        # res.append(d(prev_act[4], curr_act[4]))

    return res

def process_json_files(path, metrics='SI'):
    """Load JSON data from each file, calculate durations, and save to output JSON file."""
    res = []  # Dictionary to store durations for each file

    files = glob(os.path.join(path, "*.json"))

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
            res.extend(check_interval_visit(data))

    if metrics == 'SI':
        # Save all durations to the output JSON file
        with open('generated_durations.json', 'w') as out_file:
            json.dump(sum(res, []), out_file, indent=4)
    elif metrics == 'SD':
        # Save all durations to the output JSON file
        with open('generated_distance.json', 'w') as out_file:
            json.dump(sum(res, []), out_file, indent=4)
    else:
        # Save all durations to the output JSON file
        with open('generated_interval_data.json', 'w') as out_file:
            json.dump(res, out_file, indent=4)

def distribution(data, bins=10):
    hist, _ = np.histogram(data, bins=bins, density=True)  # Normalize histogram to create PDF
    distribution = hist / hist.sum()  # Normalize to ensure sum of probabilities = 1
    return distribution

def jsd(expected, ref):
    # Calculate the JSD using jensenshannon()
    jsd = jensenshannon(expected, ref)
    print(f"JSD: {jsd:.4f}")
    return jsd

def jsd_step_dist():
    df = pd.read_csv('checkin_distance.csv')

    # Extract and normalize distances for JSD calculation
    dist = df['distance'].values
    normalized_dist = distribution(dist)

    # process_json_files('../res/phy_cate_1min', 'SD')
    with open('generated_distance.json', 'r') as f:
        data = json.load(f)

    normalized_data = distribution(data)

    jsd_SD = jsd(normalized_dist, normalized_data)

    # plt.figure(figsize=(10, 6))
    # plt.hist(dist, bins=100, color='skyblue', edgecolor='black')
    # plt.title('Distribution of Step Distance Between Successive Activities (Real-world Check-in)')
    # plt.xlabel('Distance')
    # plt.ylabel('Frequency')
    # plt.show()

    # # Plot both distributions on the same histogram
    # plt.figure(figsize=(10, 6))

    # # Plot histogram for the first distribution (CSV data)
    # plt.hist(normalized_dist, bins=150, color='skyblue', alpha=0.5, label='Real-world Check-in')

    # # Plot histogram for the second distribution (JSON data)
    # plt.hist(normalized_data, bins=150, color='orange', alpha=0.5, label='TrajLLM-phy')

    # # Customize plot appearance
    # plt.title('Comparison of Step Distance Distributions: Tokyo Check-in Dataset vs Generated Trajectories')
    # plt.xlabel('Distance')
    # plt.ylabel('Frequency')
    # plt.legend()  # Add legend to identify both distributions
    # plt.show()

    return jsd_SD

def jsd_step_time():
    # df = pd.read_csv('checkin_durations.csv')
    df = pd.read_csv('valid_duration_with_cate_1min.csv')

    # Extract and normalize distances for JSD calculation
    # duration = df['duration_mins'].values
    duration = df['duration_minutes'].values

    normalized_duration = distribution(duration)

    # process_json_files('../res/phy_cate_mix_1min')
    # process_json_files('../res/phy_bestfit_1min')
    # process_json_files('../res/phy_mix_1min')
    # process_json_files('../res/phy_cate_1min')
    # process_json_files('../res/phy_llm_1min')
    # process_json_files('../res/phy_full_1min')
    # process_json_files('../res/phy')
    with open('generated_durations.json', 'r') as f:
        data = json.load(f)

    # ref = np.tile(data, int(np.ceil(len(normalized_duration) / len(data))))[:len(normalized_duration)]
    normalized_data = distribution(data)

    jsd_SI = jsd(normalized_duration, normalized_data)

    # plt.figure(figsize=(10, 6))
    # plt.hist(duration, bins=100, color='skyblue', edgecolor='black')
    # plt.title('Distribution of Time Durations Between Successive Activities (Real-world Check-in)')
    # plt.xlabel('Duration (minutes)')
    # plt.ylabel('Frequency')
    # plt.show()

    # # Plot both distributions on the same histogram
    # plt.figure(figsize=(10, 6))

    # # Plot histogram for the first distribution (CSV data)
    # plt.hist(duration, bins=150, color='skyblue', alpha=0.5, label='Real-world Check-in')

    # # Plot histogram for the second distribution (JSON data)
    # plt.hist(data, bins=150, color='orange', alpha=0.5, label='TrajLLM-phy')

    # # Customize plot appearance
    # plt.title('Comparison of Step Inerval Distributions: Tokyo Check-in Dataset vs Generated Trajectories')
    # plt.xlabel('Duration')
    # plt.ylabel('Frequency')
    # plt.legend()  # Add legend to identify both distributions
    # plt.show()

    return jsd_SI

def jsd_DARD():
    data_expected = pd.read_csv('valid_duration_with_cate_1min.csv', parse_dates=['localTime'])
    data_expected['time_interval'] = data_expected['localTime'].dt.hour * 6 + data_expected['localTime'].dt.minute // 10  # 10-minute bins
    # expected_points = np.array(list(zip(data_expected['time_interval'], data_expected['latitude'], data_expected['longitude'])))
    categories = sorted(data_expected['category'].unique())
    category_map = {cat: idx for idx, cat in enumerate(categories)}
    time_bins = np.arange(0, 145)

    time_intervals_expected = data_expected['time_interval']
    category_indices_expected = data_expected['category'].map(category_map)

    f = open("generated_interval_data.json")
    data_generated = json.load(f)
    data_generated = [entry for entry in data_generated if entry[2] != "Workplace" and entry[1] != 'sleep']
    time_intervals_generated = [entry[0] for entry in data_generated]
    category_indices_generated  = [category_map[entry[2]] for entry in data_generated]

    # Create 2D histograms for expected and generated data
    def create_2d_histogram(time_intervals, category_indices, time_bins, category_map):
        
        hist, _, _ = np.histogram2d(
            time_intervals,
            category_indices,
            bins=[time_bins, np.arange(len(categories) + 1)],
            density=True
        )
        return hist  # Flatten for JSD calculation

    # Create the histograms
    hist_expected = create_2d_histogram(time_intervals_expected, category_indices_expected, time_bins, category_map)
    hist_generated = create_2d_histogram(time_intervals_generated, category_indices_generated, time_bins, category_map)
    
    # Normalize the histograms to ensure they sum to 1
    hist_expected /= hist_expected.sum()
    hist_generated /= hist_generated.sum()
    
    # Compute JSD using scipy's jensenshannon function
    jsd_value = jsd(hist_expected.flatten(), hist_generated.flatten())


    # Plot the histograms
    # fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)
    
    # Expected histogram
    # im1 = axes[0].imshow(hist_expected.T, origin='lower', aspect='auto', cmap='viridis', 
    #                       extent=[time_bins.min(), time_bins.max(), 0, len(categories)])
    # axes[0].set_title('Expected Distribution')
    # axes[0].set_xlabel('Time Interval (10-min bins)')
    # axes[0].set_ylabel('Activity Category')
    # axes[0].set_yticks(range(len(categories)))
    # axes[0].set_yticklabels(categories)
    # fig.colorbar(im1, ax=axes[0], label='Density')

    # # Generated histogram
    # im2 = axes[1].imshow(hist_generated.T, origin='lower', aspect='auto', cmap='viridis', 
    #                       extent=[time_bins.min(), time_bins.max(), 0, len(categories)])
    # axes[1].set_title('Generated Distribution')
    # axes[1].set_xlabel('Time Interval (10-min bins)')
    # axes[1].set_ylabel('Activity Category')
    # axes[1].set_yticks(range(len(categories)))
    # axes[1].set_yticklabels(categories)
    # fig.colorbar(im2, ax=axes[1], label='Density')

    # plt.tight_layout()
    # plt.show()



    return jsd_value

def create_3d_histogram(data, bin):
    """
    Create a 3D histogram for spatial-temporal data.
    
    Parameters:
        data (list): List of data points, where each point is in the format 
                     [time_interval, category, subcategory, [latitude, longitude]].
        time_bins (ndarray): Bins for the time dimension.
        lat_bins (ndarray): Bins for the latitude dimension.
        lon_bins (ndarray): Bins for the longitude dimension.
    
    Returns:
        ndarray: A 3D histogram normalized to sum to 1.
    """
    # Extract time, latitude, and longitude from the data
    time = [point[0] for point in data]
    lat = [point[3][0] for point in data]
    lon = [point[3][1] for point in data]
    
    # Create a 3D histogram
    hist, edges = np.histogramdd((time, lat, lon), bins=bin, density=True)
    
    return hist

def jsd_STVD():
    """
    Evaluate Spatial-Temporal Visits Distribution (STVD) and calculate the JSD between observed and predicted distributions.
    
    Parameters:
        data (pd.DataFrame): Observed data containing 'latitude', 'longitude', 'localTime' columns.
        predicted_data (pd.DataFrame): Predicted data with the same columns as the observed data.
    
    Returns:
        None: Displays the JSD value and histograms.
    """
    data_expected = pd.read_csv('valid_duration_with_cate_1min.csv', parse_dates=['localTime'])
    data_expected['time_interval'] = data_expected['localTime'].dt.hour * 6 + data_expected['localTime'].dt.minute // 10  # 10-minute bins
    expected_points = np.array(list(zip(data_expected['time_interval'], data_expected['latitude'], data_expected['longitude'])))
    
    f = open("generated_interval_data.json")
    data_generated = json.load(f)

    # Create 3D histograms (probability distributions) for spatial-temporal visits
    time_bins = np.arange(0, 145)  # 144 intervals (10-minute bins) in a day
    spatial_bins_lat = np.linspace(data_expected['latitude'].min(), data_expected['latitude'].max(), 11)
    spatial_bins_lon = np.linspace(data_expected['longitude'].min(), data_expected['longitude'].max(), 11)
    
    bins = [time_bins, spatial_bins_lat, spatial_bins_lon]
    
    # Compute 3D histograms for observed and predicted data
    hist_expected, _ = np.histogramdd(expected_points, bins=bins, density=True)
    # hist_expected_normalized = hist_expected / hist_expected.sum()
    hist_generated = create_3d_histogram(data_generated, bins)
    # hist_generated_normalized = hist_generated / hist_generated.sum()
    
    # Calculate JSD for latitude
    jsd_val = jsd(hist_expected.flatten(), hist_generated.flatten())

    '''
    plt.subplot(1, 2, 1)
    plt.imshow(np.sum(hist_expected, axis=2), aspect='auto', origin='lower', extent=[spatial_bins_lat.min(), spatial_bins_lat.max(), time_bins.min(), time_bins.max()])
    plt.colorbar(label='Observed Frequency')
    plt.title('Observed Spatial-Temporal Distribution (Time vs Latitude)')
    plt.xlabel('Latitude')
    plt.ylabel('Time Interval')
    
    plt.subplot(1, 2, 2)
    plt.imshow(np.sum(hist_generated, axis=2), aspect='auto', origin='lower', extent=[spatial_bins_lat.min(), spatial_bins_lat.max(), time_bins.min(), time_bins.max()])
    plt.colorbar(label='Predicted Frequency')
    plt.title('Predicted Spatial-Temporal Distribution (Time vs Latitude)')
    plt.xlabel('Latitude')
    plt.ylabel('Time Interval')
    
    plt.tight_layout()
    plt.show()'''

    # fig = plt.figure(figsize=(12, 6))

    # # 3D Scatter plot for observed data
    # ax1 = fig.add_subplot(121, projection='3d')
    # x, y = np.meshgrid(spatial_bins_lat[:-1], time_bins[:-1])  # Latitude and Time bins
    # x = x.flatten()
    # y = y.flatten()
    # z = hist_expected.flatten()  # Corresponding frequencies

    # ax1.scatter(x, y, z, c=z, cmap='viridis')
    # ax1.set_title('Observed Spatial-Temporal Distribution')
    # ax1.set_xlabel('Latitude')
    # ax1.set_ylabel('Time Interval')
    # ax1.set_zlabel('Frequency')
    # ax1.set_zscale('log')  # Log scale for better visualization of high ranges
    # ax1.view_init(elev=30, azim=45)  # Set viewing angle

    # # 3D Scatter plot for predicted data
    # ax2 = fig.add_subplot(122, projection='3d')
    # z_pred = hist_generated.flatten()

    # ax2.scatter(x, y, z_pred, c=z_pred, cmap='viridis')
    # ax2.set_title('Predicted Spatial-Temporal Distribution')
    # ax2.set_xlabel('Latitude')
    # ax2.set_ylabel('Time Interval')
    # ax2.set_zlabel('Frequency')
    # ax2.set_zscale('log')
    # ax2.view_init(elev=30, azim=45)

    # plt.tight_layout()
    # plt.show()

routine_path = '../res/phy_final'

# checkin_time_duration()
# plot_time_duration()

# checkin_dist_duration()
# plot_dist_duration()

# checkin_dard()
# checkin_stvd()

# process_json_files(routine_path, 'SI')
# jsd_step_time()

# process_json_files(routine_path, 'SD')
# jsd_step_dist()

# process_json_files(routine_path, 'STVD')
# jsd_DARD()
# jsd_STVD()


folders = ['../res/phy_llm_1min', '../res/phy_full_1min', '../res/phy_full_mix_1min', 
           '../res/phy_cate_1min', '../res/phy_cate_mix_1min', '../res/phy_mix_1min', 
           '../res/phy_bestfit_1min', '../res/phy_bestfit_mix_1min', 
           '../res/phy_test', 
           '../res/phy_final', '../res/topk_final', '../res/llm_final'
           ]

# folders = [
#         #    '../res/phy_final', 
#         #    '../res/topk_final', 
#            '../res/llm_final'
#            ]

for f in folders:
    routine_path = f
    print(f'------- {routine_path} -------')

    print("SI", end=" ")
    process_json_files(routine_path, 'SI')
    jsd_step_time()

    print("SD", end=" ")
    process_json_files(routine_path, 'SD')
    jsd_step_dist()

    process_json_files(routine_path, 'STVD')
    print("DARD", end=" ")
    jsd_DARD()
    print("STVD", end=" ")
    jsd_STVD()

    print('\n')

