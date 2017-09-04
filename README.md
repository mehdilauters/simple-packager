# simple-packager
this is a simple debian package creator from a json description file

It reads package configuration from a json file.
install:
````
git clone git@github.com:mehdilauters/simple-packager.git
cd simple-packager
./main.py -p simple-packager.json -o /tmp/package.deb
sudo dpkg -i /tmp/package.deb
simple-packager -h
````