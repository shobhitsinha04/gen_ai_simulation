import random
import torch
import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
from mem_module_upgraded import MemoryModule
import openai

model_name = "/mnt/data728/datasets/meta-llama/Meta-Llama-3.1-8B-Instruct"
openai.api_key = ''

def llama_generate(context, msg):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": msg },
    ]

    input_ids = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    terminators = [
        tokenizer.eos_token_id,
        tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    outputs = model.generate(
        input_ids,
        max_new_tokens=512,
        eos_token_id=terminators,
        do_sample=True,
        temperature=1,
        top_p=0.8,
    )

    res = outputs[0][input_ids.shape[-1]:]
    return tokenizer.decode(res, skip_special_tokens=True)

def gpt_generate(context, msg):
    try: 
        res = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": msg}
            ],
            max_tokens=512,
        )
    except openai.OpenAIError as e:
        print(f"Error generating weekly summary: {e}")
        return

    return res['choices'][0]['message']['content'].strip()

def random_in_quad(v1, v2, v3, v4):
    while True:
        s, t = random.random(), random.random()
        if s + t <= 1:
            x = s * v1[0] + t * v2[0] + (1 - s - t) * v3[0]
            y = s * v1[1] + t * v2[1] + (1 - s - t) * v3[1]
            return (x, y)

def mem_retrieval(memory_module: MemoryModule, persona: int, date):
    # Monthly/weekly/daily summary memory (the day of the week + weekly + recent 3 days)
    try:
        monthly_mem = memory_module.monthly_summaries[persona][datetime.datetime.strptime(date, "%d-%m-%Y").strftime('%m-%Y')][weekday] # {'Monday': 'Summary', 'Tue'}
    except KeyError as e:
        print("Monthly Memory unavailable...")
        monthly_mem = ''

    try:
        weekly_mem = memory_module.weekly_summaries[persona][datetime.datetime.strptime(date, "%d-%m-%Y").isocalendar()[1]]
    except KeyError as e:
        print("Weekly Memory unavailable...")
        weekly_mem = ''

    try:
        daily_mem = ''
        for d in range(3):
            rec_day = (datetime.datetime.today() - datetime.timedelta(days=(d+1))).strftime("%d-%m-%Y")
            daily_mem += 'Daily routine summary for ' + rec_day + 'is: ' + memory_module.summaries[d][rec_day] + '. '
    except KeyError as e:
        print("Daily Memory: {}".format(daily_mem))

    return monthly_mem + weekly_mem + daily_mem