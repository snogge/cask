#!/bin/sh

CASK=$0
CASK_BIN_DIR=${CASK%/*}
CASK_DIRECTORY=${CASK_BIN_DIR%/*}

# Find which emacs to use
[ "$CASK_EMACS" ] || {
	case $INSIDE_EMACS in
		t|24*)
			CASK_EMACS=emacs
		;;
		*)
			CASK_EMACS=${EMACS:-emacs}
		;;
	esac }
[ "$CASK_EMACS" ] || {
	echo No CASK_EMACS found
	exit 1
}

USAGE="Usage: ${0##*/} [-hv] [-o arg] args"

if [ "$#" = "0" ] ; then
	# default command is install
	subcommand=install
else
	subcommand=$1
	shift
fi

case $subcommand in
	emacs)
		EMACSLOADPATH=$($CASK load-path)
		xPATH=$($CASK path)
		EMACSLOADPATH=$EMACSLOADPATH PATH=$xPATH EMACS=$CASK_EMACS $CASK_EMACS "$@"
		;;   
	exec)
		EMACSLOADPATH=$($CASK load-path)
		xPATH=$($CASK path)
		EMACSLOADPATH=$EMACSLOADPATH PATH=$xPATH EMACS=$CASK_EMACS "$@"
		;;
	*)
		cli=$CASK_DIRECTORY/cask-cli.el
		$CASK_EMACS -Q --script $cli -- $subcommand "$@"
		;;
esac

