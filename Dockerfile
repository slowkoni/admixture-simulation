# Start from a recent release of the 14.04 ubuntu distribution
FROM ubuntu:14.04.5

MAINTAINER Mark Koni Wright <markoni.wright@gmail.com>
LABEL version="0.04"

# Update base distribution and install needed packages
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq -y && apt-get upgrade -qq -y
RUN apt-get install -qq -y git pkg-config python python-all time

ARG UID=1000
RUN useradd --non-unique -u $UID --home /home/admixture-simulation --user-group --create-home --shell /bin/bash admixture-simulation
ADD . /home/admixture-simulation

RUN mkdir -p /home/admixture-simulation/shared
RUN chown -R admixture-simulation:admixture-simulation /home/admixture-simulation

USER admixture-simulation
WORKDIR /home/admixture-simulation

#RUN git clone https://github.com/slowkoni/rfmix.git
#WORKDIR rfmix
#RUN autoreconf --force --install && ./configure && make
WORKDIR /home/admixture-simulation
#RUN gunzip hapmap-phase2-genetic-map.tsv.gz

ENV PATH="/home/admixture-simulation/bin:${PATH}"
ENTRYPOINT ["./do-admixture-simulation.py"]
