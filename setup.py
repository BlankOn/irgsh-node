#!/usr/bin/python

from setuptools import setup

def get_version():
    import irgsh_node
    return irgsh_node.__version__

packages = ['irgsh_node', 'irgsh_node.conf', 'irgsh_node.localqueue',
            'irgsh_node.amqplibssl', 'irgsh_node.amqplibssl.client_0_8']

setup(name='irgsh-node', 
      version=get_version(),
      description='Irgsh Package Builder',
      url='http://irgsh.blankonlinux.or.id',
      packages=packages,
      maintainer='BlankOn Developers',
      maintainer_email='blankon-dev@googlegroups.com',
      entry_points={'console_scripts': ['irgsh-node = irgsh_node.main:main',
                                        'irgsh-uploader = irgsh_node.uploader:main']},
      install_requires=['setuptools', 'python-debian', 'celery>=2.2',
                        'sqlalchemy', 'poster'],
     )
