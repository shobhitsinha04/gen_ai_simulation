import json
from typing import List, Tuple
import openai
from datetime import datetime, timedelta
import spacy 

# OpenAI API 
openai.api_key = 'api-key'

class MemoryModule:
    def __init__(self):
        # dictionary to store daily activities with date as the key
        self.daily_activities = {}
        # dictionary to store daily summaries with date as the key
        self.summaries = {}
        # dictionary to store weekly summaries with week number as the key
        self.weekly_summaries = {}
        # counter to keep track of the number of days
        self.day_counter = 0
        # dictionary to store monthly summaries with month as the key
        self.monthly_summaries = {}
        # counter to see how many times a memory is accessed 
        self.memory_access_counter = {}
        #  pre defined threshold 
        self.memory_threshold = 0.5 #YET TO DECIDE THE VALUE

        # Loading the spaCy model
        self.nlp = spacy.load("en_core_web_sm") #check

    def store_daily_activities(self, activities_dict : dict[str, List[List[str]]]):
        """
        Stores the activities for a specific date.
        activities_dict: A dictionary containing the activities for each date.
        Sample format: {"2024-07-10": [["sleep", "(00:00, 08:11)"], ...]} 
        """
        for date, activities in activities_dict.items():
            self.daily_activities[date] = activities
            self.day_counter += 1

    ########################################################################################## 
    # FOR SUMMARIZATION
    ########################################################################################## 
    def summarize_day(self, date: str):
        """
        Summarizes the activities of a specific day using GPT model.
        date: The date of the activities to be summarized.
        """
        #retrieve the activities for each date and then converts the activties to a json string format for input to the LLM
        activities = self.daily_activities.get(date, [])
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
            
        # get the summary text from the response and store it in the summaries dictionary  
        summary = response['choices'][0]['message']['content'].strip()
        self.summaries[date] = summary
        # initalize the memory access counter for the date
        self.memory_access_counter[date] = 0
        # return summary


    def summarize_week(self, end_date: str):
        """
        Summarizes the activities of a specific week using GPT model.
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
            if date in self.summaries:
                input_weekly_summary.append(self.summaries[date])

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
        self.weekly_summaries[week_number] = weekly_summary

    
    def summarize_month(self, end_date: str):
        """
        Summarizes the activities of a specific month using GPT model.
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
            if date_str in self.summaries:
                daywise_summaries[day_name].append(self.summaries[date_str])
            
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

                # formatted_response = response['choices'][0]['message']['content'].strip()
                # # Ensuring the first letter of the response is capitalized
                # monthly_summary[day] = formatted_response[0].upper() + formatted_response[1:]

        month_year = end_date_dt.strftime('%m-%Y')
        self.monthly_summaries[month_year] = monthly_summary
                           
    ########################################################################################## 
    # FOR RETRIEVAL
    ########################################################################################## 

    def retrieve_tasks_by_intention(self, intention: str):
        """
        Retrieves historical tasks based on a specific intention by searching through summaries.
        intention: The intention to search for in the summaries.
        returns a list of tuples containing the date and summary where the intention was found. Format will be List[Tuple[str, str]].
        """
        relevant_tasks = []
        for date, summary in self.summaries.items():
            if intention in summary:
                # Increase the access frequency of that date
                self.memory_access_counter[date] += 1
                relevant_tasks.append((date, summary)) 
        return relevant_tasks
    
    ##########################################################################################
    # FOR MEMORY DELETION
    ##########################################################################################
    def calculate_information_density(self, summary: str):
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
    
    def calculate_importance_score(self, date, summary):
        """
        Calculates the importance score based on recency, frequency, and information density.
        """
        frequency = self.memory_access_counter.get(date, 0)
        recency = (datetime.now() - datetime.strptime(date, '%d-%m-%Y')).days
        weighted_info_density = self.calculate_information_density(summary)

        # Normalizing the recency and frequency 
        max_recency = 90
        normalized_recency = 1 - min(recency / max_recency, 1) # it is (1 -) because the more recent memory should have higher score
        
        max_frequency = max(self.memory_access_counter.values(), default=0)  
        max_frequency = max(1, max_frequency)  # Ensure max_frequency is at least 1 to avoid division by zero
    
        
        normalized_frequency = min(frequency / max_frequency, 1)

        # Calculating the overall importance score for the memory
        importance_score = (normalized_frequency + normalized_recency + weighted_info_density) / 3

        return importance_score

    def deleting_memory(self):
        """
        Deletes the memory of the user based on the memory access threshold.
        """
        for date, summary in list(self.summaries.items()):
            # iterates over the summaries dictionary and deletes the low scoring daily summaries and daily activities
            importance_score = self.calculate_importance_score(date, summary)
            if importance_score < self.memory_threshold:
                del self.summaries[date]
                self.memory_access_counter.pop(date, None)
                if date in self.daily_activities:
                    self.daily_activities.pop(date, None)




