from utils import *
import json
from tqdm import tqdm
import string
import random
random.seed(20240830)

persons = json.load(open('eval_profile.json'))
polls = json.load(open('polls_2016.json'))
letters = list(string.ascii_uppercase)
output_path = 'output/qwen.jsonl'
model = 'qwen'

with open('config.json', 'r') as f:
    llm_config = json.load(f)[model]

code_poll_mapping = {}
for item in polls:
    code_poll_mapping[item['code']] = item

prompt_direct = '''
###Instruction: It’s 2016, and you’re being surveyed for the 2016 American National Election Studies. You are a real person with the following personal information. Please answer the following question as best as you can. You should act consistently with the role you are playing. Do not select the option to refuse to answer.
###Personal information: !<INPUT 0>!
###Question: !<INPUT 1>!
###Options: !<INPUT 2>!
###You should give your answer (you only need to answer the option letter number) in JSON format as example below:
```json
{
    "answer": "A"
}
```
'''.strip()

prompt_summary = '''
Instruction: You are a very outstanding biographer. Now there is some information about a person. Please generate a description of his past experiences based on this information. Please return to this biography in the second person, with the sentence structure of "You are xxx".
Personal Information: !<INPUT 0>!
You should give your answer and reason in JSON format as below:
```json
{
    "biography": "biography generated here"
}
```
Answer:
'''.strip()

prompt_template = prompt_direct
for person in tqdm(persons):
    case_id = person['case_id']
    attributes = person['attributes']
    prompt = prompt_summary.replace(f"!<INPUT 0>!", str(attributes))
    attributes_desc = generate_and_parse(prompt, llm_config)['biography']# personal information
    questions_log = person['questions_log']
    questions_simu_log = {}
    for question_code, _ in questions_log.items():
        question = code_poll_mapping[question_code]["question"]
        options = code_poll_mapping[question_code]["options"]
        
        # shuffle indices
        shuffled_indices = list(range(len(options)))
        random.shuffle(shuffled_indices)


        shuffled_options = [options[i] for i in shuffled_indices] # shuffle
        shuffled_options_with_letters = [f"{letters[i]} {option}" for i, option in enumerate(shuffled_options)]
        options_desc = '\n'.join(shuffled_options_with_letters)
        
        options_code = code_poll_mapping[question_code]["options_code"]
        shuffled_options_code = [options_code[i] for i in shuffled_indices] # shuffle mapping

        prompt = prompt_template
        filling_input = [attributes_desc, question, options_desc]
        for i, content in enumerate(filling_input):
            prompt = prompt.replace(f"!<INPUT {i}>!", str(content))
        result = generate_and_parse(prompt, llm_config)
        try:
            questions_simu_log[question_code] = shuffled_options_code[letters.index(result["answer"])]
        except Exception as e:
            print(e)
            print(question_code)
            print(result)
            questions_simu_log[question_code] = -10086

    person['questions_simu_log'] = questions_simu_log
    with open(output_path, 'a') as f:
        f.write(json.dumps(person, ensure_ascii=False))
        f.write('\n')