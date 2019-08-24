#!/usr/bin/env bash

set -e

setup_demo () {
    # Setup JupyterHub config.
    setup_jupyterhub "${1}"

    # Create users.
    make_user instructor1
    make_user instructor2
    make_user grader-course101
    make_user student1

    # Install global nbgrader config file.
    cp global_nbgrader_config.py /etc/jupyter/nbgrader_config.py

    # Setup nbgrader configuration for grading account.
    setup_nbgrader grader-course101 course101_nbgrader_config.py
    create_course grader-course101 course101

    # Enable extensions for grading account.
    enable_create_assignment grader-course101
    enable_formgrader grader-course101

    # Enable extensions for instructors.
    instructors=(instructor1 instructor2)
    for instructor in ${instructors[@]}; do
        enable_assignment_list "${instructor}"
        enable_course_list "${instructor}"
    done

    # Enable extensions for student.
    enable_assignment_list student1
}
