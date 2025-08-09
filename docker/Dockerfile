FROM ubuntu:20.04

ARG DOCKER_SERVER_ROOT_DIR
WORKDIR ${DOCKER_SERVER_ROOT_DIR}

ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NOWARNINGS="yes"
RUN apt-get update && apt-get install -y \
    mc \
    htop \
    gdb \
    expect-dev \
    zip \
    libcurl4-gnutls-dev \
    libphysfs-dev \
    tzdata \
    && dpkg-reconfigure -f noninteractive tzdata \
    && ln -fs /usr/share/zoneinfo/Europe/Kiev /etc/localtime \
    && mkdir /usr/local/ssl \
    && ln -s '/etc/ssl/certs' /usr/local/ssl/certs \
    && echo "set auto-load safe-path /" > $HOME/.gdbinit \
    && ln -fs /usr/lib/x86_64-linux-gnu/libffi.so.7 /usr/lib/x86_64-linux-gnu/libffi.so.6

# python _ctypes.so requires libffi.so.6