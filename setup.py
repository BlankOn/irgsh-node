#!/usr/bin/python

from setuptools import setup

def get_version():
    import irgsh_node
    return irgsh_node.__version__

setup(name='irgsh-node', 
      version=get_version(),
      description='irgsh builder',
      url='http://irgsh.blankonlinux.or.id',
      packages=['irgsh_node'],
      maintainer='BlankOn Developers',
      maintainer_email='blankon-dev@googlegroups.com',
      entry_points={'console_scripts': ['irgsh-node = irgsh_node.main:main',
                                        'irgsh-celery = irgsh_node.worker:main']},
      install_requires=['setuptools', 'python-debian', 'celery', 'amqplib'],
     )
