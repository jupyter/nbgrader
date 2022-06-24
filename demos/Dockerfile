# Dockerfile for running / testing demos
# build: `docker build -t nbgrader-demo .`
# build and run: `docker build -t nbgrader-demo . && docker run --rm -it -p 8000:8000 nbgrader-demo`
# run a demo without rebuilding by mounting the demo dir as a volume (e.g. if you are editing the demos):
# docker run --rm -it -p 8000:8000 -v $PWD:/root nbgrader-demo /root/restart_demo.sh demo_multiple_classes

FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get -y dist-upgrade \
 && apt-get -y install git sudo
# cache some of the bigger installs
RUN apt-get -y install python3-pip nodejs npm
RUN python3 -m pip install --upgrade jupyterhub notebook nbclassic
RUN git clone https://github.com/jupyter/nbgrader /srv/nbgrader/nbgrader
# COPY is like deploy_demos.sh
COPY ./ /root/
WORKDIR /root
CMD /root/restart_demo.sh demo_one_class_multiple_graders
EXPOSE 8000
