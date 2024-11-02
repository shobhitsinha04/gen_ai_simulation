import argparse
import pandas as pd
import numpy as np
import json
import random

from helper.utils import llm_generate, random_in_quad
from helper.prompt import person_info_prompt, daily_activity_prompt, persona_prompt

def gen_random_trait(mean, std):
    return np.random.normal(loc=mean, scale=std)

def gen_random_personality(data):
    personality = {}

    for key, val in data.items():
        personality[key] = gen_random_trait(val[0], val[1])

    return personality

def gen_random_home_SYD(hdata: list[list[list[float]]]):
    c1, c2, c3, c4 = random.choice(hdata)
    return random_in_quad(c1, c2, c3, c4)

def gen_random_school_SYD(csv, school: str):
    if (school != 'Other education'):
        schools = csv[csv['Category'] == school]
    else:
        return ['undefined']

    return gen_random_place_SYD(schools)

def gen_random_place_SYD(csv):
    # Need to be changed tocreasonable workplace
    ran_p = csv.sample(n=1)
    return [ran_p['Latitude'].values[0], ran_p['Longitute'].values[0]]

def gen_random_school_TKY(school: str):
    data = open('POI_data/{}_ca_poi.csv'.format(school)) 
    schools = pd.read_csv(data)

    return gen_random_place_TKY(schools)

def gen_random_workplace_TKY(industry: str):
    data = open('POI_data/Workplace/{}_ca_poi.csv'.format(industry)) 
    workplaces = pd.read_csv(data)

    return gen_random_place_TKY(workplaces)

def gen_random_place_TKY(csv):
    # Need to be changed tocreasonable workplace
    ran_p = csv.sample(n=1)
    return [ran_p['lat'].values[0], ran_p['lng'].values[0]]

def gen_daily_activities(data, loc):
    daily_act = []
    for p in data:
        global_context = person_info_prompt(loc, p["name"], p["age"], p["gender"], p["occupation"], p["personality"]["ext"], p["personality"]["agr"], p["personality"]["con"], p["personality"]["neu"], p["personality"]["ope"])
        msg = daily_activity_prompt(args.location)
        res = llm_generate(global_context, msg)
        daily_act.append(json.loads(res))

    return daily_act

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='genPersona')
    # parser.add_argument('-s', '--social_force') # Include relationship between agents
    parser.add_argument('-n', '--number', type=int, default=1, help="Amount of personas to generate (1 for 5)") # Include relationship between agents
    parser.add_argument('--location', choices=['Sydney', 'Tokyo'], default='Tokyo', 
        help="Choose location: either 'Sydney' or 'Tokyo'", type=str)
    args = parser.parse_args()

    if (args.location == 'Sydney'):
        f_path = 'data/SYD'
    else:
        f_path = 'data/TKY'

    f1 = open("{}/population.json".format(f_path))
    data = json.load(f1)

    occ_data = data['occupation']
    fields = list(occ_data.keys())
    weights = list(occ_data.values())

    msg = persona_prompt(data, args.location)

    ans_format = """Important: Output has to be a list of dictionary, where each dictionary has keys 'name', 'age', 'gender' and 'occupation'.
Output format: [{name, age, gender, occupation}, {...}, ...].
"""

#     example = """Example output 1:
# [{"name": "Ethan Grayson", "age": 33, "gender": "male", "occupation": "fisherman"}, {"name": "Olivia Lee", "age": 3, "gender": "female", "occupation": "unemployed"}, \
# {"name": "Mia Harris", "age": 69, "gender": "female", "occupation": "retiree"}, {"name": "Thomas Turner", "age": 41, "gender": "male", "occupation": "YouTuber"}, {"name": "Li Wei", "age": 26, "gender": "female", "occupation": "electrical engineer"}]
# Example output 2:
# [{"name": "Jake Evans", "age": 17, "gender": "male", "occupation": "student"}, {"name": "Yuki Tanaka", "age": 31, "gender": "female", "occupation": "dentist"}, \
# {"name": "Lily O'Connor", "age": 59, "gender": "female", "occupation": "traffic controller"}, {"name": "Maxwell Rivera", "age": 36, "gender": "male", "occupation": "retail assistant"}, {"name": "Ella Winter", "age": 28, "gender": "female", "occupation": "research assistant"}]
# """

    context = "You are a json generator who always responds required data in json format, but without any additional introduction, text or explanation."

    print("======== Start! ========")
    personas = []
    for i in range(args.number):
        # Pick 5 potential jobs for selection
        potential_jobs = random.choices(fields, weights=weights, k=5)
        final_msg = msg + \
        "4. If the persona is employed, please pick one of the industry division from {}, and then assign the 'occupation' attribute of the persona \
to be the picked industry division. e.g. {{\"name\": Hikaru Satou, \"age\": 29, \"gender\": female, \"occupation\": \"Manufacturing\"}}\n".format(potential_jobs) + \
        "5. When generating personas, don't have to always include student, retiree or unemployed people. \
Generate persona based on the distribution of population, and the age and sex of the persona." + ans_format

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

    if (args.location == 'Sydney'):
        csv = pd.read_csv('data/SYD/around_unsw.csv')
        homes = open('data/SYD/home.json') 
        hdata = json.load(homes)

        for i in range(len(personas)):
            personas[i]["home"] = gen_random_home_SYD(hdata)
            if (personas[i]["occupation"] == "student"):
                personas[i]["school"] = gen_random_school_SYD(csv, daily_act[i]["education"][1][0])
            elif (personas[i]["occupation"] != "unemployed" and personas[i]["occupation"] != "retiree"):
                personas[i]["work"] = gen_random_place_SYD(csv)
    else:
        homes = open('POI_data/Home_ca_poi.csv') 
        hdata = pd.read_csv(homes)
        for i in range(len(personas)):
            personas[i]["home"] = gen_random_place_TKY(hdata)
            if (personas[i]["occupation"] == "student"):
                personas[i]["school"] = gen_random_school_TKY(daily_act[i]["education"][1][0])
            elif (personas[i]["occupation"] != "unemployed" and personas[i]["occupation"] != "retiree"):
                personas[i]["work"] = gen_random_workplace_TKY(personas[i]["occupation"])

    with open('res/personas.json','w+') as f3:
        json.dump(personas, f3)