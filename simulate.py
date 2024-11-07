import argparse
import datetime
import re
import json
import pandas as pd
import random

# import dest_phy.recommend as rcmd
# from dest_phy.densmapClass import *
from densmapClass import *
import recommend as rcmd
from topk_lossy_count import *
from helper.utils import llama_generate, gpt_generate, mem_retrieval, act_loc
from helper.prompt import person_info_prompt, next_motivation_prompt
from mem_module_upgraded import MemoryModule

import time as slp

def validate_date(date_str: str):
    # Regular expression for validating date format dd-mm-yyyy
    if not re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):
        raise argparse.ArgumentTypeError("Invalid date format. Expected dd-mm-yyyy.")
    return date_str

def valid_time(time_str: str):
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

def check_routine_finished(time: str):
    return time == "23:59"

def time_exceed(t1: str, t2: str):
    format = '%H:%M'
    time1_obj = datetime.datetime.strptime(t1, format).time()
    time2_obj = datetime.datetime.strptime(t2, format).time()

    return time1_obj > time2_obj

def time_update(curr_time: str, min: int):
    format = '%H:%M'
    time_obj = datetime.datetime.strptime(curr_time, format)
    new_time = time_obj + datetime.timedelta(minutes=min)
    return new_time.strftime(format)

def gen_time_duration(mean, var):
    # Using chi-squared distribution
    a = var / (2 * mean)
    k = 2 * (mean * mean) / var

    random_value = np.random.chisquare(df=k)
    print(str(a * random_value))
    return a * random_value

def valid_mot(data):
    return isinstance(data, list) and len(data) == 3 and isinstance(data[0], str) and isinstance(data[1], str)\
        and isinstance(data[2], list) and len(data[2]) == 2 and all(isinstance(item, str) for item in data[2])

def gen_next_motivation(llm: str, context: str, pre_mot, mem, date: str, weekday: str, time: str):
    msg = next_motivation_prompt(pre_mot, mem, date, weekday, time)
    # print(msg)
    while True:
        if llm == 'llama':
            print("--- llama ---")
            res = llama_generate(context, msg)
        else:
            print("--- gpt ---")
            res = gpt_generate(context, msg, 256)
        
        print(res)
        try:
            parsed_json = json.loads(res)
            if valid_mot(parsed_json):
                break
            else:
                if (valid_mot(parsed_json[0])):
                    parsed_json = parsed_json[0]
                    print("Invalid Format received, fixed...")
                    break
                else:
                    print("Invalid Format received, retrying...")

        except json.JSONDecodeError:
            print("Invalid JSON received, retrying...")
            
    return parsed_json

parser = argparse.ArgumentParser(description='genMotivation')
# parser.add_argument('-a', action='store_true') # Generate activity list for each persona
parser.add_argument('-d', '--date', type=validate_date, help="Date in the format dd-mm-yyyy")
parser.add_argument('-n', '--num_of_days', type=int, default=1, help="Number of days to simulate")
parser.add_argument('--location', choices=['Sydney', 'Tokyo'], default='Tokyo', 
    help="Choose location: either 'Sydney' or 'Tokyo'", type=str)
parser.add_argument('-m', "--model", choices=['physical', 'physical_mix', 'llm'], default='llm',
    help="Specify the model type to use: 'physical', 'physical_mix' or 'llm'", type=str)
parser.add_argument('-l', "--llm", choices=['llama', 'gpt'], default='llama',
    help="Specify the model type to use: llama or gpt", type=str)

# parser.add_argument('-p', '--exploration') # Include exploration behaviours into the model
# parser.add_argument('--population', default = 'population.json', type=str)
# parser.add_argument('--mode_choice', default = 'realRatio', type=str)  # realRatio
args = parser.parse_args()

