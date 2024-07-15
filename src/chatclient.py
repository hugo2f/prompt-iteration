import os
import sys
import textwrap

import dashscope
from dashscope import MultiModalConversation
from dotenv import load_dotenv

from utils import character_level_compare_and_display, json_compare_and_display, json_accuracy_score
from right_answer import RIGHT_ANSWER

__all__ = ['ChatClient']

# constants
_JSON_START = '```json'
_JSON_END = '```'


def _get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_text(response):
    """get text from qwen response"""
    return response.output.choices[0]['message']['content'][0]['text']


def _extract_json(full_response):
    """
    get json inside ```json```,
    returns '' if nonexistent
    """
    start_index = full_response.find(_JSON_START)
    end_index = full_response.find(_JSON_END, start_index + len(_JSON_START))
    return full_response[start_index + len(_JSON_START):end_index]


class ChatClient:
    """
    handles sending to and receiving from qwen
    """

    def __init__(self, mode='JSON', image_name=None, right_answer=None):
        # setup info
        self.mode = mode
        load_dotenv()
        dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

        if image_name:
            images_dir = os.path.join(_get_project_root(), 'images')
            # image to give to qwen
            self.qwen_file_path = f'file://{images_dir}/{image_name}'

        # 2 most recent pairs of prompts/responses to compare
        self.prev_prompt = self.prev_response = None
        self.cur_prompt = self.cur_response = None

        # response rating
        self.right_answer = right_answer
        # percentage accuracy compared to right_answer (JSON: number of correct keys and values vs. total)
        self.prev_accuracy = self.cur_accuracy = 0
        # user given score
        self.prev_score = self.cur_score = 0

    def send_task_message(self, msg):
        """send user's task to model"""

        # update saved prompts
        self.prev_prompt = self.cur_prompt
        self.cur_prompt = textwrap.fill(msg, width=35)

        # send message to qwen
        messages = [
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
            messages=messages,
        )

        response_text = _get_text(response)

        if self.mode == 'json':
            response_text = _extract_json(response_text)

        self.prev_response, self.cur_response = self.cur_response, response_text
        self.prev_accuracy = self.prev_accuracy
        self.cur_accuracy = json_accuracy_score(self.cur_response, RIGHT_ANSWER)

    def send_analyze_message(self, message):
        """send message for analyzing how a prompt can be improved"""
        pass

    def compare_prompts(self, col1, col2):
        character_level_compare_and_display(self.prev_prompt, self.cur_prompt, col1, col2)

    def compare_responses(self, col1, col2):
        if _JSON_START in self.prev_response and _JSON_START in self.cur_response:
            json_compare_and_display(self.prev_response, self.cur_response, col1, col2)
        else:
            character_level_compare_and_display(self.prev_response, self.cur_response, col1, col2)


def main():
    """test program to send prompts to qwen"""

    image_name = 'apple.webp'
    image_path = f'../images/{image_name}'
    if not os.path.isfile(image_path):
        print('Image does not exist')
        sys.exit(-1)

    chat = ChatClient(image_name=image_name)

    while True:
        msg = input('> ')
        chat.send_task_message(msg)
        print()


if __name__ == '__main__':
    main()
