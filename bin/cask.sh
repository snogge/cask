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

#set -x

case $subcommand in
	install|pkg-file|update|build|clean-elc|eval|exec-path|files|\
	help|info|init|link|list|load-path|outdated|package|\
	package-directory|path|upgrade|upgrade-cask|version)
		cli=$CASK_DIRECTORY/cask-cli.el
		$CASK_EMACS -Q --script $cli -- $subcommand $*
		;;
	emacs)
		EMACSLOADPATH=$($CASK load-path)
		xPATH=$($CASK path)
		EMACSLOADPATH=$EMACSLOADPATH PATH=$xPATH EMACS=$CASK_EMACS $CASK_EMACS $*
		;;   
	exec)
		EMACSLOADPATH=$($CASK load-path)
		xPATH=$($CASK path)
		EMACSLOADPATH=$EMACSLOADPATH PATH=$xPATH EMACS=$CASK_EMACS $*
		;;
esac

exit $?

# Parse command line options.
while getopts hvo: OPT; do
    case "$OPT" in
        h)
            echo $USAGE
            exit 0
            ;;
        v)
            echo "`basename $0` version 0.1"
            exit 0
            ;;
        o)
            OUTPUT_FILE=$OPTARG
            ;;
        \?)
            # getopts issues an error message
            echo $USAGE >&2
            exit 1
            ;;
    esac
done

# Remove the switches we parsed above.
shift `expr $OPTIND - 1`

# We want at least one non-option argument. 
# Remove this block if you don't need it.
if [ $# -eq 0 ]; then
    echo $USAGE >&2
    exit 1
fi

# Access additional arguments as usual through 
# variables $@, $*, $1, $2, etc. or using this loop:
for PARAM; do
    echo $PARAM
done

# EOF
