ll = """
THE_PO_IN
STEP_SMALL_SUBTRACT_ROW
STEP_SMALL_SUBTRACT_COLUMN
DRAW_LINES
TEST_FOR_OPTIMALITY
THE_PO_ZE
HERE_GIVE
HERE_MAX
"""

import os

for l in ll.split():
    fl = f"{l.lower()}.html"
    if not os.path.exists(fl):
        with open(fl, 'w') as f:
            f.write("<div></div>")
