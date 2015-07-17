"""Print a list of contributors for a particular milestone.

Usage:

    python tools/contributor_list.py MILESTONE

"""

import sys
from gh_api import (
    get_milestone_id,
    get_pulls_list,
    get_issues_list,
)

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    milestone = sys.argv[1]

    milestone_id = get_milestone_id(
        "jupyter/nbgrader",
        milestone)

    issues = get_issues_list(
        "jupyter/nbgrader",
        state='all',
        milestone=milestone_id)

    pulls = get_pulls_list(
        "jupyter/nbgrader",
        state='merged',
        milestone=milestone_id)

    users = set()
    for issue in issues:
        users.add(issue['user']['login'])
    for pull in pulls:
        users.add(pull['user']['login'])

    users = {user.lower(): user for user in users}
    print()
    print("The following users have submitted issues and/or PRs:")
    print("-----------------------------------------------------")
    for user in sorted(users.keys()):
        print(users[user])
    print("-----------------------------------------------------")
