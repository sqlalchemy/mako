"""preprocessing functions, used with the 'preprocessor' 
argument on Template, TemplateLookup"""

import re

def convert_comments(text):
    """preprocess old style comments.
    
    example:
    
    from mako.ext.preprocessors import convert_comments
    t = Template(..., preprocessor=preprocess_comments)"""
    return re.sub(r'(?<=\n)\s*#[^#]', "##", text)

