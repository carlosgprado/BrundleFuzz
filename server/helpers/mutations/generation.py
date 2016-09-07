################################################################
# INTELLIGENT MUTATION STRATEGIES
# Imported by Cthulhu
################################################################

try:
    import pfp

except ImportError:
    print("*" * 60)
    raise ImportError("[!] Could not import PFP module")

import io
import os
import random

templates_dir = '010templates'


class IntelligentMutationEngine(object):
    def __init__(self, parent, debug = False):
        self.parent = parent
        self.cfg = parent.cfg
        self.debug = debug
        self.idx = 0
        self.r = 0
        self.dom = None
        self.nr_array_types = 0
        self.nr_core_types = 0
        self.template_file = self._get_template_filename()

    def _get_template_filename(self):
        """Get template filename

        Depending on the configuration
        format parameter
        """
        _format = self.cfg.get('mutations', 'format')
        if _format == 'pdf':
            tf = 'PDFTemplate.bt'
        elif _format == 'png':
            tf = 'PNG12Template.bt'

        module_dir = os.path.dirname(os.path.abspath(__file__))

        return os.path.join(module_dir, templates_dir, tf)

    def _generate_dom(self, file_contents):
        """Generates the file's DOM

        Applies a template to a file in order to generate
        a DOM to use as an intelligent mutation seed.
        :param template: the 010 editor template
        :param file: the original file
        """
        bytestream = io.BytesIO(file_contents)
        try:
            dom = pfp.parse(
                data = bytestream,
                template_file = self.template_file)

            return dom
        except Exception as e:
            print(e)
            return None

    def _analyze(self, node, visited = set([])):
        """This is basically dfs all over again.

        I chose clarity over code reuse.
        :return: Nothing, calculates some statistics
        regarding node types
        """
        for ch in self._get_children(node):
            if ch not in visited:
                visited.add(ch)
                # In this first sweep I want to gather data
                # like the number of core types
                # How many values are present?
                if type(ch) == pfp.fields.Dom or \
                    self._base_name(ch) == 'Struct':
                    pass
                elif self._base_name(ch) == 'Array':
                    self.nr_array_types += 1
                else:
                    self.nr_core_types += 1

                self._analyze(ch, visited)

    def yield_mutation(self, file_contents = None):
        """Thin wrapper

        This is exposed to Cthulhu.
        :return: mutated file contents
        """
        self.dom = self._generate_dom(file_contents)
        if not self.dom:
            print('Error parsing DOM. Crappy fallback.')
            return 'A' * 1024

        # Populate node type statistics
        self.nr_core_types = 0
        self.nr_array_types = 0
        self._analyze(self.dom)
        self.r = random.randint(0, self.nr_core_types + self.nr_array_types)

        # Now we are ready to mutate the file
        self.idx = 0
        self._mutate_file(self.dom)

        return self.dom._pfp__build()

    def _mutate_file(self, node, visited = set([])):
        """Implementation of Depth-First Search

        Call this with the DOM's root
        Returns nothing, only mutates the
        file's DOM structure.
        """
        for ch in self._get_children(node):

            if ch not in visited:
                visited.add(ch)

                try:
                    self._mutate_node(ch)
                except Exception as e:
                    print(e)

                # Recursion is a bitch
                self._mutate_file(ch, visited)

    def _mutate_node(self, node):
        """Perform node mutations (if any)

        :returns: Nothing, updates node in place
        """
        self.idx += 1

        if self.idx != self.r:
            return

        # Exclude some things like signatures, etc.
        exclusions = ['signature', 'crc']
        for ex in exclusions:
            if ex in node._pfp__name.lower():
                return

        if type(node) == pfp.fields.Dom:
            return
        elif self._base_name(node) == 'Struct':
            # This is a container, interested in
            # its children nodes
            return
        elif self._base_name(node) == 'Array':
            print("%s is an Array of %s (%s)" % (node._pfp__name,
                node.field_cls, node.width))
            # I can change the data at once:
            node.raw_data = "cacaca"

            # Or iterate through its elements:
            # for e in node:
            #    e._pfp__set_value(e._pfp__value + 1)
        else:
            # CORE TYPE
            # This is supposed to cast
            print('CORE TYPE?')
            node._pfp__set_value(1337)

    def _get_children(self, x):
        """This is a workaround.

        Some PFP types do not have this attribute...
        """
        try:
            return x._pfp__children

        except AttributeError:
            return []

    def _base_name(self, cls):
        """PFP types are fucked up.

        Somehow generated on the fly.
        More reliable to check the base.
        """
        bn = ''

        for base in cls.__class__.__bases__:
            bn = base.__name__

        return bn
