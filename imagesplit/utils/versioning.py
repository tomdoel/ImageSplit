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


def version_from_versioneer():
    """Return a version string based on the git repo, conforming to PEP440"""

    # Attempt to get the version string from the git repository
    try:
        from .versioneer_version import get_versions
        version_info = get_versions()
        if version_info['error'] is None:
            return version_info['version']
        return None
    except:  # pylint: disable=bare-except
        return None


def _check_pip_version(version_string):
    return bool(re.match(PIP_VERSION_REGEX, version_string))


def get_version():
    """
    Return a user-visible string describing the product version

    This is a safe function that will never throw an exception
    """

    version_string = version_from_versioneer()

    if not version_string:
        version_string = version_from_pip()

    return version_string
