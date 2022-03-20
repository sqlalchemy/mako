#!/usr/bin/env python3

"""
entry point for directly running mako as templating engine.

that way, mako can directly be used as an rendering interpreter
in an executable text files' shebang:
#!/usr/bin/env -S python3 -m mako -s --
"""

from .cmd import cmdline

if __name__ == "__main__":
    cmdline()
