from llm_sdk import Small_LLM_Model

model = Small_LLM_Model()

prompt = "waddup"
input_ids = model.encode(prompt)[0].tolist()

for _ in range(10):
    logits = model.get_logits_from_input_ids(input_ids)
    next_id = max(range(len(logits)), key=lambda i: logits[i])
    input_ids.append(next_id)
    print(model.decode(next_id))


print(model.decode(input_ids))
