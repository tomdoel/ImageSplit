# coding=utf-8
"""
Utility files for constructing a version string

Author: Tom Doel
Copyright UCL 2017

"""
import os

import re

VERSION_TAG_REGEX = '^v[0-9.]+(dev)?$'

# Could be pip install from repository, leading to local version identifiers
PIP_VERSION_REGEX = \
    r'^[0-9.]+(dev)?(\+[0-9]+\.g[A-Fa-f0-9]+(?:.dirty|.broken)?)?$'


VERSION_TAG_GLOB = 'v[0-9]*'  # Don't confuse with regex; matches v+digit+...
HASH_REGEX = '^g[A-Fa-f0-9]+$'  # git describe prefixes hash with 'g'


def _get_module_path():
    """Return the path to this module"""

    return os.path.dirname(os.path.realpath(__file__))


def get_version_string():
    """
    Return a user-visible string describing the name and product version

    This is a safe function that will never throw an exception
    """

    version_string = get_version()
    if not version_string:
        version_string = "unknown"

    return "ImageSplit version " + version_string


def _run_describe(dir_in_repo):
    from subprocess import check_output, CalledProcessError

    command_git = ['git', 'describe', '--always', '--dirty',
                   '--match', VERSION_TAG_GLOB]
    try:
        describe_output = check_output(
            command_git, stderr=open('/dev/null', 'w'), cwd=dir_in_repo
        ).rstrip()

        try:
            # convert bytes object if necessary (depends on Python version)
            describe_output = describe_output.decode('utf-8')
        except AttributeError:
            pass

        return describe_output

    except CalledProcessError:
        return None


#  pylint: disable=too-many-return-statements
def _parse_describe(describe_output, default_version):
    if not describe_output:
        return None

    tokens = describe_output.split('-')

    # If the first token is a hash, then we assume there is no tag. So we
    # take the default version and append the output, which may include
    if re.match(HASH_REGEX, tokens[0]):
        if len(tokens) == 1:
            return default_version + '+0.' + tokens[0]
        if len(tokens) > 2 or not \
                (tokens[1] == 'dirty' or tokens[1] == 'broken'):
            return None
        return default_version + '+0.' + tokens[0] + '.' + tokens[1]

    # Otherwise the first token should be a valid version tag
    if not re.match(VERSION_TAG_REGEX, tokens[0]):
        return None

    # Strip out the 'v' prefix from the version tag
    version_string = tokens[0][1:]

    # If there are no other tokens, this is an exact tag
    if len(tokens) == 1:
        return version_string

    # Otherwise we should have at 3 or 4 tokens: tag-dist-hash (-dirty/broken)
    if len(tokens) < 3 or len(tokens) > 4:
        return None

    # Second token must be commit distance from tag
    if not re.match("^[0-9]+$", tokens[1]):
        return None

    # Third token must be a hash
    if not re.match(HASH_REGEX, tokens[2]):
        return None

    # Three tokens means not dirty or broken
    if len(tokens) == 3:
        return '{}+{}.{}'.format(version_string, tokens[1], tokens[2])

    # Fourth token must be dirty or broken
    if not (tokens[3] == 'dirty' or tokens[3] == 'broken'):
        return None

    return '{}+{}.{}.{}'.format(version_string, tokens[1], tokens[2], tokens[3])


def version_from_git(default):
    """Return a version string based on the git repo, conforming to PEP440"""

    return _parse_describe(_run_describe(_get_module_path()), default)


def version_from_pip():
    """Return a version string based on the git repo, conforming to PEP440"""

    try:
        import pkg_resources
        version_string = pkg_resources.get_distribution("imagesplit").version
        if _check_pip_version(version_string):
            return version_string
        return None
    except:  # pylint: disable=bare-except
        return None


def _check_pip_version(version_string):
    return bool(re.match(PIP_VERSION_REGEX, version_string))


def get_version(default='0.0'):
    """
    Return a user-visible string describing the product version

    This is a safe function that will never throw an exception
    """

    version_string = version_from_git(default)

    if not version_string:
        version_string = version_from_pip()

    return version_string
