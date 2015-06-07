import dataset
from stuf import stuf
import ConfigParser
import re
import string
import random
import hashlib
from flask import jsonify

config = ConfigParser.ConfigParser()
config.read('main.cfg')

mysql_uri = 'mysql://{user}:{pw}@{host}/{db}'


def cnf(section, value, default=False):
    """
        Wrapper for ConfigParser. Use default argument to allow
        cnf() to fallback to another variable if it doesn't exist
        within the configuration file. Also note that it will
        return a string, regardless of what's in the configuration
        file, so you will need to parse lists yourself.
    """
    try:
        _val = config.get(str(section), str(value))
        if not _val:
            return default
        return _val
    except:
        return default


def db():
    """
        Simplification wrapper for dataset.connect(). Yields
        database session, will throw an exception if any of the
        parameters are incorrect. MySQL, SQLite, and PostgreSQL
        natively.
    """
    return dataset.connect(mysql_uri.format(
        user=cnf('Database', 'username'),
        pw=cnf('Database', 'password'),
        host=cnf('Database', 'hostname'),
        db=cnf('Database', 'database')
    ), row_type=stuf)


def table(name, key="String"):
    """
        Simplification wrapper for dataset.Table.get_table(). Yields
        table, and creates it within the database if it doesn't exist
        yet.
    """
    return db().get_table(str(name), primary_type=key)


def counter(link=None, cur=0):
    """
        increments page and url counters, should be ran in the background,
        to keep TTFB faster.
    """
    if link:
        cur += 1
        table("urls").upsert(dict(id=str(link), hits=cur), ['id'])
    else:
        count = table("stats").find_one(id="hits")
        count = int(count.count) + 1 if count else 1
        table("stats").upsert(dict(id="hits", count=count), ['id'])


def valid_url(url):
    """
        Provides link/url based validation for incoming URL's, as
        many different characters can be contained in a URL, this
        also includes IP-based links.
    """
    if re.match(r'(?i)\/\/(?:www)?\.links\.ml', url) or len(url) < 1:
        return False
    regex = re.compile(
        r'^http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        re.IGNORECASE)
    if re.match(regex, url.strip()):
        return True
    else:
        return False


def valid_uri(text):
    """ Provides rough regex validation for incoming ID's """
    text = str(text)
    if re.match(r'^[0-9A-Za-z]+$', text):
        return True
    else:
        return False


def new_uuid():
    """
        Generates a unique ID of given key length uses only basic
        ASCII characters. (A-Z, a-z, 0-9)
    """
    return "".join([random.choice(string.letters + string.digits) for n in xrange(cnf("General", "keylength", 4))])


def hash(text):
    """ Generates a SHA256 string based on the input text. """
    return str(hashlib.sha256(str(text)).hexdigest())


def err(msg):
    """
        returns a erronous flask-based return request, used mainly
        for various API requests.
    """
    return jsonify({"success": False, "message": str(msg)}), 400


def success(**kwargs):
    """
        returns a successful flask-based return request, used mainly
        for various API requests.
    """
    _tmp = {}
    for key, value in kwargs.iteritems():
        _tmp[key] = value
    _tmp["success"] = True
    return jsonify(_tmp), 200
