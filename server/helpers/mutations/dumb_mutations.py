################################################################
# DUMB MUTATION STRATEGIES
# Imported by Cthulhu
################################################################

import itertools  # cycle :)
import random


class DumbMutationEngine(object):
    def __init__(self, parent, debug = False):
        """Mutation engine for dumb fuzzing

        Some of this code has been shamelessly copied
        from Sulley Framework
        """
        self.parent = parent
        self.cfg = parent.cfg
        self.debug = debug
        self.cy_strings = itertools.cycle(self._get_common_strings())
        self.buffer_mutations = [
            self._substitute_string,
            self._lift_bytes,
            self._mutate_token,
            self._delete_block,
            self._swap_blocks,
            self._duplicate_block]

        # This is used to assign some weights to the mutations
        # Weights mean probability of occurrence
        # TODO: Get this from config file
        # TODO: Maybe modify these dynamically?
        _mutation_weigths = (1, 5, 1, 1, 1, 1)
        self.intervals = self.normalize_mutation_weights(_mutation_weigths)

    def yield_mutation(self, file_contents = None):
        """This is the main function

        :param file_contents: original file contents
        :return: mutated file contents
        """
        if file_contents:
            # Mutations processing our file input are called randomly
            # However some occurr more often than others, depending
            # on the assigned weight
            r = random.randint(0, 99)
            f_idx = 0
            for i, v in enumerate(self.intervals):
                # HACK: this algorithm may be stupid :)
                if r > v:
                    f_idx = i + 1
                else:
                    break

            # Pre-processing of buffer (plugin)
            buf = self.parent._apply_pre_processing(file_contents)

            # "Regular" contents mutation
            # This is something analogous to an
            # array of function pointers in C/C++
            if buf:
                mutated_buffer = self.buffer_mutations[f_idx](buf)

            else:
                # empty buffer ->
                mutated_buffer = buf

            # Post-processing of mutated buffer (plugin)
            new_file_contents = \
                self.parent._apply_post_processing(mutated_buffer)

            return new_file_contents

        else:
            # Crappy fallback
            # to predefined byte arrays
            print("[dumb engine] Original file contents: NULL")
            return "A" * 1024

    def normalize_mutation_weights(self, w):
        """ It is better to call this
        than think. Think hurts.
        Returns a list of intervals to use
        with the random function.
        """
        total = sum(w)
        normalized_weights = [((x + 0.0/total)) * 100 for x in w]

        intervals = []
        accumulated = 0
        for x in normalized_weights:
            t = accumulated + x
            intervals.append(t)
            accumulated = t

        return intervals

    def _lift_bytes(self, buf, granularity = 5):
        """
        Increases byte values from a
        random segment by a random value
        @param granularity: a percentage, the maximum
        size of the block to be lifted (default: 5%)
        """
        if self.debug:
            print("[mutation] _lift_bytes")

        buffer_size = len(buf)
        block_max_size = int((buffer_size * (granularity + 0.0) / 100))
        offset = random.randrange(buffer_size)
        tlen = random.randint(1, buffer_size - offset) % block_max_size
        token = buf[offset: offset + tlen]

        delta = random.randint(1, 255)
        replacement = ''.join([chr((ord(x) + delta) % 255) for x in token])
        mod_buf = buf[: offset] + replacement + buf[offset + tlen:]

        return mod_buf

    def _mutate_token(self, buf, tlen = 1):
        """
        Mutates a token (subset from the buffer)
        and substitutes it with its mutation
        """
        if self.debug:
            print("[mutation] _mutate_token")

        # Get the random token
        offset = random.randrange(len(buf))
        # tlen = random.randint(1, len(buf) - offset)
        token = buf[offset: offset + tlen]
        mutated_token = self._get_token_mutation(token, tlen)

        mod_buf = buf[: offset] + mutated_token
        # Only in case the replacement fits into
        # the original buffer
        if offset + tlen < len(buf):
            mod_buf += buf[offset + tlen:]

        return mod_buf

    def _delete_block(self, buf):
        """
        Exactly what it says :)
        Randomly selects a block and deletes it
        """
        if self.debug:
            print("[mutation] _delete_block")

        offset = random.randrange(len(buf))
        dlen = random.randrange(1, len(buf) - offset + 1)

        mod_buf = buf[: offset] + buf[offset + dlen:]

        return mod_buf

    def _duplicate_block(self, buf):
        """
        Exactly what it says :)
        Randomly selects a block and duplicates it
        """
        if self.debug:
            print("[mutation] _duplicate_block")

        offset = random.randrange(len(buf))
        dlen = random.randrange(1, len(buf) - offset + 1)

        mod_buf = buf[:offset + dlen] + buf[offset:offset + dlen]
        + buf[offset + dlen:]

        return mod_buf

    def _swap_blocks(self, buf):
        """
        Just swapping stuff
        """
        if self.debug:
            print("[mutation] _swap_blocks")

        L = len(buf)

        if L < 2:
            # Impossible to swap
            return buf

        off1 = random.randrange(L / 2)
        len1 = random.randint(1, (L / 2) - off1)

        off2 = random.randrange(L / 2, L)
        len2 = random.randint(1, L - off2)

        A = buf[: off1]
        B = buf[off1: off1 + len1]
        C = buf[off1 + len1: off2]
        D = buf[off2: off2 + len2]
        E = buf[off2 + len2:]

        return A + D + C + B + E

    def _get_token_mutation(self, t, tlen = 1):
        """
        This is particularly effective for delimiters
        but it would be useful for other tokens
        :return: random element of list of tokens
        """
        if self.debug:
            print("[mutation] _get_token_mutation")

        token_mutations = []

        # Repetition
        token_mutations.append(t * tlen)

        # if the delimiter is a space, try throwing out some tabs.
        if t == " ":
            token_mutations.append("\t" * tlen)

        # toss in some other common delimiters:
        token_mutations.append(" " * tlen)
        token_mutations.append("!" * tlen)
        token_mutations.append("@" * tlen)
        token_mutations.append("#" * tlen)
        token_mutations.append("$" * tlen)
        token_mutations.append("%" * tlen)
        token_mutations.append("^" * tlen)
        token_mutations.append("&" * tlen)
        token_mutations.append("*" * tlen)
        token_mutations.append("(" * tlen)
        token_mutations.append(")" * tlen)
        token_mutations.append("-" * tlen)
        token_mutations.append("_" * tlen)
        token_mutations.append("+" * tlen)
        token_mutations.append("=" * tlen)
        token_mutations.append(":" * tlen)
        token_mutations.append(";" * tlen)
        token_mutations.append("'" * tlen)
        token_mutations.append("\"" * tlen)
        token_mutations.append("/" * tlen)
        token_mutations.append("\\" * tlen)
        token_mutations.append("?" * tlen)
        token_mutations.append("<" * tlen)
        token_mutations.append(">" * tlen)
        token_mutations.append("." * tlen)
        token_mutations.append("," * tlen)
        token_mutations.append("\r" * tlen)
        token_mutations.append("\n" * tlen)

        return token_mutations[random.randrange(len(token_mutations))]

    def _get_common_strings(self, long_strings = False):
        """
        Produce generic (independent from input) strings.
        These are known to exercise some corner cases.
        """
        if self.debug:
            print("[mutation] _get_common_strings")

        common_strings = [
            # omission.
            "",

            # strings ripped from spike (and some others I added)
            "/.:/" + "A" * 5000 + "\x00\x00",
            "/.../" + "A" * 5000 + "\x00\x00",
            "/.../.../.../.../.../.../.../.../.../.../",
            "/../../../../../../../../../../../../etc/passwd",
            "/../../../../../../../../../../../../boot.ini",
            "..:..:..:..:..:..:..:..:..:..:..:..:..:",
            "\\\\*",
            "\\\\?\\",
            "/\\" * 5000,
            "/." * 5000,
            "!@#$%%^#$%#$@#$%$$@#$%^^**(()",
            "%01%02%03%04%0a%0d%0aASDF",
            "%01%02%03@%04%0a%0d%0aASDF",
            "/%00/",
            "%00/",
            "%00",
            "%u0000",
            "%\xfe\xf0%\x00\xff",
            "%\xfe\xf0%\x01\xff" * 20,

            # format strings.
            "%n" * 100,
            "%n" * 500,
            "\"%n\"" * 500,
            "%s" * 100,
            "%s" * 500,
            "\"%s\"" * 500,

            # some binary strings.
            "\xde\xad\xbe\xef",
            "\xde\xad\xbe\xef" * 10,
            "\xde\xad\xbe\xef" * 100,
            "\xde\xad\xbe\xef" * 1000,
            "\xde\xad\xbe\xef" * 10000,
            "\x00" * 1000,

            # miscellaneous.
            "\r\n" * 100,
            # sendmail crackaddr (http://lsd-pl.net/other/sendmail.txt)
            "<>" * 500
        ]

        if long_strings:
            # add some long strings.
            common_strings += self._gen_long_strings("A")
            common_strings += self._gen_long_strings("B")
            common_strings += self._gen_long_strings("1")
            common_strings += self._gen_long_strings("2")
            common_strings += self._gen_long_strings("3")
            common_strings += self._gen_long_strings("<")
            common_strings += self._gen_long_strings(">")
            common_strings += self._gen_long_strings("'")
            common_strings += self._gen_long_strings("\"")
            common_strings += self._gen_long_strings("/")
            common_strings += self._gen_long_strings("\\")
            common_strings += self._gen_long_strings("?")
            common_strings += self._gen_long_strings("=")
            common_strings += self._gen_long_strings("a=")
            common_strings += self._gen_long_strings("&")
            common_strings += self._gen_long_strings(".")
            common_strings += self._gen_long_strings(",")
            common_strings += self._gen_long_strings("(")
            common_strings += self._gen_long_strings(")")
            common_strings += self._gen_long_strings("]")
            common_strings += self._gen_long_strings("[")
            common_strings += self._gen_long_strings("%")
            common_strings += self._gen_long_strings("*")
            common_strings += self._gen_long_strings("-")
            common_strings += self._gen_long_strings("+")
            common_strings += self._gen_long_strings("{")
            common_strings += self._gen_long_strings("}")
            common_strings += self._gen_long_strings("\x14")
            # expands to 4 characters under utf16
            common_strings += self._gen_long_strings("\xFE")
            # expands to 4 characters under utf16
            common_strings += self._gen_long_strings("\xFF")

        return common_strings

    def _substitute_string(self, buf):
        """
        Simple substitution with *standard tokens*
        This is equivalent to smash the original bytes
        """
        if self.debug:
            print("[mutation] _substitute_string")

        replacement = self.cy_strings.next()
        rlen = len(replacement)
        offset = random.randrange(len(buf))

        mod_buf = buf[: offset] + replacement
        # Only in case the replacement fits into
        # the original buffer
        if offset + rlen < len(buf):
            mod_buf += buf[offset + rlen:]

        return mod_buf

    def _gen_long_strings(self, sequence, max_len = 0):
        """
        Given a sequence, generate a number of selectively chosen
        strings lengths of the given sequence.
        NOTE: argument max_len sets a... you got it, maximum length
        """
        if self.debug:
            print("[mutation] get_long_strings")

        long_strings = []
        for length in [128, 255, 256, 257, 511, 512, 513, 1023, 1024,
         2048, 2049, 4095, 4096, 4097, 5000, 10000, 20000, 32762, 32763,
         32764, 32765, 32766, 32767, 32768, 32769, 0xFFFF - 2, 0xFFFF - 1,
         0xFFFF, 0xFFFF + 1, 0xFFFF + 2, 99999, 100000, 500000, 1000000]:

            if max_len and length > max_len:
                break

            long_string = sequence * length
            long_strings.append(long_string)

        return long_strings
