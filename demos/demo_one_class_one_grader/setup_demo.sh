#!/usr/bin/env bash

set -e

setup_demo () {
    # Setup JupyterHub config.
    setup_jupyterhub "${1}"

    # Create users.
    make_user instructor1
    make_user student1

    # Setup instructor nbgrader configuration.
    setup_nbgrader instructor1 instructor_nbgrader_config.py
    create_course instructor1 course101

    # Enable extensions for instructor.
    enable_create_assignment instructor1
    enable_formgrader instructor1
    enable_assignment_list instructor1

    # Enable extensions for student.
    enable_assignment_list student1
}
