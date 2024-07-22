import json

__all__ = ['PROMPT_CSS', 'RESPONSE_CSS', 'add_html_wrapping']

# -----------------------------------------------------------------------------
# private globals
# -----------------------------------------------------------------------------

_COLOR_CSS = """
.red {
    color: #ff7b72;
}
.green {
    color: #2f6f37;
}
"""

# leading and trailing newlines are needed, or else
# add_html_formatting can return things like </style><div>..</div>,
# which doesn't apply the styles properly
PROMPT_CSS = f"""
<style>
.prompt-block {{
    background-color: #444;
    font-family: Helvetica;
    padding: 10px;
    border-radius: 5px;
    white-space: pre-wrap; /* preserve spaces */
}}
{_COLOR_CSS}
</style>
"""

RESPONSE_CSS = f"""
<style>
.response-block {{
    background-color: #444;
    font-family: monospace;
    padding: 10px;
    border-radius: 5px;
    white-space: pre-wrap; /* preserve spaces */
}}
{_COLOR_CSS}
</style>
"""


def add_html_wrapping(text, styles, classname):
    if isinstance(text, dict):
        text = json.dumps(text, indent=2, ensure_ascii=False)
    return f"{styles}<div class='{classname}'>{text}</div>"
