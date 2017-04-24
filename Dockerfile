FROM debian:jessie-slim

MAINTAINER BlankOn Developer <blankon-dev@googlegroups.com>

# Environment for PyEnv purpose
ENV HOME /root
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

# Debian Deps
RUN apt-get update -qq && apt-get install -y -qqq make build-essential libssl-dev zlib1g-dev libbz2-dev \
	libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils sudo python \
	python-pip python-dev python-debian dpkg-dev rabbitmq-server git-core nginx libpq-dev dput pbuilder \
	git-core python-lzma python-chardet git vim

# Configure PyEnv for python 2.6.6 support
RUN curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash &&\
	/bin/bash -c "echo 'export PATH=\"$HOME/.pyenv/bin:${PATH}\"' >> ${HOME}/.bashrc" &&\
	/bin/bash -c "echo 'eval \"\$(pyenv init -)\"' >> ${HOME}/.bashrc" &&\
	/bin/bash -c "echo 'eval \"\$(pyenv virtualenv-init -)\"' >> ${HOME}/.bashrc" &&\
	/bin/bash -c "source ${HOME}/.bashrc" &&\ 
	pyenv install 2.6.6 &&\
	pyenv global 2.6.6 &&\
	mkdir ~/src/

WORKDIR ~/src/

# Clone the repo
RUN git clone git://github.com/BlankOn/python-irgsh.git &&\
	git clone git://github.com/BlankOn/irgsh-node.git

WORKDIR irgsh-node/

RUN ln -s ../python-irgsh/irgsh

# Bootstrap
RUN python bootstrap.py

# Small Hack for pyparsing and pip deps
RUN sed -i 's/(MARKER_EXPR())/(MARKER_EXPR)/' $HOME/.pyenv/versions/2.6.6/lib/python2.6/site-packages/packaging/requirements.py &&\
	rm -rf eggs/pyparsing* &&\
	pip uninstall pyparsing -y &&\
	pip install pyparsing &&\
	pip install pyparsing==1.5.7 || echo "Pyparsing Try 1 fails" &&\
	pip install pyparsing==1.5.7 || echo "Pyparsing Try 2 fails" &&\
	./bin/buildout


ENTRYPOINT ["/bin/bash"]


