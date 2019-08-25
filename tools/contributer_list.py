#!/usr/bin/env python
"""Print a list of contributors for a particular milestone.

Usage:

    python tools/contributor_list.py [MILESTONE] [MILESTONE] ...

"""

import sys
from gh_api import (
    get_milestone,
    get_milestones,
    get_milestone_id,
    get_issues_list,
)

if __name__ == "__main__":

    if len(sys.argv) < 2:
        milestones = get_milestones("jupyter/nbgrader", auth=True)
    else:
        milestones = [get_milestone("jupyter/nbgrader", milestone_id, auth=True)
                      for milestone_id in sys.argv[1:]]

    users = set()
    for milestone in milestones:
        if milestone['title'] == "No action":
            continue

        print("Getting users for {}...".format(milestone['title']))

        # this returns both issues and PRs
        issues = get_issues_list(
            "jupyter/nbgrader",
            state='all',
            milestone=milestone['number'],
            auth=True)

        for issue in issues:
            users.add(issue['user']['login'])

    users = {user.lower(): user for user in users}
    print()
    print("The following users have submitted issues and/or PRs:")
    print("-----------------------------------------------------")
    for user in sorted(users.keys()):
        print("- {}".format(users[user]))
    print("-----------------------------------------------------")
