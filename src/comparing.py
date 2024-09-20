import copy
import difflib
import json
from json import JSONDecodeError

from deepdiff import DeepDiff
import streamlit as st

from html_formatting import PROMPT_CSS, RESPONSE_CSS, add_html_wrapping

__all__ = ['character_level_compare_and_display', 'path_to_keys', 'follow_path',
           'get_json_diffs', 'json_compare_and_display', 'json_accuracy_score',
           'load_json_string']

# -----------------------------------------------------------------------------
# private globals
# -----------------------------------------------------------------------------

# types of json differences
_VALUE_CHANGED = 0
_KEY_CHANGED = 1


def load_json_string(json_string):
    """
    convert a string with a JSON into a dict
    returns None if string is not a valid JSON
    """
    try:
        converted_json = json.loads(json_string)
        return converted_json
    except (JSONDecodeError, TypeError):
        return None


def get_json_diffs(cur_dict, target_dict):
    """
    :param cur_dict: cur_response (if valid JSON, converted to dict already)
    :param target_dict: right answer
    :return:
        None if cur_dict is not a dict,
        DeepDiff diffs with view='tree' otherwise
    """
    if not isinstance(cur_dict, dict):
        return None
    return DeepDiff(cur_dict, target_dict, view='tree')


def character_level_compare_and_display(text1, text2, col1, col2):
    """
    compare texts and display to streamlit columns
    :param text1, text2: Texts to compare
    :param col1, col2: target streamlit columns
    """
    matcher = difflib.SequenceMatcher(None, text1, text2)
    # differences as a list of tuples (operation, start1, end1, start2, end2)
    opcodes = matcher.get_opcodes()

    with col1:
        processed_text1 = []
        for tag, i1, i2, j1, j2 in opcodes:
            chunk = text1[i1:i2]
            if tag == 'equal':
                processed_text1.append(f'<span>{chunk}</span>')
            elif tag in ('replace', 'delete'):
                processed_text1.append(f"<span class='red'>{chunk}</span>")

        html_code = add_html_wrapping(''.join(processed_text1), PROMPT_CSS, 'prompt-block')
        st.markdown(html_code, unsafe_allow_html=True)

    with col2:
        processed_text2 = []
        for tag, i1, i2, j1, j2 in opcodes:
            chunk = text2[j1:j2]
            if tag == 'equal':
                processed_text2.append(f'<span>{chunk}</span>')
            elif tag in ('replace', 'insert'):
                processed_text2.append(f"<span class='green'>{chunk}</span>")

        html_code = add_html_wrapping(''.join(processed_text2), PROMPT_CSS, 'prompt-block')
        st.markdown(html_code, unsafe_allow_html=True)


def path_to_keys(diff):
    """
    for example, diff could look like: "root['工单信息'][0]['产品名称']"
    we want the keys as a list: [工单信息, 0, 产品名称]
    the .replace("'", "") removes redundant single quotes for string keys

    :param diff: item DeepDiff comparison, e.g."root['工单信息'][0]['产品名称']"
    :return: deepdiff
    """
    return diff.strip("root[").strip("]").replace("'", "").split("][")


def follow_path(cur_dict, diff_keys):
    """follow the keys in diff_keys into cur_dict"""
    for key in diff_keys:
        # if the json contains lists, the key is an int index
        if isinstance(cur_dict, list):
            key = int(key)
        cur_dict = cur_dict[key]
    return cur_dict


def _highlight_json_diffs(d, diffs, color_class, change_type):
    """
    add HTML formatting for differences in the dictionary
    :param d: initial json (dictionary)
    :param diffs: list of paths to differing keys/values
    :param color_class: color for highlighting differences
    :param change_type: VALUE_CHANGED to highlight only the value,
                        KEY_CHANGED to highlight the "subjson" rooted at a key
    :return: dictionary with HTML formatting applied
    """
    original_dict = copy.deepcopy(d)

    for diff in diffs:
        diff_keys = path_to_keys(diff)
        # follow the keys until the second last level, so we can modify key_to_change
        key_to_change = diff_keys.pop()
        cur_dict = follow_path(original_dict, diff_keys)

        if change_type == _VALUE_CHANGED:
            # only format the value
            cur_dict[key_to_change] = f"<span class='{color_class}'>{cur_dict[key_to_change]}</span>"
        elif change_type == _KEY_CHANGED:
            # replace the current <key, value> pair with the formatted version
            cur_dict[f"<span class='{color_class}'>{key_to_change}</span>"] = (
                f"<span class='{color_class}'>"
                f"{json.dumps(cur_dict[key_to_change], indent=2, ensure_ascii=False)}"
                f"</span>")
            del cur_dict[key_to_change]

    return original_dict