if __name__ == '__main__':
    # TODO: 5. Load mem files into memory
    memory_module = MemoryModule()
    memory_module.load_memory_from_file()
    topk_counter = load_topk()
    densmap = rcmd.read_densmaps()

    print("day count {}".format(memory_module.day_counters))

    f1 = open("res/personas.json")
    p = json.load(f1)
    date = args.date
    if (not date):
        date = datetime.datetime.today().strftime("%d-%m-%Y")

    weekday = get_weekday(date)

    f2 = open("res/activities.json")
    act = json.load(f2)

    # TODO: SYD
    time_duration = pd.read_csv("data/TKY/cat_duration.csv")

    # Per day simulation
    for num in range(args.num_of_days):
        mem_res = {}

        # Per person simulation
        for i in range(len(p)):
            cur_routine = []
            time = "0:00"

            # Retrieve memory
            mem = mem_retrieval(memory_module, i, date, weekday)
            print("Mem: " + mem)
            
            if mem == '':
                mem = 'No historical data available.'

            # Prepare prompt
            context = person_info_prompt(args.location, p[i]["name"], p[i]["age"], p[i]["gender"], p[i]["occupation"], p[i]["personality"]["ext"], p[i]["personality"]["agr"], p[i]["personality"]["con"], p[i]["personality"]["neu"], p[i]["personality"]["ope"])
            context += """Your daily activities, their frequencies and possible happening locations is given in your daily activity dictionary. \
Each activity in your daily activity dictionary is given in the format 'activity: [frequency, location list]' as following:  
{}.""".format(act[i])
            
            print("=== Date {} Person {} ===\n".format(date, i))
            # Generate routine
            while (not check_routine_finished(time)):
                print("=== Person {}, now is {} ===".format(i, time))
                # This is the loop that generate one day routine activity by activity (for one person)
                while True:
                    res = gen_next_motivation(args.llm, context, cur_routine, mem, date, weekday, time) # Return ["sleep", "Home", ["0:00", "7:29"]]
                    if (res[0] not in act_loc) or (res[1] not in act_loc[res[0]]) or not valid_time(res[2][1]):
                        print("\n~~~~~ Rebuilding ~~~~~\n")
                        continue
                    else:
                        break

                
                print("=== Initial Motivation ===")
                print(res)

                # Check if home/workplace/education
                if (res[1] != 'Home' and res[1] != 'Workplace' and not (res[0] == 'education' and p[i]["occupation"] == 'student')):
                    if args.model == 'physical':
                        if len(cur_routine) == 0:
                            user_loc = p[i]['home']
                        else:
                            user_loc = cur_routine[-1][-1]
                        name, coord = rcmd.recommend(user_loc, res, densmap,  i, topk_counter, model='gravity')
                        
                        # Time Update
                        cate_data = time_duration[time_duration['category'] == res[1]]
                        mean = cate_data['avg_duration'].values[0]
                        var = cate_data['variance'].values[0]
                        res[2][1] = time_update(res[2][0], gen_time_duration(mean, var))

                    elif args.model == 'physical_mix':
                        user_loc = cur_routine[-1][-1]
                        name, coord = rcmd.recommend(user_loc, res, densmap, i, topk_counter, model='mix')
                        
                        # Time Update
                        cate_data = time_duration[time_duration['category'] == res[1]]
                        mean = cate_data['avg_duration'].values[0]
                        var = cate_data['variance'].values[0]
                        res[2][1] = time_update(res[2][0], gen_time_duration(mean, var))

                    else:
                        recommandation = memory_module.generate_recommendation(str(i), res)
                        print("--- recommandation --- ")
                        print(recommandation)
                        if (args.location == 'Tokyo'):
                            name, coord, min = memory_module.generate_choice(args.location, res, recommandation, "POI_data/{}_ca_poi.csv".format(res[1])) # [id, coord, time (int)]
                        else:
                            name, coord, min = memory_module.generate_choice(args.location, res, recommandation, 'data/SYD/around_unsw.csv') # [name, coord, time (int)]

                        # Time update
                        res[2][1] = time_update(res[2][1], min)
                    
                    # Update res to ["sleep", "Hotel", ["0:00", "7:29"], name, coord] format
                    res.append(name)
                    res.append(coord)

                else:
                    res.append(res[1]) # name of the dest

                    # Coord of dest
                    if res[1] == 'Home':
                        res.append(p[i]['home'])
                    elif res[1] == 'Workplace':
                        res.append(p[i]['work'])
                    else:
                        res.append(p[i]['school'])
                        
                        # Time Update
                        cate_data = time_duration[time_duration['category'] == res[1]]
                        mean = cate_data['avg_duration'].values[0]
                        var = cate_data['variance'].values[0]

                        min = max(gen_time_duration(mean, var), 90)
                        # res[2][1] = random.choice([time_update(res[2][0], min), res[2][1]])
                        res[2][1] = time_update(res[2][0], min)
                    
                res[2][1] = time_update(res[2][1], random.randint(0, 9))

                # Error handling
                if time_exceed(res[2][0], res[2][1]):
                    # Check if llm generates activity that ends tomorrow
                    res[2][1] = "23:59"

                # TODO: Next stage: path finder

                # Updating & storing data
                time = res[2][1]

                print("=== Final Movement ===")
                # Storing ["sleep", "Home", ["0:00", "7:29"], name, coord]
                print(res)
                cur_routine.append(res)

            with open("res/routine_{}_{}.json".format(date, i),'w') as f:
                json.dump(cur_routine, f)
            
            mem_res[str(i)] = { date: cur_routine }

            print("NEXT LOOP")
            slp.sleep(2.5)

        # Per day storing into memory
        memory_module.store_daily_activities(mem_res)

        _count = 0
        for persona_id, dates in mem_res.items():
            _count += 1
            for date in dates.keys():
                print("=== Day Summary {} ===".format(_count))
                memory_module.summarize_day(persona_id, date)
                # Checking if 7 days have passed to generate a weekly summary
                if memory_module.day_counters[persona_id] % 7 == 0:
                    print("=== Month Summary ===")
                    memory_module.summarize_week(persona_id, date)
                    memory_module.summarize_month(persona_id, date)
        
        print("=== Saving up topk ===")
        update_topk(topk_counter, mem_res)

        date_obj = datetime.datetime.strptime(date, '%d-%m-%Y')
        date = (date_obj + datetime.timedelta(days=1)).strftime("%d-%m-%Y")
        weekday = get_weekday(date)

    # TODO: 4. Store the memory into files
    print("=== storing mem ===")
    memory_module.store_memory_to_file()

    print("=== storing topk ===")
    save_topk(topk_counter)
