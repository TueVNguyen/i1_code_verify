from datasets import load_dataset
import requests
import json
import random
import re
from utils import _detect_callable_name

URL_DOCKER_SANDBOX = "http://localhost:5434"

def check_health():
    response = requests.get(f"{URL_DOCKER_SANDBOX}/v1/ping")
    print(response.json())
    if response.status_code != 200:
        raise Exception("Sandbox is not running")
    return True

if not check_health():
    raise Exception("Sandbox is not running please pull docker image and run docker server")


def code_oj_verify(llm_output, gt_output):
    value = json.loads(gt_output)
    test_cases = value['test_cases']
    language = value['language'] 
    # generate random id 
    id = random.randint(0, 1000000)
    row = {
        "id": id,
        "content": "optional: Problem description",
        "test": [
            {
                "input": {"stdin": test_cases[i]['input']},
                "output": {"stdout": test_cases[i]['output']}
            }
            for i in range(len(test_cases))
        ]
    }
    response = requests.post(f"{URL_DOCKER_SANDBOX}/submit", json={
        'dataset': 'custom_dataset_this_name_is_optional',
        'id': id,
        'config': {
            'dataset_type': 'CommonOJDataset',
            "language": language,
            'provided_data': row
        },
        'completion': llm_output,
    })
    total_passes = 0 
    for test in response.json()['tests']:  
        # print(test) 
        if test['passed']:
            total_passes += 1
        # else:
            # print(test)
    return total_passes/ len(test_cases)

def code_function_call_verify(llm_output, gt_output):
    HARNESS_CODE_METHOD = """{user_code}\nobj = {class_or_func}()\nmethod = getattr(obj, '{fn_name}')\nargs = {args}\nres = method(*args)\nprint(res)\n"""

    HARNESS_CODE_FUNCTION = """{user_code}\nmethod = {fn_name}\nargs = {args}\nres = method(*args)\nprint(res)\n"""
    code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", llm_output, re.DOTALL)
    if code_blocks:
        user_code = code_blocks[-1].strip()
    else:
        user_code = llm_output 
    injection = "from typing import List, Dict, Set, Tuple, Union, Optional\n"
    user_code = injection + user_code

    value = json.loads(gt_output)
    language = value['language'].lower()
    test_cases = value['test_cases']  
    total_passes = 0 
    assert language == 'python', "Only support python for now"
    for test in test_cases:  
        
        fn_name = test['fn_name']
        args = test['input']
        class_or_func, is_method = _detect_callable_name(user_code, fn_name)
        if class_or_func is None:
            continue 

        if is_method:
            harness_code = HARNESS_CODE_METHOD.format(user_code=user_code, fn_name=fn_name, args=args, class_or_func=class_or_func)
        else:
            harness_code = HARNESS_CODE_FUNCTION.format(user_code=user_code, fn_name=fn_name, args=args)
        print(harness_code)
        response = requests.post(
            f"{URL_DOCKER_SANDBOX}/run_code", 
            headers={'Content-Type': 'application/json'}, 
            data=json.dumps({"code": harness_code, "language": language, "stdin":""}))
        result = response.json()
        if result['run_result']['return_code'] == 0:
            stdout = result['run_result']['stdout']
            if stdout.strip() == str(test['output']).strip():
                total_passes += 1
    return total_passes/ len(test_cases)
    



string_code = """
#include <iostream>
using namespace std;

int main() {
    float a, b, c;

    cin >> a >> b;
    
    cout << a/b << endl;
    return 0;
}
"""
string_code_python="""
input_str = input()
a, b = input_str.split()
print(float(a)/float(b))
"""



gt_output_prime = {'test_cases': [{'type': 'stdin_stdout', 
                                   'input': '1 2', 
                                   'output': '0.5'},
                                   {'type': 'stdin_stdout', 
                                   'input': '4 5', 
                                   'output': '0.8'},
                                   {'type': 'stdin_stdout', 
                                   'input': '1 1', 
                                   'output': '1'}], 
                                   'language': 'cpp'}
gt_output_string = json.dumps(gt_output_prime)
llm_response = f'<think>...</think>\n```c++\n{string_code}\n```\n ok hw'

llm_response_python = f'<think>...</think>\n```python\n{string_code_python}\n```\n'
gt_output_prime_python = {'test_cases': [{'type': 'stdin_stdout',   
                                   'input': '1 2', 
                                   'output': '0.5'},
                                   {'type': 'stdin_stdout', 
                                   'input': '4 5', 
                                   'output': '0.8'},
                                   {'type': 'stdin_stdout', 
                                   'input': '1 1', 
                                   'output': '1'}], 
                                   'language': 'python'}
gt_output_prime_python_string = json.dumps(gt_output_prime_python)
print(code_oj_verify(llm_response_python, gt_output_prime_python_string))
print(code_oj_verify(llm_response, gt_output_string))

from datasets import load_dataset
# prime_dataset = load_dataset("PrimeIntellect/verifiable-coding-problems")

# sample = prime_dataset["train"][488]
# print(sample)

llm_response=f"""
<think>...</think>
```python
class Solution:
    def maxScore(self, cardPoints: List[int], k: int) -> int:
        ans = s = sum(cardPoints[-k:])
        for i, x in enumerate(cardPoints[:k]):
            s += x - cardPoints[-k + i]
            ans = max(ans, s)
        return ans```
"""

gt_output_prime = {'test_cases': [{'type': 'function_call', 'fn_name': 'maxScore', 'input': [[1, 2, 3, 4, 5, 6, 1], 3], 'output': 12}], 'language': 'Python'}
gt_output_prime_string = json.dumps(gt_output_prime)
print(code_function_call_verify(llm_response, gt_output_prime_string))



from datasets import load_dataset
dataset = load_dataset("tuenguyen/verifiable-coding-problems")

def combine_verifiable_coding_problems(llm_response, answer):
    # First we need to check the answer is function call or testcase 
    answer_parser = json.loads(answer)
    if all([item['type']=='function_call' for item in answer_parser['test_cases']]):
        return code_function_call_verify(llm_response, answer)
    else:
        return code_oj_verify(llm_response, answer)

total_pass = 0
total = 0
for index, row in enumerate(dataset["train"]):
    gold_standard_solution = row["gold_standard_solution"]
    
    if gold_standard_solution is not None:
        answer = row["answer"]
        value = combine_verifiable_coding_problems(gold_standard_solution, answer)
        # if value != 1:
            # print(index, value)
        if value == 1:
            total_pass += 1
        total += 1
    if index %1000==0:
        print(total_pass/total, total_pass, total)




