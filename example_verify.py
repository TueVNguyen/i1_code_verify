from datasets import load_dataset
import requests
import json
import random

URL_DOCKER_SANDBOX = "http://localhost:5434"

def check_health():
    response = requests.get(f"{URL_DOCKER_SANDBOX}/v1/ping")
    print(response.json())
    if response.status_code != 200:
        raise Exception("Sandbox is not running")
    return True

if not check_health():
    raise Exception("Sandbox is not running please pull docker image and run docker server")




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
llm_response = f'<think>...</think>\n```c++\n{string_code}\n```\n'

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
    
    return total_passes/ len(test_cases)




print(code_oj_verify(llm_response, gt_output_string))

    

