import re

def flatten_result(result):
    return re.sub(r'[\s\n]+', ' ', result).strip()
