import streamlit as st

from chatclient import ChatMode, ChatClient

# initialize states
# create chat session
image_name = 'form1.png'
if 'chat_client' not in st.session_state:
    st.session_state.chat_client = ChatClient(image_name=image_name, mode=ChatMode.JSON)
if 'mode' not in st.session_state:
    st.session_state.mode = ChatMode.TEXT
chat_client = st.session_state.chat_client

# setup app page
st.set_page_config(layout="wide")

# title bar + mode list
_, title_col, mode_col = st.columns([1, 6, 1])
with title_col:
    st.markdown("<h1 style='text-align: center; margin-top: -5px; padding-top: 0;'>Prompt Iteration</h1>",
                unsafe_allow_html=True)

# with mode_col:
#     selected_mode = st.selectbox("Mode", list(ChatMode), format_func=lambda mode: mode.value, key='mode',
#                                  on_change=chat_client.set_mode, args=(st.session_state.mode,),
#                                  label_visibility='collapsed')

left, right = st.columns(2)
left.markdown("""
    <style>
    .column-header {
        padding: 0;
        margin: 0;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
right.markdown("""
    <style>
    .column-header {
        padding: 0;
        margin; 0;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
left.markdown("<h3 class='column-header'>Previous</h3>", unsafe_allow_html=True)
right.markdown("<h3 class='column-header'>Current</h3>", unsafe_allow_html=True)

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
    # chat_client.send_task_message(prompt)

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
