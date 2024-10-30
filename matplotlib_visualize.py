import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
import geopandas as gpd


# Provided data
activities_dict = {
    "1": {
        "01-07-2024": [["sports and exercise", "Gym", ["19:21", "20:02"], "Fitness First Randwick", (-33.918, 151.2412)], ["eat breakfast", "home", ["07:24", "08:00"]], ["go to work", "university", ["09:00", "12:00"], "The University of New South Wales", (-33.9173, 151.2313)]],
        "02-07-2024": [["go to sleep", "home", ["00:00", "07:00"]], ["jogging", "gym", ["08:30", "09:30"], "Plus Fitness 24/7 Kensington", (-33.9181, 151.228)]],
        "03-07-2024": [["go to sleep", "home", ["00:00", "06:45"]], ["eat breakfast", "home", ["07:15", "07:45"]], ["office work", "university", ["08:30", "12:00"], "The University of New South Wales", (-33.9173, 151.2313)]],
        "04-07-2024": [["go to sleep", "home", ["00:00", "06:30"]], ["emails", "home", ["08:00", "09:00"]], ["client call", "home", ["11:30", "12:30"]]],
        "05-07-2024": [["go to sleep", "home", ["00:00", "07:15"]], ["marketing research", "university", ["09:00", "11:00"], "The University of New South Wales", (-33.9173, 151.2313)], ["brainstorming session", "university", ["14:00", "16:00"], "The University of New South Wales", (-33.9173, 151.2313)]],
        "06-07-2024": [["go to sleep", "home", ["00:00", "07:00"]], ["gardening", "home", ["14:00", "16:00"]], ["dinner", "restaurant", ["18:00", "19:00"], "Tropical Green (Pho House)", (-33.9173, 151.2356)]],
        "07-07-2024": [["go to sleep", "home", ["00:00", "06:45"]], ["eat breakfast", "home", ["07:15", "07:45"]], ["relaxing", "home", ["08:00", "09:00"]], ["watch movie", "cinemas", ["10:00", "12:00"]]]
    },
    "2": {
        "01-07-2024": [["sleep", "home", ["23:00", "06:00"]], ["exercise", "gym", ["06:30", "07:30"], "Snap Fitness Randwick", (-33.9175, 151.2415)]],
        "02-07-2024": [["sleep", "home", ["23:00", "06:00"]], ["eat breakfast", "cafe", ["08:00", "08:30"], "Sharetea", (-33.9174, 151.233)]],
        "03-07-2024": [["sleep", "home", ["23:00", "06:00"]], ["online meeting", "home", ["14:00", "15:00"]]]
    },
    "3": {
        "01-07-2024": [["sleep", "home", ["22:00", "06:00"]], ["morning run", "park", ["06:30", "07:00"], "Queens Park", (-33.907, 151.2428)]],
        "02-07-2024": [
    ["eat", "Home", ["0:00", "0:30"], "Home", [-33.912760385171445, 151.23575047362291]],
    ["leisure activities", "Park", ["0:30", "01:37"], "Fred Hollows Reserve", [-33.9104, 151.2454]],
    ["shopping", "Grocery", ["01:37", "02:42"], "Harris Farm Markets", [-33.9174, 151.2418]],
    ["medical treatment", "Clinic", ["02:42", "03:57"], "Randwick Medical", [-33.9167, 151.2418]],
    ["leisure activities", "Home", ["03:57", "04:22"], "Home", [-33.912760385171445, 151.23575047362291]],
    ["leisure activities", "Home", ["04:22", "06:00"], "Home", [-33.912760385171445, 151.23575047362291]],
    ["eat", "Cafe", ["06:30", "07:10"], "Caffe Brioso", [-33.9173, 151.235]],
    ["leisure activities", "Home", ["07:10", "08:30"], "Home", [-33.912760385171445, 151.23575047362291]],
    ["leisure activities", "Home", ["08:30", "10:15"], "Home", [-33.912760385171445, 151.23575047362291]],
    ["leisure activities", "Home", ["10:15", "11:45"], "Home", [-33.912760385171445, 151.23575047362291]],
    ["leisure activities", "Home", ["11:45", "13:15"], "Home", [-33.912760385171445, 151.23575047362291]],
    ["leisure activities", "Park", ["13:20", "14:50"], "Queens Park", [-33.907, 151.2428]],
    ["leisure activities", "Home", ["14:50", "16:15"], "Home", [-33.912760385171445, 151.23575047362291]],
    ["eat", "Home", ["16:15", "17:00"], "Home", [-33.912760385171445, 151.23575047362291]],
    ["leisure activities", "Home", ["17:00", "18:30"], "Home", [-33.912760385171445, 151.23575047362291]],
    ["leisure activities", "Home", ["18:30", "20:00"], "Home", [-33.912760385171445, 151.23575047362291]],
    ["leisure activities", "Home", ["20:00", "22:00"], "Home", [-33.912760385171445, 151.23575047362291]],
    ["sleep", "Home", ["22:00", "23:59"], "Home", [-33.912760385171445, 151.23575047362291]]],
        "03-07-2024": [["sleep", "home", ["22:00", "06:00"]], ["work", "office", ["09:00", "17:00"]]]
    },
    "4": {
        "01-07-2024": [["sleep", "home", ["23:00", "07:00"]], ["yoga", "gym", ["07:30", "08:00"], "UNSW Fitness & Aquatic Centre", (-33.9165, 151.233)]],
        "02-07-2024": [["sleep", "home", ["23:00", "07:00"]], ["eat breakfast", "cafe", ["08:30", "09:00"], "Campus Village Cafe", (-33.9176, 151.2333)]],
        "03-07-2024": [["sleep", "home", ["23:00", "07:00"]], ["work", "university", ["10:00", "16:00"], "The University of New South Wales", (-33.9173, 151.2313)]]
    }
}

