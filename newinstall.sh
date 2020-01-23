#!/bin/bash
cd -- $HOME || exit 1
sudo apt update
sudo apt upgrade
sudo ubuntu-drivers autoinstall
mkdir -v tmp
mkdir -v -p usr/bin
cd usr/bin || exit 1
sudo apt -y install git
git config --global user.name "Franco Egidi"
git config --global user.email "franco.egidi@gmail.com"
git config --list
sudo apt install openssh-server
# ssh-keygen -t rsa
# git clone https://github.com/Frankifisu/bin.git
sudo apt install -y vim
sudo apt install -y texlive-full
sudo apt install -y texmaker
sudo apt install -y chromium-browser
sudo apt install -y cmake
sudo apt install -y gfortran
sudo apt install -y mutt
cd ~ && wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf -
~/.dropbox-dist/dropboxd
