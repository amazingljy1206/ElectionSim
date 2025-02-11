import json
import string
import os
import argparse
from tqdm import tqdm
from utils import *
import random
import concurrent.futures

random.seed(2024)

letters = list(string.ascii_uppercase)  # 将选项添上易选的字母标识

PROMPT_WITH_EXP_2016 = '''
It’s 2016, and you’re being surveyed for the 2016 American National Election Studies. You are a real person living in !<INPUT 0>! with the following personal information. Please answer the following question as best as you can. You should act consistently with the role you are playing.  Do not select the option to refuse to answer.
Personal information: !<INPUT 1>!
Some of your historical comments on social media platforms: !<INPUT 2>!
Candidates Information: In the 2016 United States presidential election, the Republican ticket was led by Donald Trump, a businessman and television personality who had never held political office before. Trump's campaign focused on themes of nationalism and populism, with promises to build a wall on the U.S.-Mexico border and to "Make America Great Again." His running mate was Governor Mike Pence of Indiana. On the Democratic side, former Secretary of State Hillary Clinton was the nominee, with a long history in public service, including her tenure as a U.S. Senator from New York and as First Lady. Senator Tim Kaine from Virginia was her running mate. Clinton's campaign emphasized experience and a continuation of policies from the Obama administration, with a focus on issues such as economic growth, national security, and healthcare reform. The election was marked by a highly polarized political climate and intense scrutiny of both candidates.
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

YEAR_PROMPT_MAPPING = {
    "2016": PROMPT_WITH_EXP_2016
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
        # options随机打乱
        shuffled_indices = list(range(len(options)))
        random.shuffle(shuffled_indices)
        shuffled_options = [options[i] for i in shuffled_indices]
        shuffled_options_with_letters = [f"{letters[i]} {option}" for i, option in enumerate(shuffled_options)]
        options_desc = '\n'.join(shuffled_options_with_letters)
    
        prompt = YEAR_PROMPT_MAPPING[args.year]
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
    attributes = {key: agent.get(key) for key in ['AGE', 'GENDER', 'RACE', 'IDEOLOGY', 'PARTY']}
    # history = cut_down_max_tokens(agent['sample_content'])
    answer_log = {}
    for idx, poll in enumerate(polls):
        question_code = poll['code']
        question = poll['question']
        options = poll['options']
        options_code = poll['options_code']
        # options随机打乱
        shuffled_indices = list(range(len(options)))
        random.shuffle(shuffled_indices)
        shuffled_options = [options[i] for i in shuffled_indices]
        shuffled_options_with_letters = [f"{letters[i]} {option}" for i, option in enumerate(shuffled_options)]
        options_desc = '\n'.join(shuffled_options_with_letters)
    
        prompt = YEAR_PROMPT_MAPPING[args.year]
        # filling_input = [state_name, attributes, question, options_desc] # 其实写歪了，但是效果出奇得好
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
    
    # # 基于key_words完成筛选，并拼接成一段文本
    # history = select_history(agent['all_posts'], KEY_WORDS)
    # history = cut_down_max_tokens(history)
    
    answer_log = {}
    for idx, poll in enumerate(polls):
        question_code = poll['code']
        question = poll['question']
        options = poll['options']
        options_code = poll['options_code']
        # options随机打乱
        shuffled_indices = list(range(len(options)))
        random.shuffle(shuffled_indices)
        shuffled_options = [options[i] for i in shuffled_indices]
        shuffled_options_with_letters = [f"{letters[i]} {option}" for i, option in enumerate(shuffled_options)]
        options_desc = '\n'.join(shuffled_options_with_letters)
    
        prompt = YEAR_PROMPT_MAPPING[args.year]

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
        # options随机打乱
        shuffled_indices = list(range(len(options)))
        random.shuffle(shuffled_indices)
        shuffled_options = [options[i] for i in shuffled_indices]
        shuffled_options_with_letters = [f"{letters[i]} {option}" for i, option in enumerate(shuffled_options)]
        options_desc = '\n'.join(shuffled_options_with_letters)
    
        prompt = YEAR_PROMPT_MAPPING[args.year]
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
    
    # 基于key_words完成筛选，并拼接成一段文本
    history = select_history(agent['sample_content'], KEY_WORDS)
    history = cut_down_max_tokens_string_len(history)
    answer_log = {}
    for idx, poll in enumerate(polls):
        question_code = poll['code']
        question = poll['question']
        options = poll['options']
        options_code = poll['options_code']
        # options随机打乱
        shuffled_indices = list(range(len(options)))
        random.shuffle(shuffled_indices)
        shuffled_options = [options[i] for i in shuffled_indices]
        shuffled_options_with_letters = [f"{letters[i]} {option}" for i, option in enumerate(shuffled_options)]
        options_desc = '\n'.join(shuffled_options_with_letters)
    
        prompt = YEAR_PROMPT_MAPPING[args.year]
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
        if args.pattern == 31:
            agent_log = process_agent_baseline3_1(agent, polls, llm_config, args)
        elif args.pattern == 32:
            agent_log = process_agent_baseline3_2(agent, polls, llm_config, args)
        elif args.pattern == 33:
            agent_log = process_agent_baseline3_3(agent, polls, llm_config, args)
        elif args.pattern == 2:
            agent_log = process_agent_baseline2(agent, polls, llm_config, args)
        elif args.pattern == 1:
            agent_log = process_agent_baseline1(agent, polls, llm_config, args)
        else:
            raise Exception("Invalid pattern!")
        with open(output_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(agent_log, ensure_ascii=False))
            f.write('\n')
            f.flush()
    
# 新方法将剩余的块也进行平摊，减少了其他进程的等待时间
def split_file(input_path, num_chunks):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 计算基本块大小和剩余记录数
    total_records = len(data)
    chunk_size = total_records // num_chunks
    remainder = total_records % num_chunks
    
    chunks = []
    start = 0
    for i in range(num_chunks):
        # 分配基本块大小
        end = start + chunk_size
        # 如果还有剩余记录，则分配给当前块
        if i < remainder:
            end += 1
        # 添加当前块
        chunks.append(data[start:end])
        # 更新起始位置
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
    
    # 以下是模拟条件设置
    parser.add_argument("--pattern", type=int, default=31, choices=[1, 2, 31, 32, 33])
    parser.add_argument("--model", type=str, default='qwen', choices=['qwen', 'llama3', 'gpt4o_mini'])
    parser.add_argument("--state_name", type=str, default="Alabama")
    parser.add_argument("--year", type=str, default="2016")
    # 以下是输出路径和线程数设置
    parser.add_argument("--user_profile_folder", type=str, default="./user_profile")
    parser.add_argument("--poll_path", type=str, default="./poll.json")
    parser.add_argument("--output_path", type=str, default="./output")
    parser.add_argument("--final_output_file_name", type=str, default="final_output.jsonl")
    parser.add_argument("--num_threads", type=int, default=4)
    
    args = parser.parse_args()
    
    # 整理相关工作目录
    output_folder = os.path.join(args.output_path, args.state_name)
    final_output_path = os.path.join(output_folder, args.final_output_file_name)
    user_profile_path = os.path.join(args.user_profile_folder, args.state_name) + '.json'
    num_chunks = args.num_threads

    # 创建当前州工作目录
    os.makedirs(output_folder, exist_ok=True)

    # 分割原始文件
    chunks = split_file(user_profile_path, num_chunks)

    # 加载投票问题文件
    with open(args.poll_path, 'r', encoding='utf-8') as f:
        polls = json.load(f)
    
    # 加载模型config
    with open('config.json', 'r') as f:
        llm_configs = json.load(f)
        llm_config = llm_configs[args.model]

    # 并行处理每个子文件
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

    # 合并所有输出文件
    merge_files(output_folder, final_output_path, num_chunks)

    print("All tasks completed.")