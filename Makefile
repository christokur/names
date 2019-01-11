#
# names - a python module implementing the ASIM naming convention
#

.PHONY: all check clean lint 

all:	check
	./names.py gridscape.csv gridscape.txt

check:
	# --full-trace --verbose
	pytest --capture=no --doctest-modules --maxfail=1 \
		--hypothesis-show-statistics names.py

clean:
	@echo skip

lint:
	flake8 names.py

pylint: # pylint is a bit of a fascist so its unused for now
	pylint names.py

# 
commit-check:
	@if [ "`fossil extras`" != "" ]; \
	then echo "fossil extras != ''" ;  fossil extras ;  exit 1 ; \
	fi
#
# The setup is:
#
# 1. ~/Desktop/github/ohm - contains a checkedout version of ohm from github that
#    stephen has kindly setup. (This is a private repo for now)
#
# 2. ~/Desktop/FOSSILS/ohm.fossil - contains the project fossil
#
# Note that this currently exports the current version into the trunk
# branch.
#

FOSSIL=~/Desktop/names/ohm.fossil
GIT=~/Desktop/github/ohm

# tests - disabled for now for export-git
.export-git:  
	cd $(GIT) ; fossil export --git $(FOSSIL) | git fast-import
	cd $(GIT) ; git push -u origin pjm
	cd $(GIT) ; git push --tags



# tarballs and zipfile creation

.PHONY: tarballs

tarballs:
	fossil tarball tip names.tgz
	fossil zip tip names.zip


