# import gmplot package
import argparse
import re
import json
import sys
import gmplot

def validate_date(date_str: str):
    # Regular expression for validating date format dd-mm-yyyy
    if not re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):
        raise argparse.ArgumentTypeError("Invalid date format. Expected dd-mm-yyyy.")
    return date_str

parser = argparse.ArgumentParser(description='genMotivation')
parser.add_argument('-d', '--date', type=validate_date, help="Date in the format dd-mm-yyyy")
args = parser.parse_args()

if __name__ == '__main__':
    f1 = open("res/personas.json")
    p_count = len(json.load(f1))

    overall_map = gmplot.GoogleMapPlotter(35.681855, 139.766565, 11, apikey='')

    for i in range(p_count):
        submap = gmplot.GoogleMapPlotter(35.681855, 139.766565, 11, apikey='')
        filename = "res/phy/routine_{}_{}.json".format(args.date, i)
        try:
            f = open(filename, 'r')
            routine = json.load(f)
        except FileNotFoundError:
            print("{}: File not found.".format(filename))
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

        submap.scatter(latitude_list, longitude_list, color=['red' if location_list[x] == 'Home' else 'green' if location_list[x] == 'Workplace' else 'blue' if activity_list[x] == 'education' else 'yellow' for x in range(len(location_list))], 
                       size = 40, marker = True, title=name_list, label=[location_list[x][0] if location_list[x] == 'Home' or location_list[x] == 'Workplace' else 'S' if activity_list[x] == 'education' else activity_list[x][0] for x in range(len(activity_list))])
        submap.plot(latitude_list, longitude_list, 'cornflowerblue', edge_width = 2.5)
        submap.draw("plots/mob_{}_{}.html".format(args.date, i))

        if (i != 1):
            # Plot the starting point as a single blue marker
            overall_map.scatter([latitude_list[0]], [longitude_list[0]], color=['#0000FF'], size=500, marker=False, symbol=['x'])

            # Plot the rest of the points in red
            overall_map.scatter(latitude_list[1:], longitude_list[1:], '#FF0000', size=500, marker=False)

            # overall_map.scatter(latitude_list, longitude_list, '#FF0000', size = 500, marker = False)
            overall_map.plot(latitude_list, longitude_list, 'cornflowerblue', edge_width = 2.5)

    overall_map.draw("plots/overall_mob.html")