# Function to generate a range of floating-point numbers
def frange(start, stop, step):
    while start < stop:
        yield start
        start += step

# Extract coordinates for each persona
persona_coords = {}
for persona_id, dates in activities_dict.items():
    coords = []
    for date, activities in dates.items():
        for activity in activities:
            if len(activity) == 5:
                coords.append(activity[4])
    persona_coords[persona_id] = coords

# Debugging: Print the coordinates
for persona_id, coords in persona_coords.items():
    print(f"Persona {persona_id} coordinates: {coords}")

# Plotting
fig, ax = plt.subplots(figsize=(15, 8))

# Colors for different personas
colors = ['blue', 'green', 'red', 'purple']

# Plot each persona's activities
for idx, (persona_id, coords) in enumerate(persona_coords.items()):
    if len(coords) < 2:
        continue
    gdf = gpd.GeoDataFrame(geometry=[Point(xy[1], xy[0]) for xy in coords])  # Switch x and y
    line = LineString([(xy[1], xy[0]) for xy in coords])  # Switch x and y

    # Plot the points
    gdf.plot(ax=ax, color=colors[idx], marker='o', markersize=15, label=f'Persona {persona_id}')

    # Plot the lines
    gpd.GeoSeries(line).plot(ax=ax, color=colors[idx])

    # Annotate the points with coordinates
    # for point, activity in zip(gdf.geometry, coords):
    #     plt.annotate(f"{(point.y, point.x)}", (point.x, point.y), textcoords="offset points", xytext=(5,5), ha='right', fontsize=8)

# Adjust axis limits dynamically based on the data
all_coords = [(xy[1], xy[0]) for coords in persona_coords.values() for xy in coords]  # Switch x and y
min_lon, min_lat = map(min, zip(*all_coords))
max_lon, max_lat = map(max, zip(*all_coords))

# Add padding around the points
padding = 0.001

plt.xlim(min_lon - padding, max_lon + padding)
plt.ylim(min_lat - padding, max_lat + padding)

# Set y-ticks with a difference of 0.0008
yticks = [round(y, 7) for y in frange(min_lat, max_lat + padding, 0.0008)]
plt.yticks(yticks)

plt.gca().set_aspect('equal', adjustable='box')

plt.title('Persona Movement')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.legend()
plt.grid(True)

# Add ticks for better spacing
plt.xticks(rotation=45)
plt.yticks(rotation=45)

plt.show()