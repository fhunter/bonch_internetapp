all: deb

tree: internet.py internet.desktop control
	mkdir -p target
	mkdir -p target/DEBIAN
	mkdir -p target/usr/share/applications/
	mkdir -p target/usr/bin
	cp control target/DEBIAN
	cp internet.py target/usr/bin/
	cp internet.desktop target/usr/share/applications/

deb: tree
	fakeroot dpkg -b ./target/ ./
