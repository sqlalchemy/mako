import re

def flatten_result(result):
    return re.sub(r'[\s\n]+', ' ', result).strip()

def result_lines(result):
    return [x.strip() for x in re.sub(r' +', ' ', result).split('\n') if x.strip() != '']