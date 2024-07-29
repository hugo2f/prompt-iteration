from http import HTTPStatus
import os
import sys

import dashscope
from dashscope import MultiModalConversation
from dotenv import load_dotenv

from messages import json_analysis_prompt
from right_answer import RIGHT_ANSWER
from comparing import (character_level_compare_and_display, get_json_diffs,
                       json_compare_and_display, json_accuracy_score,
                       load_json_string)

__all__ = ['ChatClient']

# -----------------------------------------------------------------------------
# private globals
# -----------------------------------------------------------------------------
_QWEN_MODEL = 'qwen-vl-max'


def _get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_text(response):
    """Get text from qwen response"""
    return response.output.choices[0]['message']['content'][0]['text']


def _extract_json(full_response):
    """
    If exists, the json will start with ```json or ```, and end with ```,
    returns '' if nonexistent
    """
    _JSON_BLOCK_START = '```JSON'
    _CODE_BLOCK_START = '```'
    _CODE_BLOCK_END = '```'

    # look for JSON block
    json_start = full_response.find(_JSON_BLOCK_START)
    if json_start != -1:
        content_start = json_start + len(_JSON_BLOCK_START)
        end = full_response.find(_CODE_BLOCK_END, content_start)
        if end != -1:
            return full_response[content_start:end].strip()

    # if ```json not present, check if there's a code block with just ```
    code_start = full_response.find(_CODE_BLOCK_START)
    if code_start != -1:
        content_start = code_start + len(_CODE_BLOCK_START)
        end = full_response.find(_CODE_BLOCK_END, content_start)
        if end != -1:
            return full_response[content_start:end].strip()

    # no JSON/code found
    return ''


class ChatClient:
    """handles sending to and receiving from qwen"""

    def __init__(self, mode='JSON', image_name=None):
        # setup info
        self.mode = mode
        load_dotenv()
        dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')
        self.messages = []

        # if uploading image
        self.qwen_file_path = None
        if image_name:
            images_dir = os.path.join(_get_project_root(), 'images')
            # image to give to qwen
            self.qwen_file_path = f'file://{images_dir}/{image_name}'

        # 2 most recent pairs of prompts/responses to compare
        # stores dicts in JSON mode (if response contains a valid JSON)
        self.prev_prompt = self.prev_response = None
        self.cur_prompt = self.cur_response = None

        # response rating
        self.right_answer = load_json_string(RIGHT_ANSWER)

        # accuracy (in percent) compared to right_answer (JSON: number of correct keys and values vs. total)
        self.prev_accuracy = self.cur_accuracy = 0
        # user given score
        self.prev_score = self.cur_score = 0

    def _send_message(self, msg, is_first_message):
        """
        :param msg: message to send to model
        :param is_first_message: upload image if first time sending JSON prompt
        :return:
            None if HTTP error,
            text in response otherwise
        """
        if is_first_message:
            self.messages = [
                {
                    'role': 'user',
                    'content': [
                        {'text': msg},
                        {'image': self.qwen_file_path}
                    ]
                }
            ]
        else:
            self.messages.append({"role": "user",
                                  "content": [
                                      {"text": msg}
                                  ]})

        # for testing: display chat history
        import streamlit as st
        st.write(len(self.messages), self.messages)
        response = MultiModalConversation.call(
            model=_QWEN_MODEL,
            messages=self.messages,
            seed=1024,
            top_p=0.3,
        )

        if response.status_code != HTTPStatus.OK:
            return None

        # save response to chat history
        self.messages.append({'role': response.output.choices[0].message.role,
                              'content': response.output.choices[0].message.content})

        processed_response = _get_text(response)
        return processed_response

    def send_task_message(self, msg, is_first_prompt):
        """send user's task to model"""
        # update saved prompts
        self.prev_prompt = self.cur_prompt
        self.cur_prompt = msg

        # send message to qwen
        processed_response = self._send_message(msg, is_first_prompt)

        if self.mode == 'JSON':
            print('processed response: ', _extract_json(processed_response))
            print('loaded json: ', load_json_string(_extract_json(processed_response)))
            loaded_json = load_json_string(_extract_json(processed_response))
            if loaded_json:
                processed_response = loaded_json

        self.prev_response, self.cur_response = self.cur_response, processed_response
        self.prev_accuracy = self.prev_accuracy
        self.cur_accuracy = json_accuracy_score(self.cur_response, self.right_answer)

    def send_analyze_message(self, is_first_prompt):
        """
        send message for analyzing how a prompt can be improved

        :return response text
        """

        diffs = get_json_diffs(self.cur_response, self.right_answer)
        msg = json_analysis_prompt(self.cur_prompt, self.cur_accuracy, diffs,
                                   self.cur_response, is_first_prompt)

        processed_response = self._send_message(msg, False)
        return processed_response

    def compare_display_prompts(self, col1, col2):
        character_level_compare_and_display(self.prev_prompt, self.cur_prompt, col1, col2)

    def compare_display_responses(self, col1, col2, warn1, warn2):
        if self.mode == 'JSON':
            json_compare_and_display(self.prev_response, self.cur_response,
                                     col1, col2, warn1, warn2)
        else:
            character_level_compare_and_display(self.prev_response, self.cur_response,
                                                col1, col2)


def interactive_prompting():
    """test program to send prompts to qwen"""
    image_name = 'apple.webp'
    image_path = f'../images/{image_name}'
    if not os.path.isfile(image_path):
        print('Image does not exist')
        sys.exit(-1)

    chat_client = ChatClient(image_name=image_name)

    is_first_prompt = True
    while True:
        msg = input('> ')
        chat_client.send_task_message(msg, is_first_prompt)
        is_first_prompt = False
        print()


def test_compare():
    cur_response = """
    {
      "工单信息": [
        {
          "产品名称": "剪刀缸1150",
          "规格型": "JY.1150-1.11.01-001-G-01.001 0178/0160*805",
          "需方": "佛山市南海区源上液压设备有限公司",
          "数量": "1"
        },
        {
          "产品名称": "辅助缸筒1150T",
          "规格型号": "JY.1150-1.11.04-001-G-01.001 0230/0180*1935",
          "需方": "佛山市南海区源上液压设备有限公司",
          "数量": "2"
        },
        {
          "产品名称": "托模缸筒1150T",
          "规格型号": "0140/0120*1300",
          "需方": "佛山市南海区源上液压设备有限公司",
          "数量": "1"
        },
        {
          "产品名称": "盛辅助缸筒(后置)1250T",
          "规格型号": "0178/0140*1160",
          "需方": "佛山市南海区源上液压设备有限公司",
          "数量": "4"
        }
      ]
    }
    """.strip()

    chat_client = ChatClient()
    chat_client.cur_response = cur_response
    chat_client.cur_accuracy = json_accuracy_score(cur_response, chat_client.right_answer)
    print(chat_client.cur_accuracy)
    print('analyze prompt:')
    print(chat_client.send_analyze_message(True))


if __name__ == '__main__':
    # interactive_prompting()
    # print(DeepDiff(None, json.loads(RIGHT_ANSWER), view='tree').get('type_changes')[0].path())
    test_compare()
