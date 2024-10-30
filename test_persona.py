import json

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
    
    # Calculate and print the percentages for each age bracket and gender
    print("Age distribution by gender (percentage of total population):")
    for bracket, gender_count in age_gender_count.items():
        for gender, count in gender_count.items():
            percentage = (count / total_population) * 100
            print(f"Age {bracket[0]}-{bracket[1]} ({gender}): {percentage:.3f}%")
    
    # Calculate and print the average personality traits
    print("\nAverage personality attributes:")
    if personality_count > 0:
        for trait, total in personality_accumulator.items():
            avg_value = total / personality_count
            print(f"{trait}: {avg_value:.2f}")
    else:
        print("No personality data available.")

# Run the statistics calculation
f = open("output_persona.json")
data = json.load(f)
calculate_statistics(data)