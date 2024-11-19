from flask import Flask, jsonify, render_template
import os
import json

app = Flask(__name__)

ROUTINE_DIR = './res/phy'  # adjust this path as needed

# Route for the homepage
@app.route('/')
def home():
    return render_template('index.html')  # Assuming index.html exists in the templates folder

@app.route('/start_day', methods=['POST'])
def start_day():
    agents_data = {}
    file_count = 0

    # Load personas.json
    with open('./res/personas.json', 'r') as personas_file:
        personas = json.load(personas_file)

    # Get a sorted list of files in the directory
    routine_files = sorted([f for f in os.listdir(ROUTINE_DIR) if f.endswith('.json')])

    for filename in routine_files:
        if file_count < 5:
            file_path = os.path.join(ROUTINE_DIR, filename)
            with open(file_path, 'r') as file:
                data = json.load(file)

                agent_id = str(file_count)

                # Get the corresponding persona
                persona = personas[file_count]

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

                # Include persona data
                agents_data[agent_id] = {
                    "activities": activities,
                    "name": persona.get('name', ''),
                    "age": persona.get('age', ''),
                    "occupation": persona.get('occupation', '')
                }
            file_count += 1

    return jsonify({"agents": agents_data})


if __name__ == '__main__':
    app.run(debug=True)
