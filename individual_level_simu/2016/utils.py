from openai import OpenAI
import json
import re

def extract_json_from_text(text):
    try:
        json_object = json.loads(text)
        return [json_object]
    except:
        pass    
    # 定义正则表达式模式
    pattern = r"```json(.*?)```"
    
    # 查找所有匹配项
    matches = re.findall(pattern, text, re.DOTALL)
    
    # 解析找到的 JSON 数据
    json_objects = []
    for match in matches:
        try:
            # 尝试解析 JSON
            json_data = json.loads(match.strip())
            json_objects.append(json_data)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {match}")
    
    return json_objects

def llm_generate(prompt, llm_config):
    client = OpenAI(api_key=llm_config['api_key'],
                    base_url=llm_config['api_base'])

    response = client.chat.completions.create(
    # model="claude-3-5-sonnet-20240620",
    # model="gpt-4o-2024-08-06",
    # model = "gpt-4o-mini-2024-07-18",
    model = llm_config['model'],
    max_tokens = llm_config['max_tokens'],
    temperature = llm_config['temperature'],
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ]
    )

    return response.choices[0].message.content

def generate_and_parse(prompt, llm_config):
    max_try = 0
    while(max_try < 6):
        try:
            response = llm_generate(prompt, llm_config)
            response = extract_json_from_text(response)[0]
            break
        except:
            # print(f'Retry {max_try}')
            max_try += 1
            if max_try == 6:
                response = 'failed'
    return response