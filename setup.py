#!/usr/bin/python

from setuptools import setup

def get_version():
    import irgsh_node
    return irgsh_node.__version__

packages = ['irgsh_node', 'irgsh_node.conf']

setup(name='irgsh-node', 
      version=get_version(),
      description='irgsh builder',
      url='http://irgsh.blankonlinux.or.id',
      packages=packages,
      maintainer='BlankOn Developers',
      maintainer_email='blankon-dev@googlegroups.com',
      entry_points={'console_scripts': ['irgsh-node = irgsh_node.main:main',
                                        'irgsh-celery = irgsh_node.main_celery:main',
                                        'irgsh-uploader = irgsh_node.uploader:main']},
      install_requires=['setuptools', 'python-debian', 'celery', 'amqplib',
                        'sqlalchemy', 'poster'],
     )
