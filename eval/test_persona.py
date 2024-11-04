import json
from scipy.spatial.distance import jensenshannon
import numpy as np
import random

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
            gen_dic[gender] = round(percentage, 3)
        
        print(f"[Age {bracket[0]}-{bracket[1]}] male: {gen_dic['male']:.3f}% | female: {gen_dic['female']:.3f}%")
        
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

def normalization(arr):
    combined_ratios = np.array([group["male"] + group["female"] for group in arr])
    male_ratios = np.array([group["male"] for group in arr])
    female_ratios = np.array([group["female"] for group in arr])
    combined_ratios /= combined_ratios.sum()
    male_ratios /= male_ratios.sum()
    female_ratios /= female_ratios.sum()

    return (combined_ratios, male_ratios, female_ratios)


def jsd(expected, data):
    expected_combined_ratios, expected_male_ratios, expected_female_ratios = normalization(expected)
    output_combined_ratios, output_male_ratios, output_female_ratios = normalization(data)

    # Calculate JSD
    jsd_combined = jensenshannon(expected_combined_ratios, output_combined_ratios)
    jsd_male = jensenshannon(expected_male_ratios, output_male_ratios)
    jsd_female = jensenshannon(expected_female_ratios, output_female_ratios)

    print(f"Jensen-Shannon Divergence (both): {jsd_combined:.4f}")
    print(f"Jensen-Shannon Divergence (male): {jsd_male:.4f}")
    print(f"Jensen-Shannon Divergence (female): {jsd_female:.4f}")
    return [round(jsd_combined, 4), round(jsd_male, 4), round(jsd_female, 4)]

def mape(expected, data):
    expected_combined_ratios, expected_male_ratios, expected_female_ratios = normalization(expected)
    output_combined_ratios, output_male_ratios, output_female_ratios = normalization(data)

    mape_combined = np.mean(np.abs((expected_combined_ratios - output_combined_ratios) / expected_combined_ratios)) * 100
    mape_male = np.mean(np.abs((expected_male_ratios - output_male_ratios) / expected_male_ratios)) * 100
    mape_female = np.mean(np.abs((expected_female_ratios - output_female_ratios) / expected_female_ratios)) * 100

    print(f"Mape (both): {mape_combined:.4f}")
    print(f"Mape (male): {mape_male:.4f}")
    print(f"Mape (female): {mape_female:.4f}")
    return mape_male, mape_female

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

# print('=== 1000 llama ===')
# f1 = open("llama_persona.json")
# data = json.load(f1)
# res = calculate_statistics(data)
# jsd(expected_data, res)
# mape(expected_data, res)

# # Output 100 personas
# gpt_samples = random.sample(data, 100)
# with open('../res/personas_llama.json','w') as f2:
#     json.dump(gpt_samples, f2)

print('\n=== 1000 gpt ===')
f3 = open("gpt_persona.json")
data = json.load(f3)
res = calculate_statistics(data)
jsd(expected_data, res)
mape(expected_data, res)

# # Output 100 personas
# gpt_samples = random.sample(data, 100)
# with open('../res/personas_gpt.json','w') as f4:
#     json.dump(gpt_samples, f4)


# print('\n=== 100 llama ===')
# f5 = open("../res/personas_llama.json")
# data = json.load(f5)
# res = calculate_statistics(data)
# jsd(expected_data, res)
# mape(expected_data, res)

print('\n=== 100 gpt ===')
f6 = open("../res/personas_gpt.json")
data = json.load(f6)
res = calculate_statistics(data)
jsd(expected_data, res)
mape(expected_data, res)