# nbgrader with JupyterHub demos

This directory contains a few example demonstrating how to configure nbgrader to
run with JupyterHub. In all cases, it is assumed that you are running JupyterHub
directly a single server (i.e. these demos do not cover distributed or
containerized setups).

1. `demo_one_class_one_grader`: a demo showing how to configure nbgrader if you
   only have a single class with only one grader. The instructor account is
   called `instructor1` and the student account is `student1`.
2. `demo_one_class_multiple_graders`: a slightly more complex setup, in which
   you have multiple graders for the same class. There are accounts for
   `instructor1`, `instructor2`, and `student1`.
3. `demo_multiple_classes`: the most complex setup, in which you have multiple
   classes on the same machine (possibly with multiple different graders per
   class as well). There are accounts for `instructor1` (who grades for
   `course101`), `instructor2` (who grades for `course123`), and `student1` (who
   by default is not enrolled in any classes).

## Usage

:warning: :rotating_light: **IMPORTANT NOTE** :rotating_light: :warning: these
    demos take **destructive actions** like reinstalling Jupyter, deleting user
    accounts, and wiping home directories. Only run the demos if you do not care
    what happens to your server!

:warning: :rotating_light: **IMPORTANT NOTE** :rotating_light: :warning: this is
    not meant to be a useable deployment of JupyterHub, and does not include
    important configuration such as SSL. These demos should be used as
    references only to help you get nbgrader set up for your full deployment.

To run a demo, you will need root access to a server (let's call it
`demo-server`). From your laptop, run:

```
./deploy_demos.sh root@demo-server
```

This will install the demo files on your server. Then, SSH to the server and run
the `restart_demo.sh` script to actually launch the demo. For example, to run
`demo_one_class_one_grader`:

```
ssh root@demo-server
./restart_demo.sh demo_one_class_one_grader
```

If all goes well, you should then be able to access JupyterHub from port 8000 on
your demo server. The passwords for the accounts are the same as the usernames.
