#!/usr/bin/env python3
"""Point the top-level README at the fork's own notes.

Placed immediately after upstream's "detached early state" warning, which is
where a reader stops and wonders whether the thing is usable - and which the
fork's README answers.
"""
import sys

p = sys.argv[1] if len(sys.argv) > 1 else 'README.md'
s = open(p).read()

anchor = "> This repo is used mainly as an issue tracker.\n"
note = """
> **OpenGeofiction fork.** This branch renders
> [OpenGeofiction](https://www.opengeofiction.net/)'s fictional planet, and puts
> back the layers the stylesheets style but the project file never defined —
> landcover below z10, boundaries, place labels, ferries, power, and the relief
> ladder. See **[ogf/README.md](ogf/README.md)** for what was missing, what was
> restored and from where, and what is still absent.
"""

if 'ogf/README.md' in s:
    print('  already linked')
    sys.exit(0)
if anchor not in s:
    print('  anchor not found - upstream README has changed shape')
    sys.exit(1)

s = s.replace(anchor, anchor + note)
open(p, 'w').write(s)
print('  README.md links to ogf/README.md')
