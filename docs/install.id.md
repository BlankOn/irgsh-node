Petunjuk Instalasi
==================

Persiapan Administrasi
----------------------

1. Buat sertifikat SSL yang ditandatangani oleh CA Irgsh BlankOn.
2. Buat kunci SSH.
3. Minta akun di Irgsh dengan melampirkan:
   * judul sertifikat SSL,
   * kunci publik SSH, dan
   * nama pabrik.


Kebutuhan
---------

1. Python 2.5.2 atau lebih baru
2. dput
3. pbuilder
4. git (untuk mengambil kode sumber)
5. dpkg-dev
6. fakeroot

Bagi pengguna sistem operasi berbasis Debian, jalankan perintah berikut
untuk memasang kebutuhan di atas.

    $ sudo apt-get install python dput pbuilder git-core dpkg-dev fakeroot


Instalasi
---------

### Unduh kode sumber

    $ git clone git://github.com/fajran/python-irgsh.git
    $ git clone git://github.com/fajran/irgsh-node.git
    $ cd python-irgsh
    $ git branch refactor origin/refactor
    $ git checkout refactor
    $ cd ../irgsh-node
    $ git branch celery origin/celery
    $ git checkout celery
    $ ln -s ../python-irgsh/irgsh

### Persiapkan kode sumber

    $ python bootstrap.py
    $ ./bin/buildout


Konfigurasi
-----------

Sunting berkas `irgsh-node.py` dan atur nilai berikut.

* `irgsh`
   * **node-name** berisi nama pabrik yang didaftarkan ke Irgsh.
   * **arch** berisi arsitektur pabrik, misalnya `i386` atau `amd64`.
   * **ssl-cert** berisi path menuju berkas sertifikat SSL
   * **ssl-key** berisi path menuju berkas kunci privat SSL

Sunting berkas `~/.ssh/config` dan tambahkan isian berikut.

    Host upload.irgsh.dahsy.at
    HostName upload.irgsh.dahsy.at
    IdentityFile /path/menuju/kunci/privat/ssh.key


Eksekusi
--------

### Pabrik

    $ cd irgsh-node
    $ ./bin/irgsh-celery

### Pengunggah

    $ cd irgsh-node
    $ ./bin/irgsh-uploader

