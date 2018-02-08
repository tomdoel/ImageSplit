# coding=utf-8
"""
Utility files for constructing a version string

Author: Tom Doel
Copyright UCL 2017

"""


def get_version_string():
    """
    Return a user-visible string describing the name and product version

    This is a safe function that will never throw an exception
    """

    version_string = get_version()
    if not version_string:
        version_string = "unknown"

    return "ImageSplit version " + version_string


def get_version():
    """
    Return a user-visible string describing the product version

    This is a safe function that will never throw an exception
    """

    # Attempt to get the version string from the git repository
    _, version_string, _ = get_git_version()

    # If we cannot get a git version, attempt to get a package version
    if not version_string:
        try:
            import pkg_resources
            version_string = \
                pkg_resources.get_distribution("imagesplit").version
        except:  # pylint: disable=bare-except
            version_string = None

    return version_string


def get_git_version():
    """Return a version string based on the git repo, conforming to PEP440"""

    from subprocess import check_output

    # Describe the version relative to last tag
    command_git = ['git', 'describe', '--match', 'v[0-9]*']
    try:
        version_buf = check_output(
            command_git, stderr=open('/dev/null', 'w')).rstrip()

        # Exclude the 'v' for PEP440 conformity, see
        # https://www.python.org/dev/peps/pep-0440/#public-version-identifiers
        version_buf = version_buf[1:]

        # Split the git describe output, as it may not be a tagged commit
        tokens = version_buf.split('-')
        if len(tokens) > 1:  # not a tagged commit
            # Format a developmental release identifier according to PEP440,
            # see:
            # https://www.python.org/dev/peps/pep-0440/#developmental-releases
            version_git = '{}.dev{}'.format(tokens[0], tokens[1])
        elif len(tokens) == 1:  # tagged commit
            # Format a public version identifier according to PEP440, see:
            # https://www.python.org/dev/peps/pep-0440/#public-version-identifiers
            version_git = tokens[0]
        else:
            raise ValueError('Unexpected "git describe" output:'
                             '{}'.format(version_buf))
    except:  # pylint: disable=bare-except
        version_buf = None
        version_git = None

    return version_buf, version_git, command_git
