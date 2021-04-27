FROM ubuntu

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Setup timezone
RUN ln -snf /usr/share/zoneinfo/Etc/UTC /etc/localtime \
    && echo "Etc/UTC" > /etc/timezone

RUN apt-get update && apt-get install -y git make graphviz curl python3 python3-distutils python3-apt
# setup git so we can use it with poetry later
RUN git config --global user.name "Your Name" && git config --global user.email "you@example.com"
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3 -
# poetry will be installed by adding a line to .profile which is loaded by bash
# login shells. to access it, we'll need to wrap any calls to it with `bash -l -c`.

# for discoverability, add the virtual environment in the project directory instead of
# somewhere in ~/.cache
RUN bash -l -c "poetry config virtualenvs.in-project true"

# install common text editors for convenience
RUN apt-get install -y vim nano

WORKDIR /root/artifact
COPY . .

RUN bash -l -c 'make install'

# a quick example log for the benchmarks
RUN bash -l -c 'poetry run kipro2_benchmark run geo > benchmarks/geo.log 2>&1'

WORKDIR /root/
COPY cav_artifact/README.md .
COPY latticed_k_induction_cav21.pdf .

# Enter poetry shell in /root/artifact, but then go up one directory and start a shell
CMD bash /root/artifact/cav_artifact/hello.sh