def json_compare_and_display(dict1, dict2, col1, col2, warn1, warn2):
    """
    compare texts and display to streamlit columns
    :param dict1, dict2: JSONs to compare
    :param col1, col2: target streamlit columns
    :param warn1, warn2: empty() elements for displaying warning
    """
    # just in case dict1/2 are passed in as strings, convert them if needed
    if not isinstance(dict1, dict):
        dict1 = load_json_string(dict1)
    if not isinstance(dict2, dict):
        dict2 = load_json_string(dict2)

    if dict1 is None or dict2 is None:
        if dict1 is None:
            with col1:
                st.write(dict1)
                warn1.warning('Previous response does not contain a valid JSON')
        if dict2 is None:
            with col2:
                st.write(dict2)
                warn2.warning('Current response does not contain a valid JSON')
        return

    diffs = DeepDiff(dict1, dict2, view='tree')

    # get paths to differences of each type
    added = [diff.path() for diff in diffs.get('dictionary_item_added', [])]
    removed = [diff.path() for diff in diffs.get('dictionary_item_removed', [])]
    changed = ([diff.path() for diff in diffs.get('values_changed', [])]
               + [diff.path() for diff in diffs.get('type_changes', [])])

    # highlight differing parts
    dict1_formatted = _highlight_json_diffs(dict1, removed, 'red', _KEY_CHANGED)
    dict1_formatted = _highlight_json_diffs(dict1_formatted, changed, 'red', _VALUE_CHANGED)

    dict2_formatted = _highlight_json_diffs(dict2, added, 'green', _KEY_CHANGED)
    dict2_formatted = _highlight_json_diffs(dict2_formatted, changed, 'green', _VALUE_CHANGED)

    with col1:
        html_code = add_html_wrapping(
            json.dumps(dict1_formatted, indent=2, ensure_ascii=False),
            RESPONSE_CSS,
            'response-block')

        st.markdown(html_code, unsafe_allow_html=True)

    with col2:
        html_code = add_html_wrapping(
            json.dumps(dict2_formatted, indent=2, ensure_ascii=False),
            RESPONSE_CSS,
            'response-block')
        st.markdown(html_code, unsafe_allow_html=True)


def _count_values(json_obj):
    """count number of deepest values in json_obj"""
    if isinstance(json_obj, dict):
        return sum(_count_values(v) for v in json_obj.values())
    elif isinstance(json_obj, list):
        return sum(_count_values(item) for item in json_obj)
    else:
        return 1


def json_accuracy_score(cur, target_dict):
    """
    computes similarity of cur to target based on number of matched values in target

    :param cur: string response
    :param target_dict: dict
    :return:
        -1 if cur_dict or target_dict is None (response did not contain valid json)
        percentage with one decimal digit, ex: 12.3
    """

    # convert JSON string to dict
    if isinstance(cur, dict):
        cur_dict = cur
    else:
        try:
            cur_dict = json.loads(cur)
        except (JSONDecodeError, TypeError):
            print('not a json: ', cur)
            return -1

    # number of correct values to match
    target_value_count = _count_values(target_dict)

    # count number of target values not matched
    diffs = DeepDiff(cur_dict, target_dict, view='tree')
    added = [diff.path() for diff in diffs.get('dictionary_item_added', [])]
    changed = ([diff.path() for diff in diffs.get('values_changed', [])]
               + [diff.path() for diff in diffs.get('type_changes', [])])

    not_matched = 0
    for diff in added + changed:
        diff_keys = path_to_keys(diff)
        # follow the keys until the second last level, so we can modify key_to_change
        cur_dict = follow_path(target_dict, diff_keys)
        not_matched += _count_values(cur_dict)

    accuracy = 1 - not_matched / target_value_count
    return round(accuracy * 100, 1)


def main():
    """testing use"""
    json1 = json.loads('''
        {
          "key1": {
            "nested_key1": ["value1", "value2"],
            "nested_key3": "value2"
          },
          "key2": {
            "nested_key3": "value3"
          },
          "key3": {
            "nested_key4": "value4"
          }
        }
    ''')

    json2 = json.loads('''
        {
          "key1": {
            "nested_key1": "value1",
            "nested_key2": "value2"
          },
          "key2": {
            "nested_key3": "value3",
            "nested_key4": "value4"
          }
        }
    ''')

    acc = json_accuracy_score(json1, json2)
    print(json1)
    print('-----------')
    print(json2)
    print('-----------')
    print(acc)
    diffs = DeepDiff(json1, json2, view='tree')
    added = [diff.path() for diff in diffs.get('dictionary_item_added', [])]
    changed = ([diff.path() for diff in diffs.get('values_changed', [])]
               + [diff.path() for diff in diffs.get('type_changes', [])])
    print(added)
    print(changed)


if __name__ == '__main__':
    main()
