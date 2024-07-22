#!/bin/bash
cd -- $HOME || exit 1
sudo apt update
sudo apt upgrade
sudo ubuntu-drivers autoinstall
mkdir -v tmp
cd usr/bin || exit 1
sudo apt -y install git
git config --global user.name "Franco Egidi"
#git config --global user.email "franco.egidi@gmail.com"
git remote set-url origin git@github.com:Frankifisu/bin.git
git config --global alias.graph  "log --graph --decorate --pretty=oneline --abbrev-commit --branches --remotes --tags"
git config --global alias.pgraph "log --graph --decorate --pretty=oneline --abbrev-commit"
git config --global alias.revnum 'log -n 1 --format=format:%ad --date=format:"%y%m%d"'
git config --global merge.conflictstyle diff3
git config --global push.autoSetupRemote true
git config --global fetch.prune true
git config --global pack.windowMemory 1g
git config --list
sudo apt install openssh-server
# ssh-keygen -t rsa
mkdir -v ~/usr && cd ~/usr
git clone https://github.com/Frankifisu/bin.git
echo ' source $HOME/usr/bin/.muttrc' >> ~/.muttrc
echo ' source $HOME/usr/bin/.vimrc' >> ~/.vimrc
echo ' source $HOME/usr/bin/.bashrc' >> ~/.bashrc
sudo apt install -y vim mutt
sudo apt install -y texlive-full texmaker
sudo apt install -y chromium-browser
sudo apt install -y cmake gfortran
sudo apt install -y libblas-dev liblapack-dev
cd ~ && wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf -
~/.dropbox-dist/dropboxd
