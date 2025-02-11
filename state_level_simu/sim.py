import json
import string
import os
import argparse
from tqdm import tqdm
from utils import *
import random
import concurrent.futures

random.seed(2024)

letters = list(string.ascii_uppercase) 

PROMPT_WITH_EXP_2020 = '''
It’s 2020, and you’re being surveyed for the 2020 American National Election Studies. You are a real person living in !<INPUT 0>! with the following personal information. Please answer the following question as best as you can. You should act consistently with the role you are playing.  Do not select the option to refuse to answer.
Personal information: !<INPUT 1>!
Some of your historical comments on social media platforms: !<INPUT 2>!
Candidates Information: In the 2020 United States presidential election, the Republican ticket is led by incumbent President Donald Trump, who is known for his assertive communication style and strict immigration policies. Trump is focusing on economic management and a tough stance on law and order, reflecting his commitment to his "America First" approach. His running mate is Vice President Mike Pence. On the Democratic side, former Vice President Joe Biden is the nominee, with Senator Kamala Harris from California as his running mate. Harris is the first African-American, first Asian-American, and third female vice presidential nominee on a major party ticket. Biden's campaign emphasizes unity and healing, with a focus on addressing the public health and economic impacts of the ongoing COVID-19 pandemic, civil unrest following the killing of George Floyd, the future of the Affordable Care Act, and the composition of the U.S. Supreme Court.
Question: !<INPUT 3>!
Options: !<INPUT 4>!
You should give your answer (you only need to answer the option letter number) in JSON format as example below:
```json
{
    "answer": "A"
}
```
Answer:
'''.strip()

PROMPT_WITH_EXP_2020_NO_CAN = '''
It’s 2020, and you’re being surveyed for the 2020 American National Election Studies. You are a real person living in !<INPUT 0>! with the following personal information. Please answer the following question as best as you can. You should act consistently with the role you are playing.  Do not select the option to refuse to answer.
Personal information: !<INPUT 1>!
Some of your historical comments on social media platforms: !<INPUT 2>!
Question: !<INPUT 3>!
Options: !<INPUT 4>!
You should give your answer (you only need to answer the option letter number) in JSON format as example below:
```json
{
    "answer": "A"
}
```
Answer:
'''.strip()

PROMPT_WITH_EXP_2024 = '''
It’s 2024, and you’re being surveyed for the 2024 American National Election Studies. You are a real person living in !<INPUT 0>! with the following personal information. Please answer the following question as best as you can. You should act consistently with the role you are playing.  Do not select the option to refuse to answer.
Personal information: !<INPUT 1>!
Some of your historical comments on social media platforms: !<INPUT 2>!
Candidates Information: Donald Trump, the former President of the United States and a prominent figure in the Republican Party, is running for the 2024 Presidential Election. Known for his assertive communication style and stringent immigration policies, Trump has promised to implement even more restrictive measures against illegal immigration if re-elected. He is also advocating for comprehensive tariffs on foreign goods, aiming to protect American industries, although this could lead to increased consumer prices. Trump's campaign emphasizes economic nationalism and a return to his "America First" approach to governance. Kamala Harris, the current Vice President of the United States and a key member of the Democratic Party, is seeking the presidency in the upcoming election. As a former prosecutor and attorney general, Harris brings a strong background in law and justice to her campaign. She is focusing on issues such as reducing child poverty, supporting labor unions, ensuring affordable healthcare, and advocating for paid family leave. Harris is also a proponent of voting rights legislation, gun control measures, and reproductive rights. Her vice presidency has seen her engage with voting reforms, immigration policies, and efforts to protect and expand access to abortion services.
Question: !<INPUT 3>!
Options: !<INPUT 4>!
You should give your answer (you only need to answer the option letter number) in JSON format as example below:
```json
{
    "answer": "A"
}
```
Answer:
'''.strip()

PROMPT_WITH_EXP_2024_NO_CAN = '''
It’s 2024, and you’re being surveyed for the 2024 American National Election Studies. You are a real person living in !<INPUT 0>! with the following personal information. Please answer the following question as best as you can. You should act consistently with the role you are playing.  Do not select the option to refuse to answer.
Personal information: !<INPUT 1>!
Some of your historical comments on social media platforms: !<INPUT 2>!
Question: !<INPUT 3>!
Options: !<INPUT 4>!
You should give your answer (you only need to answer the option letter number) in JSON format as example below:
```json
{
    "answer": "A"
}
```
Answer:
'''.strip()

