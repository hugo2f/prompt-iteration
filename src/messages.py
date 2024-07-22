import json

__all__ = ['json_analysis_prompt']

ANALYSIS_RESPONSE_START = '###analysis：'


def _format_diffs(diffs):
    """
    format diffs for model prompt
    """
    # format for differences: e.g. 漏掉了[missing_keys]，[wrong_keys]读取错误
    added = [diff.path() for diff in diffs.get('dictionary_item_added', [])]
    changed = ([diff.path() for diff in diffs.get('values_changed', [])]
               + [diff.path() for diff in diffs.get('type_changes', [])])

    # each path looks like "root['工单信息'][0]['产品名称']"
    # convert this to [工单信息][0][产品名称]
    missing_keys = [path.strip('root').replace("'", "") for path in added]
    wrong_values = [path.strip('root').replace("'", "") for path in changed]

    # portion of the prompt dealing with missing_keys and wrong_values
    missing_prompt = f'漏掉了的消息有：{"、".join(missing_keys)}' if missing_keys else ''
    wrong_prompt = f'错误的消息有：{"、".join(wrong_values)}' if wrong_values else ''
    return f'{missing_prompt}\n{wrong_prompt}'


def json_analysis_prompt(prompt, accuracy, diffs, response, response_is_json, is_first_prompt):
    """
    formats a prompt to analyze current response vs. right answer

    :param prompt: user prompt
    :param accuracy: percentage accuracy, e.g. 25.2
    :param diffs: DeepDiff diffs
    :param response: model response, dict if contains valid json, else string
    :param response_is_json: True if response contains valid json, False otherwise
    :param is_first_prompt: True if analyzing first prompt, False if analyzing new prompt versions
    """
    if is_first_prompt:
        prompt_start = ""
    else:
        prompt_start = "我对上一版prompt做了修改。"
    if response_is_json:
        response = json.dumps(response, indent=2, ensure_ascii=False)
        analysis = (f"你正确解析了{accuracy}%的JSON键值对，具体错误如下。\n"
                    f"{_format_diffs(diffs)}\n")
    else:
        if isinstance(response, list):
            analysis = "合理的JSON格式是由{}围绕，但你的返回用了[]。"
        else:
            analysis = "你的输出不是JSON格式。"

    task = ('请综合考量核心任务、提示词、输出、错误详情，' if is_first_prompt
            else '请综合考量核心任务、提示词的变化带来的错误详情的变化，')

    analyze_json_prompt = (
        f"# 你作为assistant的核心任务\n"
        f"从附件中解析关键信息并输出JSON。为了更好的完成这个任务，我将尝试不同的提示词来提高JSON输出的准确率。\n\n"
        f"# 提示词\n"
        # f"{prompt_start}当prompt为'{prompt}'时，你的解析是：\n\n"
        f"{prompt}\n\n"
        f"# 输出\n"
        f"{response}\n\n"
        f"# 错误详情\n"
        f"{analysis}\n\n"
        f"# 当前任务\n"
        f"{task}分析提示词可以改进的方向，输出调整提示词的建议"
    )
    return analyze_json_prompt
