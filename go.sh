#!/bin/sh
# -*- coding: utf-8; -*-

# Copyright (C) 2012, 2013, 2014 Johan Andersson
# Copyright (C) 2013, 2014 Sebastian Wiesner
# Copyright (C) 2017 Ola Nilsson

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with GNU Emacs; see the file COPYING.  If not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA 02110-1301, USA.

# Install Cask

: ${TARGET_DIRECTORY:=$HOME/.cask}
: ${REPOSITORY:=https://github.com/snogge/cask.git}
ISSUE_TRACKER=https://github.com/snogge/cask/issues

OKGREEN="\033[32m"
FAIL="\033[31m"
ENDC="\033[0m"

success() {
	echo ${OKGREEN}$*${ENDC}
	exit 0
}

fail() {
	echo ${FAIL}$*${ENDC}
	exit 1
}

bootstrap_cask() {
	cask=$1/bin/cask.sh
	$cask upgrade-cask || fail "Cask could not be bootstrapped. Try again later, or report an issue at $ISSUE_TRACKER."
}

install_cask() {
	target_directory=$1
	[ -d $target_directory ] &&
		fail "Directory $target_directory exists. Is Cask already installed?"
	command -p -v git >/dev/null ||
		fail "git executable not found. Please install Git."
	git clone ${REPO_BRANCH:+-b $REPO_BRANCH} $branch $REPOSITORY $target_directory ||
		fail "Cask could not be installed. Try again later or report an issue at $ISSUE_TRACKER."
   
}

install_cask $TARGET_DIRECTORY
bootstrap_cask $TARGET_DIRECTORY
success "Successfully installed Cask! Now, add the cask binary to your \$PATH:
  export PATH=\$TARGET_DIRECTORY/bin:\$PATH"
