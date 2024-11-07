import os
import glob
import gmplot
import json
import sys

# Specify the folder path
folder_path = '../res/phy'

# Get a list of all JSON files in the specified folder
json_files = glob.glob(os.path.join(folder_path, '*.json'))

overall_map = gmplot.GoogleMapPlotter(35.681855, 139.766565, 11, apikey='')

for f in json_files:
    try:
        f = open(f, 'r')
        routine = json.load(f)
    except FileNotFoundError:
        print("{}: File not found.".format(f))
        break
    except PermissionError:
        print("Permission denied.")
        break
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
        
    activity_list = [l[0] for l in routine]
    location_list = [l[1] for l in routine]
    name_list = [l[3] for l in routine]
    latitude_list = [l[4][0] for l in routine]
    longitude_list = [l[4][1] for l in routine]

    overall_map.scatter([latitude_list[0]], [longitude_list[0]], color=['#0000FF'], size=500, marker=False, symbol=['x'])

    # Plot the rest of the points in red
    overall_map.scatter(latitude_list[1:], longitude_list[1:], '#FF0000', size=500, marker=False)

    # overall_map.scatter(latitude_list, longitude_list, '#FF0000', size = 500, marker = False)
    # overall_map.plot(latitude_list, longitude_list, 'cornflowerblue', edge_width = 2.5)

    overall_map.draw("plots/overall_mob.html")