PROMPT_COUNTERFACT_CANDIDATE = '''
It’s 2024, and you’re being surveyed for the 2024 American National Election Studies. You are a real person living in !<INPUT 0>! with the following personal information. Please answer the following question as best as you can. You should act consistently with the role you are playing.  Do not select the option to refuse to answer.
Personal information: !<INPUT 1>!
Some of your historical comments on social media platforms: !<INPUT 2>!
Candidates Information: Kamala Harris, the former President of the United States and a prominent figure in the Republican Party, is running for the 2024 Presidential Election. Known for her assertive communication style and stringent immigration policies, Harris has promised to implement even more restrictive measures against illegal immigration if re-elected. She is also advocating for comprehensive tariffs on foreign goods, aiming to protect American industries, although this could lead to increased consumer prices. Harris's campaign emphasizes economic nationalism and a return to her "America First" approach to governance. Donald Trump, the current Vice President of the United States and a key member of the Democratic Party, is seeking the presidency in the upcoming election. As a former prosecutor and attorney general, Trump brings a strong background in law and justice to his campaign. He is focusing on issues such as reducing child poverty, supporting labor unions, ensuring affordable healthcare, and advocating for paid family leave. Trump is also a proponent of voting rights legislation, gun control measures, and reproductive rights. His vice presidency has seen him engage with voting reforms, immigration policies, and efforts to protect and expand access to abortion services.
Question: !<INPUT 3>!
Options: !<INPUT 4>!
You should give your answer (you only need to answer the option letter number) in JSON format as example below:
```json
{
    "answer": "A"
}
```
Answer:
'''.strip()

PROMPT_COUNTERFACT_PARTISANSHIP = '''
It’s 2024, and you’re being surveyed for the 2024 American National Election Studies. You are a real person living in !<INPUT 0>! with the following personal information. Please answer the following question as best as you can. You should act consistently with the role you are playing.  Do not select the option to refuse to answer.
Personal information: !<INPUT 1>!
Some of your historical comments on social media platforms: !<INPUT 2>!
Candidates Information: Donald Trump, the former President of the United States and a key member of the Democratic Party, is running for the 2024 Presidential Election. Known for his assertive communication style and stringent immigration policies, Trump has promised to implement even more restrictive measures against illegal immigration if re-elected. He is also advocating for comprehensive tariffs on foreign goods, aiming to protect American industries, although this could lead to increased consumer prices. Trump's campaign emphasizes economic nationalism and a return to his "America First" approach to governance. Kamala Harris, the current Vice President of the United States and a prominent figure in the Republican Party, is seeking the presidency in the upcoming election. As a former prosecutor and attorney general, Harris brings a strong background in law and justice to her campaign. She is focusing on issues such as reducing child poverty, supporting labor unions, ensuring affordable healthcare, and advocating for paid family leave. Harris is also a proponent of voting rights legislation, gun control measures, and reproductive rights. Her vice presidency has seen her engage with voting reforms, immigration policies, and efforts to protect and expand access to abortion services.
Question: !<INPUT 3>!
Options: !<INPUT 4>!
You should give your answer (you only need to answer the option letter number) in JSON format as example below:
```json
{
    "answer": "A"
}
```
Answer:
'''.strip()

PROMPT_COUNTERFACT_POLICY = '''
It’s 2024, and you’re being surveyed for the 2024 American National Election Studies. You are a real person living in !<INPUT 0>! with the following personal information. Please answer the following question as best as you can. You should act consistently with the role you are playing.  Do not select the option to refuse to answer.
Personal information: !<INPUT 1>!
Some of your historical comments on social media platforms: !<INPUT 2>!
Candidates Information: Donald Trump, the former President of the United States and a prominent figure in the Republican Party, is running for the 2024 Presidential Election. Known for his assertive communication style, Trump is focusing on issues such as reducing child poverty, supporting labor unions, ensuring affordable healthcare, and advocating for paid family leave. He is also a proponent of voting rights legislation, gun control measures, and reproductive rights. Trump's campaign has seen him engage with voting reforms, immigration policies, and efforts to protect and expand access to abortion services. Kamala Harris, the current Vice President of the United States and a key member of the Democratic Party, is seeking the presidency in the upcoming election. Known for her stringent immigration policies, Harris has promised to implement even more restrictive measures against illegal immigration if re-elected. She is also advocating for comprehensive tariffs on foreign goods, aiming to protect American industries, although this could lead to increased consumer prices. Harris's campaign emphasizes economic nationalism and a return to her "America First" approach to governance.
Question: !<INPUT 3>!
Options: !<INPUT 4>!
You should give your answer (you only need to answer the option letter number) in JSON format as example below:
```json
{
    "answer": "A"
}
```
Answer:
'''.strip()

