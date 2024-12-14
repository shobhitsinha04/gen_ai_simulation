import json
from typing import Counter
import numpy as np

from scipy.spatial.distance import jensenshannon

# Kullback-Leibler Divergence for normal distributions
def kl_divergence(mu1, sigma1, mu2, sigma2):
    return np.log(sigma2 / sigma1) + (sigma1**2 + (mu1 - mu2)**2) / (2 * sigma2**2) - 0.5

# Jensen-Shannon Divergence (JSD) for two normal distributions
def jsd(mu1, sigma1, mu2, sigma2):
    # Calculate the average distribution (M)
    mu_m = (mu1 + mu2) / 2
    sigma_m = np.sqrt((sigma1**2 + sigma2**2) / 2)
    
    # Calculate KL divergences
    kl_p_m = kl_divergence(mu1, sigma1, mu_m, sigma_m)
    kl_q_m = kl_divergence(mu2, sigma2, mu_m, sigma_m)
    
    # Jensen-Shannon Divergence
    return 0.5 * (kl_p_m + kl_q_m)

# Calculate mean and std for each personality trait
def calculate_stats(values):
    mean = np.mean(values)
    std = np.std(values)
    return mean, std

# Initialize lists to store personality trait values
ext_values = []
agr_values = []
con_values = []
neu_values = []
ope_values = []

# Load the data from the JSON file
# with open('../res/personas.json', 'r') as file:
#     data = json.load(file)

with open('persona_eval/llama_persona.json', 'r') as file:
    data = json.load(file)

# Extract the personality traits for each person
for person in data:
    personality = person.get("personality", {})
    ext_values.append(personality.get("ext", 0))
    agr_values.append(personality.get("agr", 0))
    con_values.append(personality.get("con", 0))
    neu_values.append(personality.get("neu", 0))
    ope_values.append(personality.get("ope", 0))

# Calculate and display results
ext_mean, ext_std = calculate_stats(ext_values)
agr_mean, agr_std = calculate_stats(agr_values)
con_mean, con_std = calculate_stats(con_values)
neu_mean, neu_std = calculate_stats(neu_values)
ope_mean, ope_std = calculate_stats(ope_values)

# Print results
print(f"Extraversion (ext): Mean = {ext_mean}, Std = {ext_std}")
print(f"Agreeableness (agr): Mean = {agr_mean}, Std = {agr_std}")
print(f"Conscientiousness (con): Mean = {con_mean}, Std = {con_std}")
print(f"Neuroticism (neu): Mean = {neu_mean}, Std = {neu_std}")
print(f"Openness (ope): Mean = {ope_mean}, Std = {ope_std}")

# Calculate JSD
divergence = jsd(13.22, 1.99, ext_mean, ext_std)
print(f"ext: {divergence}")

divergence = jsd(14.05, 1.67, agr_mean, agr_std)
print(f"agr: {divergence}")

divergence = jsd(14.15, 1.95, con_mean, con_std)
print(f"con: {divergence}")

divergence = jsd(11.05, 2.29, neu_mean, neu_std)
print(f"neu: {divergence}")

divergence = jsd(13.59, 1.59, ope_mean, ope_std)
print(f"ope: {divergence}")

# # Load the data from the JSON file
# with open('../res/personas.json', 'r') as file:
#     data = json.load(file)

print(f"ope: {len(ext_values)}")



############## Occupation ###############
##                +  +                 ##
##                 --                  ##
#########################################

# Initialize counters
male_count = female_count = 0
male_unemployed_or_retiree = female_unemployed_or_retiree = 0

occupation_counts = Counter()
total_employee = 0

# Iterate through the data
for person in data:
    occupation = person["occupation"]
    if occupation not in ["unemployed", "retiree", 'student']:
        occupation_counts[occupation] += 1
        total_employee += 1

    if person['gender'] == 'male':
        male_count += 1
        if person['occupation'] in ['unemployed', 'retiree', 'student']:
            male_unemployed_or_retiree += 1
    elif person['gender'] == 'female':
        female_count += 1
        if person['occupation'] in ['unemployed', 'retiree', 'student']:
            female_unemployed_or_retiree += 1

# Calculate percentages
male_percentage = (male_unemployed_or_retiree / male_count * 100) if male_count > 0 else 0
female_percentage = (female_unemployed_or_retiree / female_count * 100) if female_count > 0 else 0

# Print results
print(f"Percentage of unemployed/retiree males: {male_percentage:.2f}%")
print(f"Percentage of unemployed/retiree females: {female_percentage:.2f}%")


# Calculate percentages
industry_percentages = {
    industry: (count / total_employee) * 100
    for industry, count in occupation_counts.items()
}

# # Print results
# print("Percentage of people in each industry (excluding unemployed/retiree):")
# for industry, percentage in industry_percentages.items():
#     print(f"{industry}: {percentage:.2f}%")

expected = {
    "Agriculture and forestry": 205,
    "Fisheries": 7,
    "Mining and quarrying of stone and gravel": 10,
    "Construction": 4014,
    "Manufacturing": 7479,
    "Electricity, gas, heat supply and water": 346,
    "Information and communications": 10491,
    "Transport and postal activities":3507,
    "Wholesale and retail trade": 11527,
    "Finance and insurance": 3397,
    "Real estate and goods rental and leasing": 3263,
    "Scientific research, professional and technical services": 6118,
    "Accommodations, eating and drinking services": 4333,
    "Living-related and personal services and amusement services": 2664,
    "Education, learning support": 4261,
    "Medical, health care and welfare": 8843,
    "Compound services": 239,
    "Services, N.E.C.": 7112,
    "Government, except elsewhere classified": 2735,
    "Other industries": 2418
}

# Normalize the expected data to percentages
total_count = sum(expected.values())
expected_percentages = {k: (v / total_count) * 100 for k, v in expected.items()}

# Align categories (fill missing categories with 0 in either dataset)
all_categories = set(expected_percentages.keys()).union(set(industry_percentages.keys()))
expected_vector = np.array([expected_percentages.get(cat, 0) for cat in all_categories])
output_vector = np.array([industry_percentages.get(cat, 0) for cat in all_categories])

# Normalize the vectors to probabilities for JSD
expected_prob = expected_vector / expected_vector.sum()
output_prob = output_vector / output_vector.sum()

jsd = jensenshannon(expected_prob, output_prob)

print("Jsd for Occupation:", jsd)

# # Category-wise Absolute Difference
# abs_differences = {cat: abs(expected_percentages.get(cat, 0) - industry_percentages.get(cat, 0)) for cat in all_categories}
# print("\nCategory-wise absolute differences:")
# for cat, diff in abs_differences.items():
#     print(f"{cat}: {diff:.2f}%")