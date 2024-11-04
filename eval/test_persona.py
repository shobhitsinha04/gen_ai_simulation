import json
from scipy.spatial.distance import jensenshannon
import numpy as np

# Define the age brackets
age_brackets = [(i, i + 4) for i in range(0, 85, 5)]
age_brackets.append((85, 120))

def find_age_bracket(age):
    for bracket in age_brackets:
        if bracket[0] <= age <= bracket[1]:
            return bracket
    return None

# Function to calculate percentage and personality averages
def calculate_statistics(data):
    total_population = len(data)
    print("Total Population is {}.".format(total_population))
    
    # Initialize counters and accumulators
    age_gender_count = {}
    personality_accumulator = {'ext': 0, 'agr': 0, 'con': 0, 'neu': 0, 'ope': 0}
    personality_count = 0
    
    # Initialize age bracket count structure
    for bracket in age_brackets:
        age_gender_count[bracket] = {'male': 0, 'female': 0}
    
    # Iterate through the data to accumulate values
    for person in data:
        age_bracket = find_age_bracket(person['age'])
        if age_bracket:
            age_gender_count[age_bracket][person['gender']] += 1
        
        # Accumulate personality attributes
        personality = person.get('personality', None)
        if personality:
            for trait in personality:
                personality_accumulator[trait] += personality[trait]
            personality_count += 1
    
    age_gender_distribution = []
    # Calculate and print the percentages for each age bracket and gender
    print("Age distribution by gender (percentage of total population):")
    for bracket, gender_count in age_gender_count.items():
        gen_dic = {}
        for gender, count in gender_count.items():
            percentage = (count / total_population) * 100
            print(f"Age {bracket[0]}-{bracket[1]} ({gender}): {percentage:.3f}%")
            gen_dic[gender] = round(percentage, 3)
        
        age_gender_distribution.append(gen_dic)
    
    # Calculate and print the average personality traits
    print("\nAverage personality attributes:")
    if personality_count > 0:
        for trait, total in personality_accumulator.items():
            avg_value = total / personality_count
            print(f"{trait}: {avg_value:.2f}")
    else:
        print("No personality data available.")
    
    return age_gender_distribution

def jsd(data):
    # Sample expected data for male proportions in each age group
    expected_data = [
        {"male": 1.896, "female": 1.813}, 
        {"male": 1.936, "female": 1.850}, 
        {"male": 1.876, "female": 1.783}, 
        {"male": 1.966, "female": 1.907}, 
        {"male": 2.826, "female": 2.861}, 
        {"male": 3.244, "female": 3.248}, 
        {"male": 3.289, "female": 3.242}, 
        {"male": 3.542, "female": 3.418}, 
        {"male": 3.748, "female": 3.634}, 
        {"male": 4.140, "female": 4.082}, 
        {"male": 3.773, "female": 3.632}, 
        {"male": 3.189, "female": 3.016}, 
        {"male": 2.486, "female": 2.427}, 
        {"male": 2.383, "female": 2.445}, 
        {"male": 2.640, "female": 2.943}, 
        {"male": 1.963, "female": 2.52}, 
        {"male": 1.388, "female": 2.065}, 
        {"male": 1.207, "female": 2.568}
    ]

    print(data)

    # Extract male ratios from each age group
    expected_male_ratios = np.array([group["male"] for group in expected_data])
    output_male_ratios = np.array([group["male"] for group in data])

    # Extract female ratios from each age group
    expected_female_ratios = np.array([group["female"] for group in expected_data])
    output_female_ratios = np.array([group["female"] for group in data])

    # Ensure distributions sum to 1 (if not already)
    expected_male_ratios /= expected_male_ratios.sum()
    output_male_ratios /= output_male_ratios.sum()

    # Ensure distributions sum to 1 (if not already)
    expected_female_ratios /= expected_female_ratios.sum()
    output_female_ratios /= output_female_ratios.sum()

    # Calculate JSD
    jsd_male = jensenshannon(expected_male_ratios, output_male_ratios)
    jsd_female = jensenshannon(expected_female_ratios, output_female_ratios)

    print(f"Jensen-Shannon Divergence (male): {jsd_male:.4f}")
    print(f"Jensen-Shannon Divergence (male): {jsd_female:.4f}")
    return [round(jsd_male, 4), round(jsd_female, 4)]

# Run the statistics calculation
f = open("output_persona.json")
data = json.load(f)
res = calculate_statistics(data)
jsd(res)