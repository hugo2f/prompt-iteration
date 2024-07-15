import streamlit as st

from chatclient import ChatClient
import utils

# create chat session
image_name = 'form2.jpg'
if 'chat_client' not in st.session_state:
    st.session_state.chat_client = ChatClient(image_name)
chat_client = st.session_state.chat_client

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
compare_col1, compare_col2 = st.columns(2)

# chat section
response_display = st.empty()
prompt = st.chat_input('Enter your prompt')

# this runs every time user presses enter
if prompt:
    chat_client.send_task_message(prompt)

    if not chat_client.prev_prompt:  # no need to compare
        with prompt_col2:
            st.write(chat_client.cur_prompt)
        with compare_col2:
            st.write(chat_client.cur_response)
    else:
        # update prompts
        chat_client.compare_prompts(prompt_col1, prompt_col2)
        # update response comparisons
        chat_client.compare_responses(compare_col1, compare_col2)

    # placeholder space no longer needed after there are responses
    with space_between_prompt_response:
        st.write("")

