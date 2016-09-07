##################################################################
# sample_analysis.py
# Server side analysis of samples for more efficient fuzzing
##################################################################

import glob

class SampleAnalysis(object):
    def __init__():
        self.string_tokens = []

    def _strings_from_binary(self, buf, min_string_length = 4):
        """ Gets ASCII strings from sample binary
        These will be fed to Cthulhu and be used
        as tokens for further mutations.
        Contributed by Phillip Lang """
        tmp_str = ""
        for offset, byte in enumerate(buf):
            alphabet = string.digits + string.letters + '{}/\()[]!#"$%&'
            if byte in alphabet:
                tmp_str += byte
                continue
            if len(tmp_str) >= min_string_length:
                yield (tmp_str, offset - len(tmp_str))
            tmp_str = ""

    def populate_string_tokens(self, samples_path = ''):
        """ Produces a list of string tokens by
        analyzing the file samples
        """
        if not samples_path:
            raise 'Specify samples path!'

        for filename in glob.glob(os.path.join(samples_path, '*.*')):
            with open(filename, 'rb') as f:
                buf = f.read()

            for s in self._strings_from_binary(buf):
                if s not in self.string_tokens:
                    self.string_tokens.append(s)

        return len(self.string_tokens)

