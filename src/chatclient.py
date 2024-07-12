from enum import Enum
import json
import os
import sys
import textwrap
import streamlit as st

import dashscope
from dashscope import MultiModalConversation
from dotenv import load_dotenv

import messages
from utils import character_level_compare_and_display, json_compare_and_display

__all__ = ['ChatMode', 'ChatClient']


class ChatMode(Enum):
    TEXT = 'Text'
    JSON = 'JSON'


def _get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_text(response):
    """
    get text from qwen response
    """

    return response.output.choices[0]['message']['content'][0]['text']


def _extract_json(full_response):
    """
    get json inside ```json```,
    returns '' if nonexistent
    """
    start_index = full_response.find(_JSON_START)
    end_index = full_response.find(_JSON_END, start_index + len(_JSON_START))
    return full_response[start_index + len(_JSON_START):end_index]


# constants
_JSON_START = '```json'
_JSON_END = '```'


class ChatClient:
    """
    handles sending to and receiving from qwen
    """
    def __init__(self, mode=ChatMode.TEXT, image_name=None, right_answer=None):
        # chat setup
        self.mode = mode

        # qwen setup
        if image_name:
            images_dir = os.path.join(_get_project_root(), 'images')
            load_dotenv()
            dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

            # image to give to qwen
            self.qwen_file_path = f'file://{images_dir}/{image_name}'

        # 2 most recent pairs of prompts/responses to compare
        self.prev_prompt = self.prev_response = None
        self.cur_prompt = self.cur_response = None

        # response rating
        self.right_answer = right_answer
        self.accuracy = 0  # percentage accuracy compared to right_answer
        self.score = 0     # user given score

    def set_mode(self, mode):
        self.mode = mode

    def send_task_message(self, msg):
        """send user's task to model"""

        # update saved prompts
        self.prev_prompt = self.cur_prompt
        self.cur_prompt = textwrap.fill(msg, width=40)

        # send message to qwen
        message = [
            {
                'role': 'user',
                'content': [
                    {'image': self.qwen_file_path},
                    {'text': f'{msg}'}
                ]
            }
        ]

        response = MultiModalConversation.call(
            model='qwen-vl-plus',
            messages=message,
            # stream=False,
            # incremental_output=True,
        )

        response_text = _get_text(response)

        if self.mode == 'json':
            response_json = _extract_json(response_text)
            response_json = json.dumps(json.loads(response_json), indent=2, ensure_ascii=False)
        else:
            response_json = response_text

        self.prev_response = self.cur_response
        self.cur_response = response_json

    def send_analyze_message(self, msg):
        """send message for analyzing how a prompt can be improved"""

        # todo: analyze_json_response parameters
        message = [
            {
                'role': 'user',
                'content': [
                    {'image': self.qwen_file_path},
                    {'text': messages.format_json_analysis_message()}
                ]
            }
        ]

    def compare_prompts(self, col1, col2):
        character_level_compare_and_display(self.prev_prompt, self.cur_prompt, col1, col2)

    def compare_responses(self, col1, col2):
        col1.write(self.mode)
        if self.mode == ChatMode.JSON:
            st.write('comparing json')
            json_compare_and_display(_extract_json(self.prev_response), _extract_json(self.cur_response), col1, col2)
        elif self.mode == ChatMode.TEXT:
            character_level_compare_and_display(self.prev_response, self.cur_response, col1, col2)


def main():
    """test program to send prompts to qwen"""

    image_name = 'apple.webp'
    image_path = f'../images/{image_name}'
    if not os.path.isfile(image_path):
        print('Image does not exist')
        sys.exit(-1)

    chat = ChatClient(image_name=image_name, mode=ChatMode.JSON)

    while True:
        msg = input('> ')
        chat.send_task_message(msg)
        print()


if __name__ == '__main__':
    main()
