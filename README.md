irgsh-node
==========

irgsh-node adalah pabrik pekerja dalam infrastruktur [pabrik
paket](http://irgsh.blankonlinux.or.id)
[BlankOn](http://www.blankonlinux.or.id).


Kebutuhan Administrasi
----------------------

1. Sertifikat SSL untuk pabrik paket, ditandatangani oleh CA Irgsh BlankOn.
2. Kunci SSH.
3. Akun di [Irgsh](http://irgsh.blankonlinux.or.id) yg dapat diperoleh
   dengan melampirkan:
    1. Judul sertifikat SSL
    2. Kunci publik SSH
    3. Nama pabrik
    4. Arsitektur pabrik

Kebutuhan Aplikasi
------------------

    $ sudo apt-get install python dput pbuilder git-core

Instalasi
---------

### Mendapatkan kode sumber

Kode sumber akan diambil langsung dari repositori di GitHub.

    $ git clone git://github.com/BlankOn/python-irgsh.git
    $ git clone git://github.com/BlankOn/irgsh-node.git
    $ cd irgsh-node
    $ ln -s ../python-irgsh/irgsh

### Menyiapkan `irgsh-node`

Instalasi `irgsh-node` akan disiapkan oleh skrip
[Buildout](http://www.buildout.org/) yang disertakan. Pustaka Python lain yang
dibutuhkan akan otomatis diunduh oleh Buildout.

    $ cd irgsh-node
    $ python bootstrap.py
    $ ./bin/buildout

Konfigurasi
-----------

### `irgsh-node`

Sunting berkas `irgsh-node.conf` dan atur nilai-nilai berikut.

* `irgsh`
  * `node-name` berisi nama pabrik, sesuai yang didaftarkan ke [Irgsh](http://irgsh.blankonlinux.or.id).
  * `arch` berisi arsitektur pabrik, misalnya `i386` atau `amd64`.
  * `ssl-cert` berisi path menuju berkas sertifikat SSL.
  * `ssl-key` berisi path menuju berkas kunci privat SSL.

### SSH

Sunting berkas `~/.ssh/config` dan tambahkan isian berikut.

    Host rani.blankonlinux.or.id
    HostName rani.blankonlinux.or.id
    Port 2222
    IdentityFile /path/menuju/kunci/privat/ssh.key

### sudo

Pastikan pengguna yang menjalankan irgsh-node dapat memanggil
`/usr/sbin/pbuilder` dengan sudo tanpa dimintai kata kunci. Contoh isi
`/etc/sudoers` (sunting dengan `visudo`).

    pabrik ALL=NOPASSWD: /usr/sbin/pbuilder

Eksekusi
--------

Ada dua buah aplikasi yang perlu dijalankan: pabrik `irgsh-node` dan pengunggah
`irgsh-uploader`.

### Pabrik

    $ cd irgsh-node
    $ ./bin/irgsh-node

### Pengunggah

    $ cd irgsh-node
    $ ./bin/irgsh-uploader

