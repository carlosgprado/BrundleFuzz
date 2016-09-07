##################################################################
# Aesthetics.py
# It is not only pretty but legible too
##################################################################

try:
    import colorama
    from colorama import Fore, Back, Style
    COLORAMA = True

except ImportError:
    print "[!] COLORAMA not found"
    print "Defaulting to boring text..."
    COLORAMA = False


class Aesthetics(object):
    def __init__(self, parent):
        """
        NOTE: This could be implemented
        as decorators...
        """
        self.parent = parent

        if COLORAMA:
            colorama.init(autoreset = True)

    def m_info(self, m):
        m = '[*] ' + m
        if COLORAMA:
            print Style.DIM + m
        else:
            print m

    def m_warn(self, m):
        m = '[!] ' + m
        if COLORAMA:
            print Fore.YELLOW + m
        else:
            print m

    def m_ok(self, m):
        m = '[OK] ' + m
        if COLORAMA:
            print Fore.GREEN + m
        else:
            print m

    def m_alert(self, m):
        m = '[!!] ' + m
        if COLORAMA:
            print Fore.RED + m
        else:
            print m

    def m_fatal(self, m):
        m = '[X] ' + m
        if COLORAMA:
            print Fore.WHITE + Back.RED + m
        else:
            print m

    def stop(self):
        self.m_info("Restoring terminal...")
        colorama.deinit()