# Testing the MemoryModule
if __name__ == "__main__":
    memory_module = MemoryModule()
    
    # Example activities for 7 days starting from today
    activities_dict = {
        "01-07-2024": [["go to sleep", "(00:00, 06:58)", "home"], ["eat breakfast", "(07:24, 08:00)", "home"], ["go to work", "(09:00, 12:00)", "unsw campus"], ["lunch", "(12:30, 13:00)"], ["meeting", "(13:30, 15:00)"]],
        "02-07-2024": [["go to sleep", "(00:00, 07:00)"], ["jogging", "(08:30, 09:30)"]],
        "03-07-2024": [["go to sleep", "(00:00, 06:45)"], ["eat breakfast", "(07:15, 07:45)"], ["office work", "(08:30, 12:00)"], ["lunch", "(12:30, 13:00)"]],
        "04-07-2024": [["go to sleep", "(00:00, 06:30)"], ["emails", "(08:00, 09:00)"], ["client call", "(11:30, 12:30)"], ["lunch", "(13:00, 13:30)"], ["project discussion", "(14:00, 16:00)"]],
        "05-07-2024": [["go to sleep", "(00:00, 07:15)"], ["marketing research", "(09:00, 11:00)"], ["brainstorming session", "(14:00, 16:00)"], ["report writing", "(16:30, 18:00)"]],
        "06-07-2024": [["go to sleep", "(00:00, 07:00)"], ["gardening", "(14:00, 16:00)"], ["dinner", "(18:00, 19:00)"]],
        "07-07-2024": [["go to sleep", "(00:00, 06:45)"], ["eat breakfast", "(07:15, 07:45)"], ["relaxing", "(08:00, 09:00)"], ["watch movie", "(10:00, 12:00)"], ["dinner", "(18:00, 19:00)"]]
    }

    # Storing activities and generating summaries for each day
    memory_module.store_daily_activities(activities_dict)
    for date in activities_dict.keys():
        memory_module.summarize_day(date)
        print(f"Summary for {date}: {memory_module.summaries[date]}") 
        print("\n")
        
        # Check if 7 days have passed to generate a weekly summary
        if memory_module.day_counter % 7 == 0:
            memory_module.summarize_week(date)

    # Check the generated weekly summary
    week_number = datetime.strptime("07-07-2024", '%d-%m-%Y').isocalendar()[1]
    print(f"Weekly summary for week {week_number}: {memory_module.weekly_summaries[week_number]}")
    print("\n")
    print("\n")
    
    # Example: Generating and checking the monthly summary
    end_date_str = "07-07-2024"  # Assume 7 days have passed
    memory_module.summarize_month(end_date_str)
    month_year = datetime.strptime(end_date_str, '%d-%m-%Y').strftime('%m-%Y')
    print(f"Monthly summary for {month_year}: {memory_module.monthly_summaries[month_year]}")
    print("\n")
    print("\n")
    
    # Example: Retrieving historical tasks based on intention
    intention = "eat breakfast"
    tasks = memory_module.retrieve_tasks_by_intention(intention)
    print(f"Historical tasks for intention '{intention}': {tasks}")
    
    # Example: Deleting less important information
    memory_module.deleting_memory()
    print(f"Summaries after deletion: {memory_module.summaries}")


