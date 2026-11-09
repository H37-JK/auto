"""Support standard Xauthority FamilyWild entries missing in python-xlib."""
from contextlib import contextmanager


def find_wildcard_auth(entries, dispno, types=(b'MIT-MAGIC-COOKIE-1',)):
    number = str(dispno).encode()
    for scheme in types:
        for family, address, display, name, data in entries:
            if family == 65535 and display in (b'', number) and name == scheme:
                return name, data
    return None


@contextmanager
def wildcard_xauthority():
    from Xlib import xauth, error
    original = xauth.Xauthority.get_best_auth
    def compatible(self, family, address, dispno, types=(b'MIT-MAGIC-COOKIE-1',)):
        try:
            return original(self, family, address, dispno, types)
        except error.XNoAuthError:
            found = find_wildcard_auth(self.entries, dispno, types)
            if found is None:
                raise
            return found
    xauth.Xauthority.get_best_auth = compatible
    try:
        yield
    finally:
        xauth.Xauthority.get_best_auth = original
