import random
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "/mnt/data728/datasets/meta-llama/Meta-Llama-3.1-8B-Instruct"

def llm_generate(context, msg):
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
        max_new_tokens=256,
        eos_token_id=terminators,
        do_sample=True,
        temperature=0.6,
        top_p=0.9,
    )

    res = outputs[0][input_ids.shape[-1]:]
    return tokenizer.decode(res, skip_special_tokens=True)

def gen_person_info(name, age, gender, occ, ext, arg, con, neu, ope):
    msg = """You are a person who lived in Sydney. You have the following personal infomation: name: {}, age: {}, gender: {}, occupation: {}. 
Your personality is determined based on the following 5 domains, where the full score of each domain is 24:
1. extraversion: {} scores, where people high in extraversion are outgoing and tend to gain energy in social situations. \
People who are low in domain are more introverted and tend to be more reserved. They have less energy to expend in social settings and social events can feel draining. 
2. agreeableness: {} scores, where people who are high in agreeableness tend to be more cooperative while those low in this personality trait tend to be more competitive and sometimes even manipulative.
3. conscientiousness: {} scores, where people with higher score for conscientiousness tend to be organized and mindful of details. \
People low in this domain is less structured and less organized. They may procrastinate to get things done, sometimes missing deadlines completely.
4. neuroticism: {} scores, where people who are high in neuroticism tend to experience mood swings, anxiety, irritability, and sadness. Those low in this personality trait tend to be more stable and emotionally resilient.
5. openness to experience: {} scores, where people with high score in openness tend to have a broad range of interests and be more adventurous and creative. \
Conversely, people low in this domain are often much more traditional and may struggle with abstract thinking.
""".format(name, age, gender, occ, ext, arg, con, neu, ope)
    return msg

def random_in_quad(v1, v2, v3, v4):
    while True:
        s, t = random.random(), random.random()
        if s + t <= 1:
            x = s * v1[0] + t * v2[0] + (1 - s - t) * v3[0]
            y = s * v1[1] + t * v2[1] + (1 - s - t) * v3[1]
            return (x, y)
