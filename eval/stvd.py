import numpy as np
import pandas as pd
import datetime
from scipy.spatial.distance import jensenshannon

def time_to_interval(time_str, bin_size=10):
    """Convert time string to an interval (0-144) based on bin size."""
    time_obj = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    total_minutes = time_obj.hour * 60 + time_obj.minute
    return total_minutes // bin_size

def build_stvd(data, bin_size=10):
    """Builds a histogram of Spatial-Temporal Visits Distribution (STVD) from the given data."""
    histogram = np.zeros(144)  # 0-143 for 10-minute intervals in a day
    for entry in data:
        start_time, end_time, latitude, longitude = entry
        start_interval = time_to_interval(start_time, bin_size)
        end_interval = time_to_interval(end_time, bin_size)

        # Increment the histogram for the duration of the visit
        for t in range(start_interval, end_interval + 1):
            histogram[t] += 1  # Count the visit in the corresponding time interval
            
    return histogram

def read_csv_data(file_path):
    """Reads the CSV data and prepares it for STVD calculation."""
    df = pd.read_csv(file_path)
    data = []
    for index, row in df.iterrows():
        data.append([row['start'], row['end'], row['latitude'], row['longitude']])
    return data

def calculate_jsd(stvd1, stvd2):
    """Calculates Jensen-Shannon Divergence between two distributions."""
    # Normalize the histograms
    stvd1_normalized = stvd1 / np.sum(stvd1)
    stvd2_normalized = stvd2 / np.sum(stvd2)
    
    # Calculate JSD
    jsd = jensenshannon(stvd1_normalized, stvd2_normalized)
    return jsd

def analyze_stvd_and_calculate_jsd(stvd_data, csv_file_path):
    """
    Analyze Spatial-Temporal Visits Distribution (STVD) and calculate JSD against CSV data.
    
    Parameters:
        stvd_data (list of lists): Data for STVD where each sublist is
                                    [start_time, end_time, latitude, longitude]
        csv_file_path (str): Path to the CSV file to compare against.
        
    Returns:
        jsd (float): The calculated JSD value between the two distributions.
    """
    # Build the STVD histogram from the provided data
    stvd_hist = build_stvd(stvd_data)

    # Read CSV data and build its STVD histogram
    csv_data = read_csv_data(csv_file_path)
    csv_stvd_hist = build_stvd(csv_data)

    # Calculate JSD
    jsd = calculate_jsd(stvd_hist, csv_stvd_hist)
    
    return jsd

# Example usage:
# Your STVD data (replace this with your actual data)
stvd_data = [
    ["2012-04-08 00:10:48", "2012-04-08 01:18:00", 35.66808763, 139.7673154],
    ["2012-04-08 01:18:00", "2012-04-08 01:18:21", 35.66833822, 139.7667561]
]

csv_file_path = 'path_to_your_file.csv'  # Replace with your actual CSV file path

# Calculate JSD
# jsd_value = analyze_stvd_and_calculat
