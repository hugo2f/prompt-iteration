import textwrap

import streamlit as st

from chatclient import ChatClient
from html_formatting import PROMPT_CSS, RESPONSE_CSS, add_html_wrapping

# app states
image_name = 'form2.jpg'
if 'chat_client' not in st.session_state:
    st.session_state.chat_client = ChatClient(image_name=image_name)
chat_client = st.session_state.chat_client
if 'is_first_prompt' not in st.session_state:
    st.session_state.is_first_prompt = True

# setup app page
st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center;'>Prompt Iteration</h1>", unsafe_allow_html=True)

left, right = st.columns(2)
left.subheader('Previous', divider='gray')
right.subheader('Current', divider='gray')

# prompt section
st.subheader("Prompt")
prompt_col1, prompt_col2 = st.columns(2)

# on startup, insert some space between the prompt and response sections
space_between_prompt_response = st.empty()
with space_between_prompt_response:
    st.markdown("<div style='height: 50px;' />", unsafe_allow_html=True)  # Adjust height as needed

# response section
st.subheader("Response")
response_col1, response_col2 = st.columns(2)
# displays "response is not a valid JSON" warnings
json_warning1, json_warning2 = response_col1.empty(), response_col2.empty()
analysis = st.empty()

# chat section
response_display = st.empty()
prompt = st.chat_input('Enter your prompt')

# this runs every time user presses enter
if prompt:
    chat_client.send_task_message(prompt, st.session_state.is_first_prompt)

    if st.session_state.is_first_prompt:  # no need to compare
        with prompt_col2:
            html_code = add_html_wrapping(
                textwrap.fill(chat_client.cur_prompt, width=35),
                PROMPT_CSS,
                'prompt-block')
            st.markdown(html_code, unsafe_allow_html=True)
        with response_col2:
            html_code = add_html_wrapping(
                chat_client.cur_response,
                RESPONSE_CSS,
                'response-block')
            st.markdown(html_code, unsafe_allow_html=True)
        if not isinstance(chat_client.cur_response, dict):
            json_warning2.warning('This response does not contain a valid JSON')
    else:
        # display prompt comparison
        chat_client.compare_display_prompts(prompt_col1, prompt_col2)
        # response comparison
        chat_client.compare_display_responses(response_col1, response_col2,
                                              json_warning1, json_warning2)

    if chat_client.prev_accuracy and chat_client.prev_accuracy == -1:
        json_warning1.warning('This response does not contain a valid JSON')
    if chat_client.cur_accuracy and chat_client.cur_accuracy == -1:
        json_warning2.warning('This response does not contain a valid JSON')
    # accuracy
    with response_col1:
        st.write(f'Accuracy: {max(chat_client.prev_accuracy, 0)}%')
    with response_col2:
        st.write('fdsa')
        st.write(f'Accuracy: {max(chat_client.cur_accuracy, 0)}%')
        st.write('asdf')

    if chat_client.cur_accuracy < 100:
        analysis.write(chat_client.send_analyze_message(st.session_state.is_first_prompt))
    st.session_state.is_first_prompt = False

    # placeholder space no longer needed after there are responses
    with space_between_prompt_response:
        st.write("")