PROMPT_SUMMARY = '''
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

PATTERN_PROMPT_MAPPING = {
    "2020": PROMPT_WITH_EXP_2020,
    "2020_no_can": PROMPT_WITH_EXP_2020_NO_CAN,
    "2024": PROMPT_WITH_EXP_2024,
    "2024_no_can": PROMPT_WITH_EXP_2024_NO_CAN,
    "2024_counterfact_candidate": PROMPT_COUNTERFACT_CANDIDATE,
    "2024_counterfact_partisanship": PROMPT_COUNTERFACT_PARTISANSHIP,
    "2024_counterfact_policy": PROMPT_COUNTERFACT_POLICY
}

def cut_down_max_tokens(text, max_tokens=1024):
    text = clean_string(text)
    words = text.split()
    return ' '.join(words[:max_tokens])

def cut_down_max_tokens_string_len(text, max_tokens=1024):
    text = clean_string(text)
    return text[:max_tokens]

'''
Baseline 1: direct
'''
def process_agent_baseline1(agent, polls, llm_config, args):
    user_id = agent['user_id']
    attributes = {key: agent.get(key) for key in ['AGE', 'GENDER', 'RACE', 'IDEOLOGY', 'PARTY', 'AREA']}
    # history = cut_down_max_tokens(agent['sample_content'])
    answer_log = {}
    for idx, poll in enumerate(polls):
        question_code = poll['code']
        question = poll['question']
        options = poll['options']
        options_code = poll['options_code']
        # options random shuffle
        shuffled_indices = list(range(len(options)))
        random.shuffle(shuffled_indices)
        shuffled_options = [options[i] for i in shuffled_indices]
        shuffled_options_with_letters = [f"{letters[i]} {option}" for i, option in enumerate(shuffled_options)]
        options_desc = '\n'.join(shuffled_options_with_letters)
    
        prompt = PATTERN_PROMPT_MAPPING[args.pattern]
        filling_input = [attributes, question, options_desc]
        for i, content in enumerate(filling_input):
            prompt = prompt.replace(f"!<INPUT {i}>!", str(content))
        llm_config['max_tokens'] = 32
        result = generate_and_parse(prompt, llm_config)
        try:
            answer_log[question_code] = options_code[shuffled_indices[letters.index(result['answer'])]]
        except Exception as e:
            # print(e)
            answer_log[question_code] = -10086
    return {'user_id': user_id, 'answer_log': answer_log}

'''
Baseline 2: demographic info + direct
'''
def process_agent_baseline2(agent, polls, llm_config, args):
    user_id = agent['user_id']
    state_name = args.state_name
    attributes = {key: agent.get(key) for key in ['AGE', 'GENDER', 'RACE', 'IDEOLOGY', 'PARTY', 'AREA']}
    # history = cut_down_max_tokens(agent['sample_content'])
    answer_log = {}
    for idx, poll in enumerate(polls):
        question_code = poll['code']
        question = poll['question']
        options = poll['options']
        options_code = poll['options_code']
        # options random shuffle
        shuffled_indices = list(range(len(options)))
        random.shuffle(shuffled_indices)
        shuffled_options = [options[i] for i in shuffled_indices]
        shuffled_options_with_letters = [f"{letters[i]} {option}" for i, option in enumerate(shuffled_options)]
        options_desc = '\n'.join(shuffled_options_with_letters)
    
        prompt = PATTERN_PROMPT_MAPPING[args.pattern]
        filling_input = [state_name, attributes, 'None', question, options_desc]
        for i, content in enumerate(filling_input):
            prompt = prompt.replace(f"!<INPUT {i}>!", str(content))
        llm_config['max_tokens'] = 32
        result = generate_and_parse(prompt, llm_config)
        try:
            answer_log[question_code] = options_code[shuffled_indices[letters.index(result['answer'])]]
        except Exception as e:
            # print(e)
            answer_log[question_code] = -10086
    return {'user_id': user_id, 'answer_log': answer_log, 'prompt': prompt}

'''
Baseline 3.1: demographic info + user_exp + direct
'''
def process_agent_baseline3_1(agent, polls, llm_config, args):
    user_id = agent['user_id']
    state_name = args.state_name
    attributes = {key: agent.get(key) for key in ['AGE', 'GENDER', 'RACE', 'IDEOLOGY', 'PARTY', 'AREA']}
    history = cut_down_max_tokens_string_len(agent['sample_content'])

    # history = select_history(agent['all_posts'], KEY_WORDS)
    # history = cut_down_max_tokens(history)
    
    answer_log = {}
    for idx, poll in enumerate(polls):
        question_code = poll['code']
        question = poll['question']
        options = poll['options']
        options_code = poll['options_code']
        # options random shuffle
        shuffled_indices = list(range(len(options)))
        random.shuffle(shuffled_indices)
        shuffled_options = [options[i] for i in shuffled_indices]
        shuffled_options_with_letters = [f"{letters[i]} {option}" for i, option in enumerate(shuffled_options)]
        options_desc = '\n'.join(shuffled_options_with_letters)
    
        prompt = PATTERN_PROMPT_MAPPING[args.pattern]

        filling_input = [state_name, attributes, history, question, options_desc]
        for i, content in enumerate(filling_input):
            prompt = prompt.replace(f"!<INPUT {i}>!", str(content))
        llm_config['max_tokens'] = 32
        result = generate_and_parse(prompt, llm_config)
        try:
            answer_log[question_code] = options_code[shuffled_indices[letters.index(result['answer'])]]
        except Exception as e:
            # print(e)
            answer_log[question_code] = -10086
    return {'user_id': user_id, 'answer_log': answer_log}

'''
Baseline 3.2: demographic info + user_exp + biography
'''
def process_agent_baseline3_2(agent, polls, llm_config, args):
    user_id = agent['user_id']
    state_name = args.state_name
    attributes = {key: agent.get(key) for key in ['AGE', 'GENDER', 'RACE', 'IDEOLOGY', 'PARTY', 'AREA']}
    prompt = PROMPT_SUMMARY.replace(f"!<INPUT 0>!", str(attributes))
    try:
        llm_config['max_tokens'] = 1024
        attributes_desc = generate_and_parse(prompt, llm_config)['biography']
    except:
        attributes_desc = str(attributes)
    history = cut_down_max_tokens_string_len(agent['sample_content'])
    answer_log = {}
    for idx, poll in enumerate(polls):
        question_code = poll['code']
        question = poll['question']
        options = poll['options']
        options_code = poll['options_code']
        # options random shuffle
        shuffled_indices = list(range(len(options)))
        random.shuffle(shuffled_indices)
        shuffled_options = [options[i] for i in shuffled_indices]
        shuffled_options_with_letters = [f"{letters[i]} {option}" for i, option in enumerate(shuffled_options)]
        options_desc = '\n'.join(shuffled_options_with_letters)
    
        prompt = PATTERN_PROMPT_MAPPING[args.pattern]
        filling_input = [state_name, attributes_desc, history, question, options_desc]
        for i, content in enumerate(filling_input):
            prompt = prompt.replace(f"!<INPUT {i}>!", str(content))
        llm_config['max_tokens'] = 32
        result = generate_and_parse(prompt, llm_config)
        try:
            answer_log[question_code] = options_code[shuffled_indices[letters.index(result['answer'])]]
        except Exception as e:
            # print(e)
            answer_log[question_code] = -10086
            if result == 'failed':
                print(llm_generate(prompt, llm_config))
    return {'user_id': user_id, 'answer_log': answer_log, 'attributes_desc': attributes_desc}

'''
Baseline 3.3 (Need #ALL_POSTS#): demographic info + user_exp (select) + direct
'''
# KEY_WORDS = ['harris', 'trump', 'election', 'president', 'politics', 'democratic party', 'republican party'] # for 2024
KEY_WORDS = ['biden', 'trump', 'election', 'president', 'politics', 'democratic party', 'republican party'] # for 2020
def process_agent_baseline3_3(agent, polls, llm_config, args):
    user_id = agent['user_id']
    state_name = args.state_name
    attributes = {key: agent.get(key) for key in ['AGE', 'GENDER', 'RACE', 'IDEOLOGY', 'PARTY', 'AREA']}
    # prompt = PROMPT_SUMMARY.replace(f"!<INPUT 0>!", str(attributes))
    # try:
    #     llm_config['max_tokens'] = 1024
    #     attributes_desc = generate_and_parse(prompt, llm_config)['biography']
    # except:
    #     attributes_desc = str(attributes)
    attributes_desc = str(attributes)
    
    # key words filter
    history = select_history(agent['sample_content'], KEY_WORDS)
    history = cut_down_max_tokens_string_len(history)
    answer_log = {}
    for idx, poll in enumerate(polls):
        question_code = poll['code']
        question = poll['question']
        options = poll['options']
        options_code = poll['options_code']
        # options random shuffle
        shuffled_indices = list(range(len(options)))
        random.shuffle(shuffled_indices)
        shuffled_options = [options[i] for i in shuffled_indices]
        shuffled_options_with_letters = [f"{letters[i]} {option}" for i, option in enumerate(shuffled_options)]
        options_desc = '\n'.join(shuffled_options_with_letters)
    
        prompt = PATTERN_PROMPT_MAPPING[args.pattern]
        filling_input = [state_name, attributes_desc, history, question, options_desc]
        for i, content in enumerate(filling_input):
            prompt = prompt.replace(f"!<INPUT {i}>!", str(content))
        llm_config['max_tokens'] = 32
        result = generate_and_parse(prompt, llm_config)
        try:
            answer_log[question_code] = options_code[shuffled_indices[letters.index(result['answer'])]]
        except Exception as e:
            # print(e)
            answer_log[question_code] = -10086
            if result == 'failed':
                print(llm_generate(prompt, llm_config))
    return {'user_id': user_id, 'answer_log': answer_log, 'attributes_desc': attributes_desc}

def process_chunk(chunk, chunk_index, polls, output_folder, llm_config, args):
    output_path = os.path.join(output_folder, f"{chunk_index + 1}.jsonl")
    for agent in tqdm(chunk):
        if args.baseline == 31:
            agent_log = process_agent_baseline3_1(agent, polls, llm_config, args)
        elif args.baseline == 32:
            agent_log = process_agent_baseline3_2(agent, polls, llm_config, args)
        elif args.baseline == 33:
            agent_log = process_agent_baseline3_3(agent, polls, llm_config, args)
        elif args.baseline == 2:
            agent_log = process_agent_baseline2(agent, polls, llm_config, args)
        elif args.baseline == 1:
            agent_log = process_agent_baseline1(agent, polls, llm_config, args)
        else:
            raise Exception("Invalid pattern!")
        with open(output_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(agent_log, ensure_ascii=False))
            f.write('\n')
            f.flush()

def split_file(input_path, num_chunks):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_records = len(data)
    chunk_size = total_records // num_chunks
    remainder = total_records % num_chunks
    
    chunks = []
    start = 0
    for i in range(num_chunks):
        end = start + chunk_size
        if i < remainder:
            end += 1
        chunks.append(data[start:end])
        start = end
    return chunks

def merge_files(output_folder, final_output_path, num_chunks):
    with open(final_output_path, 'w', encoding='utf-8') as fout:
        for i in range(1, num_chunks + 1):
            input_path = os.path.join(output_folder, f"{i}.jsonl")
            try:
                with open(input_path, 'r', encoding='utf-8') as fin:
                    for line in fin:
                        fout.write(line)
            except FileNotFoundError:
                continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    # simulation setting
    parser.add_argument("--baseline", type=int, default=33, choices=[1, 2, 31, 32, 33])
    parser.add_argument("--model", type=str, default='qwen', choices=['qwen', 'llama3', 'gpt4o_mini'])
    parser.add_argument("--pattern", type=str, default="2020")
    parser.add_argument("--state_name", type=str, default="Alabama")
    
    # environment and hyper-params setting
    parser.add_argument("--user_profile_folder", type=str, default="./user_profile")
    parser.add_argument("--poll_path", type=str, default="./poll.json")
    parser.add_argument("--output_path", type=str, default="./output")
    parser.add_argument("--final_output_file_name", type=str, default="final_output.jsonl")
    parser.add_argument("--num_threads", type=int, default=4)
    
    args = parser.parse_args()
    
    output_folder = os.path.join(args.output_path, args.state_name)
    final_output_path = os.path.join(output_folder, args.final_output_file_name)
    user_profile_path = os.path.join(args.user_profile_folder, args.state_name) + '.json'
    num_chunks = args.num_threads

    os.makedirs(output_folder, exist_ok=True)

    chunks = split_file(user_profile_path, num_chunks)

    # loading poll
    with open(args.poll_path, 'r', encoding='utf-8') as f:
        polls = json.load(f)
    
    # loading llm config
    with open('config.json', 'r') as f:
        llm_configs = json.load(f)
        llm_config = llm_configs[args.model]

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_chunks) as executor:
        futures = [
            executor.submit(process_chunk, chunk, i, polls, output_folder, llm_config, args)
            for i, chunk in enumerate(chunks)
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"An exception occurred: {e}")

    # merge outputs
    merge_files(output_folder, final_output_path, num_chunks)

    print("All tasks completed.")