# required parameters: task_description, prompt, accuracy, differences, response_json
def analyze_json_response(task_description, prompt, accuracy, differences, response_json):
    analyze_json_template = (f"你的核心任务是：根据附件，{task_description}。为了更好的完成这个任务，我会不断调整prompt，"
                             f"你需要根据prompt的delta、error的delta给我调整prompt的建议。以下是我的某一次prompt尝试。"
                             f"接收到{prompt}后，你正确解析了{accuracy}%的JSON键值对，具体错误为{differences}。"
                             f"你的解析是{response_json}。请综合任务描述和附件、以及第一次的错误，给出一个改进版的prompt。"
                             f"回答以'###prompt: '开始")
    return analyze_json_template

# todo: format of differences output from json diff, how to put in template
# is task_description same as prompt? where should it be entered?
