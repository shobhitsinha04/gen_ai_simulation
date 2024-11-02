import argparse
import pandas as pd
import numpy as np
import json
import random

from helper.utils import llm_generate, random_in_quad
from helper.prompt import person_info_prompt, daily_activity_prompt

def gen_random_trait(mean, std):
    return np.random.normal(loc=mean, scale=std)

def gen_random_personality(data):
    personality = {}

    for key, val in data.items():
        personality[key] = gen_random_trait(val[0], val[1])

    return personality

def gen_random_home(hdata: list[list[list[float]]]):
    c1, c2, c3, c4 = random.choice(hdata)
    return random_in_quad(c1, c2, c3, c4)

def gen_random_school(csv, school: str):
    if (school != 'Other education'):
        schools = csv[csv['Category'] == school]
    else:
        return ['undefined']

    ran_sch = schools.sample(n=1)
    return [ran_sch['Latitude'].values[0], ran_sch['Longitute'].values[0]]

def gen_random_workplace(csv):
    # Need to be changed tocreasonable workplace
    ran_wp = csv.sample(n=1)
    return [ran_wp['Latitude'].values[0], ran_wp['Longitute'].values[0]]

def gen_daily_activities(data, loc):
    daily_act = []
    for p in data:
        global_context = person_info_prompt(p["name"], p["age"], p["gender"], p["occupation"], p["personality"]["ext"], p["personality"]["agr"], p["personality"]["con"], p["personality"]["neu"], p["personality"]["ope"])
        msg = daily_activity_prompt()
        res = llm_generate(global_context, msg)
        daily_act.append(json.loads(res))

    return daily_act

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='genPersona')
    # parser.add_argument('-s', '--social_force') # Include relationship between agents
    parser.add_argument('-n', '--number', type=int, default=1, help="Amount of personas to generate (1 for 5)") # Include relationship between agents
    parser.add_argument('--location', choices=['Sydney', 'Tokyo'], default='Tokyo', 
        help="Choose location: either 'Sydney' or 'Tokyo'", type=str)
    # parser.add_argument('-p', '--exploration') # Include exploration behaviours into the model
    # parser.add_argument('--model', default = '...', type=str)
    # parser.add_argument('--population', default = 'population.json', type=str)
    # parser.add_argument('--mode_choice', default = 'realRatio', type=str)  # realRatio
    args = parser.parse_args()

    if (args.location == 'Sydney'):
        f_path = 'data/SYD'
    else:
        f_path = 'dara/TKY'

    msg = ""
    f1 = open("{}/population.json".format(f_path))
    data = json.load(f1)

    occ_data = data['occupation']
    fields = list(occ_data.keys())
    weights = list(occ_data.values())

    # Include age distribution in the prompt
    for i in range(len(data['age'])):
        msg += "The distribution of males from age {} to {} is {}, where females is {}. ".format(i*5, i*5+4, data['age'][i]['male'], data['age'][i]['female'])

    # Include employment data in the prompt
    msg += "\nTotal employment-to-population ratio for males is {}, for females is {}, where the ratio for males at working age (from 15 to 64 years old) is {}, for female is {}.\
The average age at retirement from labour force is {} years.\n"\
.format(data['employment']['total'][0], data['employment']['total'][1], data['employment']['working_age'][0], data['employment']['working_age'][1], data['retirement'])

    msg += """Please generate 5 independent personas and output the person's name, age, gender and occupation in JSON format based on the given population distribution.
"""
    note = """Note:
1. All students, including university students, high school students, kids in kindergarten etc, shoudld all have occupation "student".
2. Children can choose to start preschool at the age of 4, and must be in compulsory schooling by 6.
3. Unemployed people (including young kids and old people) who are not student, can only have occupation "unemployed" or "retiree".
"""

    ans_format = """Important: Output has to be a list of dictionary, where each dictionary has keys 'name', 'age', 'gender' and 'occupation'.
Output format: [{name, age, gender, occupation}, {...}, ...].
"""
    example = """Example output 1:
[{"name": "Ethan Grayson", "age": 33, "gender": "male", "occupation": "fisherman"}, {"name": "Olivia Lee", "age": 3, "gender": "female", "occupation": "unemployed"}, \
{"name": "Mia Harris", "age": 69, "gender": "female", "occupation": "retiree"}, {"name": "Thomas Turner", "age": 41, "gender": "male", "occupation": "YouTuber"}, {"name": "Li Wei", "age": 26, "gender": "female", "occupation": "electrical engineer"}]
Example output 2:
[{"name": "Jake Evans", "age": 17, "gender": "male", "occupation": "student"}, {"name": "Yuki Tanaka", "age": 31, "gender": "female", "occupation": "dentist"}, \
{"name": "Lily O'Connor", "age": 59, "gender": "female", "occupation": "traffic controller"}, {"name": "Maxwell Rivera", "age": 36, "gender": "male", "occupation": "retail assistant"}, {"name": "Ella Winter", "age": 28, "gender": "female", "occupation": "research assistant"}]
"""

    context = "You are a json generator who always responds required data in json format, but without any additional introduction, text or explanation."

    print("======== Start! ========")
    personas = []
    for i in range(args.number):
        # Pick 5 potential jobs for selection
        potential_jobs = random.choices(fields, weights=weights, k=5)
        final_msg = msg + note + \
        "4. If the persona is employed, please pick one of the industry division from {}, and generate a occupation under this division. \
For example, a persona with occupation 'fisherman' under the division 'Agriculture, Forestry and Fishing' should have occupation value as 'fisherman', \
which means DON'T include the division name in the occupation value. e.g. {{\"name\": ..., \"age\": ..., \"gender\": ..., \"occupation\": \"fisherman\"}}\n"\
        .format(potential_jobs) + \
        "5. When generating personas, don't have to always include student, retiree or unemployed people. Generate persona based on the distribution of population." + ans_format

        print("Final msg: " + final_msg)
        print("=== Waiting for LLAMA ===")
        res = llm_generate(context, final_msg)

        print("Persona it {}:\noutput: {}".format(i, res))

        res = json.loads(res)
        personas.extend(res)

    # Finialise personality
    big5 = open("{}/big5.json".format(f_path))
    big5_data = json.load(big5)
    for p in personas:
        p["personality"] = gen_random_personality(big5_data)

    # Generate act-loc list for each persona
    daily_act = gen_daily_activities(personas, args.location)
    with open('res/activities.json','w+') as f2:
        json.dump(daily_act, f2)

    homes = open('data/home.json') # TODO: residental places
    hdata = json.load(homes)

    csv = pd.read_csv('data/around_unsw.csv')
    for i in range(len(personas)):
        personas[i]["home"] = gen_random_home(hdata)
        if (personas[i]["occupation"] == "student"):
            personas[i]["school"] = gen_random_school(csv, daily_act[i]["education"][1][0])
        elif (personas[i]["occupation"] != "unemployed" and personas[i]["occupation"] != "retiree"):
            personas[i]["work"] = gen_random_workplace(csv)

    with open('res/personas.json','w+') as f3:
        json.dump(personas, f3)