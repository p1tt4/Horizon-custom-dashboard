import logging
from re import match as re_match


logger = logging.getLogger(__name__)


def extract_object_id(http_request):
    """
    This method applies both for the `jobs` and `notifications` url
    :param http_request: the HTTP-Request object
    :return: the pattern matched or None
    """
    rex = r'^/custom_backup/(notifications/)?(?P<object_id>[a-z0-9-]{36})/(update|clone)$'
    m = re_match(rex, http_request.path)
    if not m:
        logger.warning("<object_id> not found in request.path {}".format(http_request.path))
        return None
    return m.groupdict().get('object_id')


def cmp_dict(dict1, dict2):
    """
    Recursively compare two dictionaries. Being that we iterate over dict1 it is safe to use the parentheses
    notation to access the value dict1[key], instead it is important to use the dict.get() method for dict2,
    to avoid KeyError exceptions.

    equal value is recomputed at each iteration using the AND operator because it guarantees that once it gets
    FALSE it will hold this value until the last iteration.
    :return:
    """
    if not (isinstance(dict1, dict) and isinstance(dict2, dict)):
        return False

    equal = True
    for k in dict1.keys():
        if isinstance(dict1[k], dict) and isinstance(dict1[k], dict):
            equal = equal and cmp_dict(dict1[k], dict2.get(k))
        else:
            equal = equal and (dict1[k] == dict2.get(k))
    return equal
