#!/usr/bin/env python
"""Print a list of merged PRs for a given milestone.

Usage:

    python tools/changelog.py MILESTONE

"""

import sys
from gh_api import (
    get_milestone_id,
    get_pulls_list
)

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    milestone = sys.argv[1]

    all_pulls = get_pulls_list(
        "jupyter/nbgrader",
        state='closed',
        auth=True)

    pulls = []
    for pr in all_pulls:
        if pr['milestone']['title'] == milestone and pr['merged_at']:
            pulls.append(pr)

    print()
    print("The following PRs were merged for the {} milestone:".format(milestone))
    print("-----------------------------------------------------")
    for pull in pulls:
        print("- PR #{}: {}".format(pull['number'], pull['title']))
    print("-----------------------------------------------------")
