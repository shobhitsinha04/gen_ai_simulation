import json
from typing import List, Tuple
import openai
from datetime import datetime, timedelta
import spacy
import pandas as pd

# OpenAI API 
openai.api_key = 'api key'

class MemoryModule:
    def __init__(self):
        # dictionary to store daily activities 
        self.daily_activities = {}  # dict[str(persona id), dict[str, List[List[str]]](dict with key as date and value is the list of activities) ]

        # dictionary to store daily summaries 
        self.summaries = {} 
        # dict[str(persona id), dict[str, str](dict with str as date and string as the summary)] 

        # dictionary to store weekly summaries
        self.weekly_summaries = {} 
        #  dict[str(persona id), dict[int, str](dict with key number as int and string as the weekly summary)]

        # counter to keep track of the number of days
        self.day_counters = {} 
        # dict[str, int] (dict with key as persona id and value as the number of accesses)

        # dictionary to store monthly summaries 
        self.monthly_summaries = {} 
        # dict[str(persona id), dict[str, str](dict with the key as the month and the value as the monthly summary)]

        # counter to see how many times a memory is accessed 
        self.memory_access_counter = {} 
        # dict[str(persona id), dict[str, int](dict with the key as the date and the value is the number of the times the memory is accessed)]

        #  pre defined threshold 
        self.memory_threshold = 0.5 
        #YET TO DECIDE THE VALUE

        # Loading the spaCy model
        self.nlp = spacy.load("en_core_web_sm") #check

    def store_daily_activities(self, activities_dict: dict[str, dict[str, List[List[str]]]]):
        """
        Stores the activities for a specific date and persona.
        activities_dict: A dictionary containing the activities for each persona and date.
        Sample format: {"1": {"2024-07-10": [["sports and exercise", "Gym", ["19:21", "20:02"]], ...]}}
        """
        for persona_id, dates in activities_dict.items():
            if persona_id not in self.daily_activities:
                self.daily_activities[persona_id] = {}
                self.day_counters[persona_id] = 0
            for date, activities in dates.items():
                self.daily_activities[persona_id][date] = activities
                self.day_counters[persona_id] += 1


    ########################################################################################## 
    # FOR SUMMARIZATION
    ########################################################################################## 
    def summarize_day(self, persona_id: str, date: str):
        """
        Summarizes the activities of a specific day for a specific persona using GPT model.
        persona_id: The ID of the persona
        date: The date of the activities to be summarized.
        """
        #retrieve the activities for each date and then converts the activities to a json string format for input to the LLM
        activities = self.daily_activities.get(persona_id, {}).get(date, [])
        activities_json = json.dumps(activities)
        
        # Call OpenAI's API to generate a summary of the activities
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Please summarize the following activities for the day in a concise, coherent paragraph: {activities_json}"}
                ],
                max_tokens=100,
            )
        except openai.OpenAIError as e:
            print(f"Error generating summary: {e}")
            return
            
        # Get the summary text from the response and store it in the summaries dictionary  
        summary = response['choices'][0]['message']['content'].strip()

        if persona_id not in self.summaries:
            self.summaries[persona_id] = {}
        self.summaries[persona_id][date] = summary

        # initialize the memory access counter for the date
        if persona_id not in self.memory_access_counter:
            self.memory_access_counter[persona_id] = {}
        self.memory_access_counter[persona_id][date] = 0
        # return summary


    def summarize_week(self, persona_id: str, end_date: str):
        """
        Summarizes the activities of a specific week for a specific persona using GPT model.
        persona_id: The ID of the persona.
        end_date: The end date of the week to be summarized.
        """
        # making the date in the right format 
        end_date_dt = datetime.strptime(end_date, '%d-%m-%Y')

        # get the last 7 dates before
        dates = []
        for i in range(7):
            date = end_date_dt - timedelta(days=i)
            dates.append(date.strftime('%d-%m-%Y'))

        # then combine daily summaries of those 7 days
        input_weekly_summary = []
        for date in dates:
            # Checking if the date exists in the summaries dictionary
            if date in self.summaries.get(persona_id, {}):
                input_weekly_summary.append(self.summaries[persona_id][date])

        input_weekly_summary = " ".join(input_weekly_summary)

        # call the api to generate the summary
        try: 
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Here are the daily summaries for the week ending on {end_date}. Please provide a concise and coherent weekly summary in a single paragraph, focusing on the main activities and events:\n{input_weekly_summary}"}
                ],
                max_tokens=200,
            )
        except openai.OpenAIError as e:
            print(f"Error generating weekly summary: {e}")
            return

        weekly_summary = response['choices'][0]['message']['content'].strip()
        week_number = end_date_dt.isocalendar()[1]
        
        if persona_id not in self.weekly_summaries:
            self.weekly_summaries[persona_id] = {}

        self.weekly_summaries[persona_id][week_number] = weekly_summary

    
    def summarize_month(self, persona_id: str, end_date: str):
        """
        Summarizes the activities of a specific month using GPT model.
        persona_id: The ID of the persona.
        end_date: The end date of the month to be summarized.
        """
        end_date_dt = datetime.strptime(end_date, '%d-%m-%Y')
        start_date_dt = end_date_dt.replace(day=1)

        daywise_summaries = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
            "Sunday": []
        }

        current_date_dt = start_date_dt
        # loop through all the days of the month
        while current_date_dt <= end_date_dt: 
            date_str = current_date_dt.strftime('%d-%m-%Y')
            day_name = current_date_dt.strftime('%A')

            # if a summary exists for that day then add it to the dict 
            if date_str in self.summaries.get(persona_id, {}):
                daywise_summaries[day_name].append(self.summaries[persona_id][date_str])
            
            current_date_dt += timedelta(days=1)

        monthly_summary = {}

        for day, summaries in daywise_summaries.items():
            if summaries:
                input_monthly_summary = " ".join(summaries)

                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": f"Please summarize the following activities for all {day}s in the month in a structured and coherent paragraph:\n{input_monthly_summary}"}
                        ],
                        max_tokens=300,
                    )
                except openai.OpenAIError as e:
                    print(f"Error generating monthly summary for {day}: {e}")
                    continue

                monthly_summary[day] = response['choices'][0]['message']['content'].strip()


        month_year = end_date_dt.strftime('%m-%Y')
        if persona_id not in self.monthly_summaries:
            self.monthly_summaries[persona_id] = {}

        self.monthly_summaries[persona_id][month_year] = monthly_summary
                           
    ########################################################################################## 
    # FOR RETRIEVAL
    ##########################################################################################
    
    def retrieve_activities_by_location(self, persona_id: str, activity_info: List):
        """
        Retrieves historical activities based on a specific activity information.
        activity_info: List containing the intention, location category, and the time range.
        Sample input: ["sports and exercise", "Gym", ["19:21", "20:02"]]
        """
        global cata_act

        # getting the info from the list
        intention = activity_info[0].lower()
        location_category = activity_info[1].lower()
        # time_range = activity_info[2]

        locations = cata_act.get(location_category, [])
        relevant_activities = []

        for date, activities in self.daily_activities.get(persona_id, {}).items():
            for activity in activities:
                if activity[0] == intention and activity[1] in locations:
                    relevant_activities.append(f"{activity[0]} at {activity[1]} on {date}")
        return relevant_activities

    def generate_recommendation(self, persona_id: str, activity_info: List):
        """
        Generates a recommendation based on the intention and location and also looks at historically where all the person has gone.
        activity_info: List containing the intention, location category, and the time range.
        Sample input: ["sports and exercise", "Gym", ["19:21", "20:02"]]
        """
        # getting the relevant activities from history for the type of location category
        relevant_activities = self.retrieve_activities_by_location(persona_id, activity_info)
        activities_str = "; ".join(relevant_activities)
        if not activities_str:
            activities_str = "No relevant historical activities found."
        
        intention = activity_info[0]
        location_category = activity_info[1]
        # time_range = activity_info[2]
        
        # creating the prompt
        prompt = (
            f"The persona has an intention to '{intention}' and a preference for the '{location_category}' category. "
            # f"The time range is from {time_range[0]} to {time_range[1]}. "
            f"Based on historical activities: {activities_str}. Please give a line that can be used as a recommendation and help the persona choose a location for the activity."
        )
        try:
            response = openai.ChatCompletion.create(
                model = "gpt-3.5-turbo",
                messages=[
                    {"role":"system", "content":"You are a helpful assistant"},
                    {"role":"user", "content":prompt}
                ],
                max_tokens = 150,
            )
            recommendation = response['choices'][0]['message']['content'].strip()
            return recommendation
        except openai.OpenAIError as e:
            print(f"Error generating recommendation: {e}")
            return "Error generating the recommendation. Please try again later."


    def get_places_from_csv(self, file_path: str) -> List[dict[str, str]]:
        places = []
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            places.append({
                'Name': row['Name'],
                'Coordinates': (row['Latitude'], row['Longitute'])
            })
        return places
    
    def generate_choice(self, activity_info: List, recommendation: str, file_path: str) -> dict[str, any]:
        places = self.get_places_from_csv(file_path)
        activities_str = f"Activity: {activity_info[0]}, Location Category: {activity_info[1]}, Time: {activity_info[2]}"
        
        # Creating the prompt
        prompt = (
            f"The persona has an activity info: {activities_str}. Based on the recommendation: '{recommendation}', "
            f"please pick the best choice from the list of places in the attached CSV file. Provide the name, coordinates, "
            f"and an estimated transport time in minutes.\n"
        )

        for place in places:
            prompt += f"{place['Name']}, Coordinates: ({place['Coordinates'][0]}, {place['Coordinates'][1]})\n"

        # Call the OpenAI API to generate the choice
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
            )
            choice = response['choices'][0]['message']['content'].strip()
            
            #getting the details from the llm response
            lines = choice.split(',')
            name = lines[0].strip()
            coordinates = lines[1].split(':')[1].strip().strip('()').split()
            transport_time = int(lines[2].split(':')[1].strip().split()[0])

            return {
                name,
                [float(coord) for coord in coordinates],
                transport_time
            }

        except openai.OpenAIError as e:
            print(f"Error generating choice: {e}")
            return {}




    
    ##########################################################################################
    # FOR MEMORY DELETION
    ##########################################################################################
    def calculate_information_density(self, summary: str):
        #need to include a way to make it personal for each user and generate the values for the categories in persona generation
        """
        Calculates the weighted information density of a summary.
        Output would be a float
        """
        categories = {
            "events" : 0.5, # (e.g., "passed a test," "attended a meeting")   #check if you can personalize this
            "entities": 0.2, # (e.g., "person," "location")
            "actions": 0.3, # (e.g., "completed," "started")
            "attributes": 0.3 # (e.g., "high score," "difficult task")
        }
        # NER using spacy
        doc = self.nlp(summary)

        # Initial counts of each type of thing
        counts = {
            "events": 0,
            "entities": 0,
            "actions": 0,
            "attributes": 0
        }

        # Going through summaries to see how much of each type is present in the summary
        for ent in doc.ents:
            if ent.label_ in ["EVENT"]:
                counts["events"] += 1
            elif ent.label_ in ["PERSON", "ORG", "GPE", "LOC"]:
                counts["entities"] += 1

        for token in doc:
            if token.pos_ in ["VERB"]:
                counts["actions"] += 1
            elif token.pos_ in ["ADJ", "ADV"]:
                counts["attributes"] += 1

        weighted_sum = sum(categories[cat] * counts[cat] for cat in categories)
        total_words = len(summary.split())
        weighted_info_density = weighted_sum / total_words if total_words > 0 else 0

        return weighted_info_density
    
    def calculate_importance_score(self, persona_id: str, date: str, summary: str):
        """
        Calculates the importance score based on recency, frequency, and information density.
        """
        frequency = self.memory_access_counter.get(persona_id, {}).get(date, 0)
        recency = (datetime.now() - datetime.strptime(date, '%d-%m-%Y')).days
        weighted_info_density = self.calculate_information_density(summary)

        # Normalizing the recency and frequency 
        max_recency = 90 #last 3 months
        normalized_recency = 1 - min(recency / max_recency, 1) # it is (1 -) because the more recent memory should have higher score
        
        max_frequency = max(self.memory_access_counter.get(persona_id, {}).values(), default=0)  
        max_frequency = max(1, max_frequency)  # Ensure max_frequency is at least 1 to avoid division by zero
    
        
        normalized_frequency = min(frequency / max_frequency, 1)

        # Calculating the overall importance score for the memory
        importance_score = (normalized_frequency + normalized_recency + weighted_info_density) / 3

        return importance_score

    def deleting_memory(self):
        """
        Deletes the memory of the user based on the memory access threshold.
        """
        for persona_id, summaries in list(self.summaries.items()):
            for date, summary in list(summaries.items()):
                # iterates over the summaries dictionary and deletes the low scoring daily summaries and daily activities
                importance_score = self.calculate_importance_score(persona_id, date, summary)
                if importance_score < self.memory_threshold:
                    del self.summaries[persona_id][date]
                    self.memory_access_counter[persona_id].pop(date, None)
                    if date in self.daily_activities.get(persona_id, {}):
                        self.daily_activities[persona_id].pop(date, None)


