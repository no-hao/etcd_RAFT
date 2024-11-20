# Jepsen Testing Environment for etcd

This repository contains the setup and configuration for running Jepsen tests on etcd, focusing on RAFT consensus testing.

## Prerequisites

- Docker Desktop
- Git
- Terminal access
- MacOS (tested) or Linux

## Initial Setup

1. Clone the repositories:

```bash
git clone https://github.com/your-username/etcd_rust.git
cd etcd_rust
git clone https://github.com/jepsen-io/jepsen.git
```

# Docker Configuration

Navigate to the Jepsen docker directory:

```bash
cd jepsen/docker/control
```

## Create or modify the Dockerfile with these contents:

```
FROM jgoerzen/debian-base-minimal:bookworm as debian-addons
FROM debian:bookworm-slim

COPY --from=debian-addons /usr/local/preinit/ /usr/local/preinit/
COPY --from=debian-addons /usr/local/bin/ /usr/local/bin/
COPY --from=debian-addons /usr/local/debian-base-setup/ /usr/local/debian-base-setup/

RUN run-parts --exit-on-error --verbose /usr/local/debian-base-setup

ENV container=docker
STOPSIGNAL SIGRTMIN+3

ENV LEIN_ROOT true

# Install Java 17 and other dependencies
RUN apt-get -qy update && \
    apt-get -qy install \
        curl dos2unix emacs git gnuplot graphviz htop iputils-ping libjna-java \
        openjdk-17-jdk-headless pssh screen vim wget && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME for Java 17
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Install Leiningen
RUN curl -o /usr/local/bin/lein https://raw.githubusercontent.com/technomancy/leiningen/stable/bin/lein && \
    chmod 0755 /usr/local/bin/lein && \
    mkdir -p /root/.lein && \
    /usr/local/bin/lein

# Copy Jepsen
COPY jepsen/jepsen /jepsen/jepsen/
RUN if [ -f /jepsen/jepsen/project.clj ]; then cd /jepsen/jepsen && lein install; fi
COPY jepsen /jepsen/

ADD ./bashrc /root/.bashrc
ADD ./init.sh /init.sh
RUN dos2unix /init.sh /root/.bashrc \
    && chmod +x /init.sh

CMD /init.sh
```

# Building and Running

## Build the Docker images:

```bash
cd ../  # Back to docker directory
./bin/build-docker-compose
```

## Start the jepsen cluster:

```bash
./bin/up
```

## Connect to the control node:

```bash
docker exec -it jepsen-control bash
```

# Setting Up etcd Tests

## Inside the control node:

```bash
cd /jepsen
git clone https://github.com/jepsen-io/etcd.git
cd etcd
```

## Modify the project.clj:

```clojure
(defproject jepsen.etcd "0.2.4"
  :description "etcd Jepsen test"
  :url "https://github.io/jepsen/etcd"
  :license {:name "EPL-2.0 OR GPL-2.0-or-later WITH Classpath-exception-2.0"
            :url "https://www.eclipse.org/legal/epl-2.0/"}
  :dependencies [[org.clojure/clojure "1.11.1"]
                 [jepsen "0.3.4"
                  :exclusions [com.fasterxml.jackson.core/jackson-core]]
                 [tech.droit/clj-diff "1.0.1"]
                 [io.etcd/jetcd-core "0.7.5"
                  :exclusions [
                               io.netty/netty-codec-http2
                               io.netty/netty-handler-proxy
                  ]]
                 [io.netty/netty-codec-http2 "4.1.100.Final"]
                 [io.netty/netty-handler-proxy "4.1.100.Final"]
                 [cheshire "5.11.0"]]
  :java-source-paths ["src/java"]
  :javac-options ["-target" "17" "-source" "17"]
  :jvm-opts ["-Djava.awt.headless=true"
             "-server"
             "-Xmx72g"
             "-XX:-OmitStackTraceInFastThrow"]
  :repl-options {:init-ns jepsen.etcd}
  :main jepsen.etcd
  :profiles {:uberjar {:target-path "target/uberjar"
                       :aot :all}})
```

# Running Tests

## Basic test:

```bash
lein run test --workload register --time-limit 60
```

## Test with network partitions:

```bash
lein run test --workload register --nemesis partition,clock --time-limit 60
```

## Full test suite:

```bash
lein run test-all --concurrency 10 --rate 1000
```
