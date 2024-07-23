import argparse
import datetime
import re
import json

from utils import llm_generate, gen_person_info
from mem_module_upgraded import MemoryModule

def validate_date(date_str):
    # Regular expression for validating date format dd-mm-yyyy
    if not re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):
        raise argparse.ArgumentTypeError("Invalid date format. Expected dd-mm-yyyy.")
    return date_str

def valid_time(time_str):
    try:
        datetime.datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False

def get_weekday(date_str: str):
    # Parse the date string into a datetime object
    date_obj = datetime.datetime.strptime(date_str, '%d-%m-%Y')
    # Get the weekday name
    weekday = date_obj.strftime('%A')
    return weekday

def check_routine_finished(time):
    return time == "23:59"

def time_exceed(t1, t2):
    format = '%H:%M'
    time1_obj = datetime.datetime.strptime(t1, format).time()
    time2_obj = datetime.datetime.strptime(t2, format).time()
    
    return time1_obj > time2_obj

def time_update(curr_time: str, min: int):
    format = '%H:%M'
    time_obj = datetime.datetime.strptime(curr_time, format)
    new_time = time_obj + datetime.timedelta(minutes=min)
    return new_time.strftime(format)

def gen_next_motivation(context: str, pre_mot, mem, date: str, weekday: str, time: str):
    msg = """Today is {}, {}. Now is {}. You've already done the following activities: {}.
Task: Based on current date and time, your personal information and recent arrangements, please randomly select your next activity from your daily activity dictionary, \
and pick a location from the location list corresponds to the chosen activity. You should also decide the time duration for the selected activity.

Requirements for routine generation:
1. You must consider how your character attributes and personality may affect your activity and location selection.
2. The next activity should start at now, which is {}.
3. You must consider how the date and time may affect your activity and location selection. For example, most people sleep at night, and most people only goes to work during weekdays.

Note: 
1. The format for the time should be in 24-hour format.
2. The routine of a day must start at 0:00 and end at 23:59. \
The routine should not have activities that exceed the time limit, i.e. you should not create activity that starts today and ends anytime tomorrow. \
For example, you should create activity like '["sleep", "Home", ["22:18", "23:59"]]'.
3. When selecting the activity, you must take the frequency of the activity into consideration.
4. You can pick one activity only from your daily activitiy list, and one location for the chosen activity only from the location list of that activity.
Answer format: [activity name, location, [start time, end time]].

5 example outputs:
1. ["sleep", "Home", ["0:00", "7:29"]]
2. ["work", "Workplace", ["13:32", "17:30"]]
3. ["eat", "Cafe", ["11:49", "12:12"]]
4. ["sleep", "Hotel", ["22:25", "23:59"]]
5. ["sports and exercise", "Gym", ["19:21", "20:02"]]

Important: You should always responds required data in json list format, but without any additional introduction, text or explanation.
""". format(date, weekday, time, pre_mot, time)

    res = llm_generate(context, msg)
    return json.loads(res)

parser = argparse.ArgumentParser(description='genMotivation')
# parser.add_argument('-a', action='store_true') # Generate activity list for each persona
parser.add_argument('-d', '--date', type=validate_date, help="Date in the format dd-mm-yyyy")
parser.add_argument('-p', '--exploration') # Include exploration behaviours into the model
# parser.add_argument('--model', default = '...', type=str)
# parser.add_argument('--population', default = 'population.json', type=str)
# parser.add_argument('--mode_choice', default = 'realRatio', type=str)  # realRatio
args = parser.parse_args()

if __name__ == '__main__':
    # TODO: 5. Load mem files into memory
    memory_module = MemoryModule()

    f1 = open("res/personas.json")
    p = json.load(f1)

    weekday = get_weekday(args.date)
    f2 = open("res/activities.json")
    act = json.load(f2)

    for i in range(len(p)):
        cur_mot = []
        time = "0:00"

        # TODO: 2. Weekly/dayly summary memory (weekly + recent 3 days/ all dayly)
        mem = []

        context = gen_person_info(p[i]["name"], p[i]["age"], p[i]["gender"], p[i]["occupation"], p[i]["personality"]["ext"], p[i]["personality"]["agr"], p[i]["personality"]["con"], p[i]["personality"]["neu"], p[i]["personality"]["ope"])
        context += """Your daily activities, their frequencies and possible happening locations is given in your daily activity dictionary. \
Each activity in your daily activity dictionary is given in the format 'activity: [frequency, location list]' as following:
{}.""".format(act[i])
        while (not check_routine_finished(time)):
            # This is the loop that generate one day routine activity by activity (for one person)
            res = gen_next_motivation(context, cur_mot, mem, args.date, weekday, time) # Return ["sleep", "Home", ["0:00", "7:29"]]

            while (not valid_time(res[2][1])):
                # Check if llm generates invalid time
                res = gen_next_motivation(context, cur_mot, [], args.date, weekday, time)

            if time_exceed(res[2][0], res[2][1]): 
                # Check if llm generates activity that ends tomorrow
                res[2][1] = "23:59"

            if (res[1] != 'Home' or res[1] != 'Workplace' or not (res[0] == 'education' and p[i]["occupation"] == 'student')):
                # Update res to ["sleep", "Hotel", ["0:00", "7:29"], name, coord] format
                recommandation = memory_module.generate_recommendation(str(i), res)
                name, coord, min = memory_module.generate_choice(res, recommandation, 'data/around_unsw.csv') # [name, coord, time (int)]
                res.append(name)
                res.append(coord)
                res[2][1] = time_update(res[2][1], min)
            else:
                res.append(res[1])
                if res[1] == 'Home':
                    res.append(p[i]['home'])
                elif res[1] == 'Workplace':
                    res.append(p[i]['work'])
                else:
                    res.append(p[i]['school'])
                
                # TODO: Update time

            # Next stage: path finder

            # Updating & storing data
            time = res[2][1]

            # Storing ["sleep", "Home", ["0:00", "7:29"], name, coord]
            cur_mot.append(res)

        with open("res/routine_{}_{}.json".format(args.date, i),'w') as f:  
            json.dump(cur_mot, f)

        # TODO: 3. Per day per person storing into memory

    # TODO: 4. Store the memory into files