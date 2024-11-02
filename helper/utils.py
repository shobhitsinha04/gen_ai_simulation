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

def random_in_quad(v1, v2, v3, v4):
    while True:
        s, t = random.random(), random.random()
        if s + t <= 1:
            x = s * v1[0] + t * v2[0] + (1 - s - t) * v3[0]
            y = s * v1[1] + t * v2[1] + (1 - s - t) * v3[1]
            return (x, y)
