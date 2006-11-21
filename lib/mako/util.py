# util.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

try:
    Set = set
except:
    import sets
    Set = sets.Set

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
    