#Testing the module 

# Sample activities dictionary
cata_act = {
    "work": ["..."],
    "go home": ["home"],
    "eat": ["home", "restaurant", "cafe", "pub and bar", "food court"],
    "sleep": ["home", "hotel"],
    "shopping": ["grocery", "other shopping"],
    "sports and exercise": ["gym", "field", "park"],
    "leisure activities": ["home", "cinemas", "park", "stadium", "museum"],
    "medical treatment": ["hospital", "clinic", "dentist"],
    "education": ["university", "VET", "primary and secondary school", "preschool", "library", "other education"],
    "religious activities": ["church"],
    "trifles": ["legal and financial service", "automotive service", "health and beauty service"]
}

# Testing the MemoryModule
if __name__ == "__main__":
    memory_module = MemoryModule()
    
    activities_dict = {
        "1": {
            "01-07-2024": [["sports and exercise", "Gym", ["19:21", "20:02"]], ["eat", "restaurant", ["12:00", "13:00"]]],
            "02-07-2024": [["sports and exercise", "Gym", ["19:21", "20:02"]]],
            "03-07-2024": [["sports and exercise", "Gym", ["19:21", "20:02"]], ["eat", "cafe", ["12:00", "13:00"]]],
            "04-07-2024": [["sports and exercise", "Gym", ["19:21", "20:02"]], ["eat", "restaurant", ["12:00", "13:00"]]],
            "05-07-2024": [["sports and exercise", "Gym", ["19:21", "20:02"]], ["work", "university", ["09:00", "17:00"]]],
            "06-07-2024": [["sports and exercise", "Gym", ["19:21", "20:02"]]],
            "07-07-2024": [["sports and exercise", "Gym", ["19:21", "20:02"]], ["eat", "restaurant", ["12:00", "13:00"]]]
        },
        "2": {
            "01-07-2024": [["eat", "home", ["07:00", "07:30"]], ["work", "office", ["09:00", "17:00"]]],
            "02-07-2024": [["eat", "home", ["07:00", "07:30"]], ["work", "office", ["09:00", "17:00"]]],
            "03-07-2024": [["eat", "home", ["07:00", "07:30"]], ["work", "office", ["09:00", "17:00"]]],
        },
        "3": {
            "01-07-2024": [["leisure activities", "cinemas", ["20:00", "23:00"]]],
            "02-07-2024": [["sports and exercise", "park", ["06:00", "07:00"]]],
        },
        "4": {
            "01-07-2024": [["medical treatment", "clinic", ["10:00", "11:00"]]],
            "02-07-2024": [["sports and exercise", "Gym", ["19:21", "20:02"]]],
        }
    }

    # Store daily activities
    memory_module.store_daily_activities(activities_dict)

    # Generate summaries for each day
    for persona_id, dates in activities_dict.items():
        for date in dates.keys():
            memory_module.summarize_day(persona_id, date)
            if date in memory_module.summaries[persona_id]:  # Check if the summary was successfully generated
                print(f"Summary for persona {persona_id} on {date}: {memory_module.summaries[persona_id][date]}")
            else:
                print(f"Summary for persona {persona_id} on {date} was not generated.")
            print("\n")
            
            # Checking if 7 days have passed to generate a weekly summary
            if memory_module.day_counters[persona_id] % 7 == 0:
                memory_module.summarize_week(persona_id, date)

    # Check the generated weekly summary for each persona
    # getting the most recent date
    most_recent_date_str = max(date for persona in activities_dict.values() for date in persona.keys())
    # converts it to the right format and gets the iso week number 
    week_number = datetime.strptime(most_recent_date_str, '%d-%m-%Y').isocalendar()[1]

    for persona_id in activities_dict.keys():
        if persona_id in memory_module.weekly_summaries and week_number in memory_module.weekly_summaries[persona_id]:
            print(f"Weekly summary for persona {persona_id} for week {week_number}: {memory_module.weekly_summaries[persona_id][week_number]}")
        else:
            print(f"Weekly summary for persona {persona_id} for week {week_number} was not generated.")
        print("\n")

    # Generating and checking the monthly summary
    end_date_str = "07-07-2024"  # assume this is the date that is passed on to the summarize month function to generate the monthly summary for
    for persona_id in activities_dict.keys():
        memory_module.summarize_month(persona_id, end_date_str)
        month_year = datetime.strptime(end_date_str, '%d-%m-%Y').strftime('%m-%Y')
        if month_year in memory_module.monthly_summaries[persona_id]:  # Check if the monthly summary was generated
            print(f"Monthly summary for persona {persona_id} for {month_year}: {memory_module.monthly_summaries[persona_id][month_year]}")
        else:
            print(f"Monthly summary for persona {persona_id} for {month_year} was not generated.")
        print("\n")

    # Retrieving historical tasks based on location category and intention
    activity_info = ["eat", "restaurant", ["12:00", "13:00"]]
    for persona_id in activities_dict.keys():
        activities = memory_module.retrieve_activities_by_location(persona_id, activity_info)
        print(f"Historical activities for persona {persona_id} with activity info '{activity_info}': {activities}")
        print("\n")

    # Generating recommendation based on intention and location category
    for persona_id in activities_dict.keys():
        recommendation = memory_module.generate_recommendation(persona_id, activity_info)
        print(f"Recommendation for persona {persona_id} with activity info '{activity_info}': {recommendation}")
        print("\n")

    # Generating choice based on the recommendation
    file_path = 'around_unsw.csv' 
    for persona_id in activities_dict.keys():
        choice = memory_module.generate_choice(activity_info, recommendation, file_path)
        print(f"Choice for persona {persona_id} with activity info '{activity_info}' and recommendation '{recommendation}': {choice}")
        print("\n")

    # Example: Deleting less important information
    memory_module.deleting_memory()
    for persona_id in activities_dict.keys():
        print(f"Summaries for persona {persona_id} after deletion: {memory_module.summaries[persona_id]}")



    # def retrieve_activities_by_location(self, persona_id: str, location_category: str, intention: str):
    #     """
    #     Retrieves historical activities based on a specific location category and intention.
    #     sample input: memory_module.retrieve_activities_by_location("1", "eat", "eat breakfast")
    #     """
    #     global cata_act
    #     locations = cata_act.get(location_category, [])
    #     relevant_activities = []

    #     for date, activities in self.daily_activities.get(persona_id, {}).items():
    #         for activity in activities:
    #             if activity[0] == intention and activity[1] in locations:
    #                 relevant_activities.append(f"{activity[0]} at {activity[1]} on {date} during {activity[2][0]} to {activity[2][1]}")
    #     return relevant_activities