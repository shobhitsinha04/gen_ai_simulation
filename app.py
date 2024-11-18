from flask import Flask, jsonify, render_template
import os
import json

app = Flask(__name__)

ROUTINE_DIR = './res/phy'  # adjust this path as needed

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/start_day', methods=['POST'])
def start_day():
    agents_data = {}
    file_count = 0

    # get a sorted list of files in the directory
    routine_files = sorted([f for f in os.listdir(ROUTINE_DIR) if f.endswith('.json')])

    for filename in routine_files:
        if file_count < 5:
            file_path = os.path.join(ROUTINE_DIR, filename)
            with open(file_path, 'r') as file:
                data = json.load(file)

                # sequential agent ID (0, 1, 2, 3, 4)
                agent_id = str(file_count)
                
                activities = []
                for entry in data:
                    activity = {
                        "activityType": entry[0],
                        "locationType": entry[1],
                        "startTime": entry[2][0],
                        "endTime": entry[2][1],
                        "locationId": entry[3],
                        "lat": entry[4][0],
                        "lng": entry[4][1]
                    }
                    activities.append(activity)
                
                agents_data[agent_id] = activities
            file_count += 1

    return jsonify({"agents": agents_data})

if __name__ == '__main__':
    app.run(debug=True)
