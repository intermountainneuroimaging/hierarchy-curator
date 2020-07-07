#!/usr/bin/env sh

set -eu
unset CDPATH
cd "$( dirname "$0" )/../.."


USAGE="
Usage:
    $0 [OPTION...] [[--] PYTEST_ARGS...]

Runs all tests and black-linting.

Assumes running in test container or that gear_toolkit and all of its
dependencies are installed.

Options:
    -h, --help              Print this help and exit

    -s, --shell             Enter shell instead of running tests
    -b, --black-only        Run black only
    -d, --doc-only          Run sphinx-build doc only
    -B, --skip-black        Black linting
    -D, --skip-doc          Skip sphinx-build doc
    -- PYTEST_ARGS          Arguments passed to py.test

"


main() {
    export PYTHONDONTWRITEBYTECODE=1
    export PYTHONPATH=.
    local BLACK_TOGGLE=
    local DOC_TOGGLE=

    while [ $# -gt 0 ]; do
        case "$1" in
            -h|--help)
                log "$USAGE"
                exit 0
                ;;
            -s|--shell)
                sh
                exit
                ;;
            -b|--black-only)
                BLACK_TOGGLE=true
                ;;
#            -d|--doc-only)
#                DOC_TOGGLE=true
#                ;;
            -B|--skip-black)
                BLACK_TOGGLE=false
                ;;
#            -D|--skip-doc)
#                DOC_TOGGLE=false
#                ;;
            --)
                shift
                break
                ;;
            *)
                break
                ;;
        esac
        shift
    done

    log "INFO: Cleaning pyc and previous coverage results ..."
    find . -type d -name __pycache__ -exec rm -rf {} \; || true
    find . -type f -name '*.pyc' -delete
    rm -rf .coverage htmlcov
    rm -rf docs/build

    if [ "$BLACK_TOGGLE" != true -a "$DOC_TOGGLE" != true ]; then
        log "INFO: Running tests ..."
        pytest tests --exitfirst --cov=custom_curator --cov-report= "$@"

        log "INFO: Reporting coverage ..."
        local COVERAGE_ARGS="--skip-covered"
        coverage report --show-missing $COVERAGE_ARGS
        coverage html $COVERAGE_ARGS
    fi

#    if [ "$DOC_TOGGLE" != false -a "$BLACK_TOGGLE" != true ]; then
#        log "INFO: Running sphinx-build ..."
#        sphinx-build docs/source docs/build/html
#    fi

    if [ "$BLACK_TOGGLE" != false -a "$DOC_TOGGLE" != true ]; then
        log "INFO: Running black --check ..."
        black --check --diff .
    fi
}

log() {
    printf "\n%s\n" "$@" >&2
}


main "$@"
