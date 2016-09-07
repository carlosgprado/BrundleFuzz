#
# Generate test cases, either via
# mutation or generation
#

import os

from helpers.common import MutationObject
from helpers.mutations.dumb_mutations import DumbMutationEngine
from helpers.mutations.generation import IntelligentMutationEngine


################################################################
# CTHULHU
################################################################
class Cthulhu(object):
    """Main mutation object

    This object encompases all mutations
    It is literally THE BRINGER OF DEATH
    """
    def __init__(self, parent, debug = False, mode = 'dumb'):
        self.mode = mode
        self.debug = debug
        self.parent = parent
        self.engine = None
        self.ae = parent.ae
        self.cfg = parent.cfg
        self.root_dir = parent.root_dir
        self.fq = parent.fuzzing_queues
        self.plugins = parent.plugins
        self.utils = parent.utils
        self.fileops = parent.fileops
        self.mo = None
        self.plugin_list = []
        self.data_to_post = None

        self.samples_dir = os.path.join(self.root_dir, 'samples')
        self.mutations_dir = os.path.join(self.root_dir, 'mutations')

        self.ae.m_warn("Initializing Cthulhu...")
        self.ae.m_warn("THE BRINGER OF DEATH...")
        self.ae.m_warn("Mode: %s" % self.mode)

        self._initialize_plugins()
        self._populate_mutation_dir()
        self._initialize_mutation_queue()

        self.ae.m_info("Initializing mutation strategies...")

        # Select the appropriate mutation engine
        if self.mode == 'dumb':
            self.engine = DumbMutationEngine(
                self, debug = self.debug)
        elif self.mode == 'generation':
            self.engine = IntelligentMutationEngine(
                self, debug = self.debug)

    def _populate_mutation_dir(self):
        """MUTATION ONLY

        Copies all samples to the mutations directory.
        """
        self.fileops.copy_all_files(self.samples_dir, self.mutations_dir)

    def _initialize_mutation_queue(self):
        """MUTATION MODE ONLY"""

        # Initialize the Queue with the mutated files
        self.ae.m_info("Adding all files in mutations directory to \
            queue with priority: 10")

        for s in self.fileops.get_all_filenames(self.mutations_dir):
            self.fq.mutationQueue.put(MutationObject(10, s,
                self.parent.g_id, 0, None, None))
            self.parent.g_id += 1

        self.ae.m_info("Queue initialized with %d files" % self.parent.g_id)

    def _get_input_filename(self):
        """Gets a filename from the Mutation Queue

        Moves the Queue elements around
        (from mutation to processed one)
        """
        e = self.fq.mutationQueue.get()
        self.mo.p_id = e.id
        self.mo.id = self.parent.g_id
        self.fq.mutationQueue.put(e)

        if self.debug:
            print("Filename:", e.filename)
            print("id: %d, parent id: %d" % (self.parent.g_id, self.mo.p_id))

        return e.filename

    def _prep_mutation_file(self):
        """Prepares a mutation file

        Gets a file from the mutation queue, generates a new filename
        for it and reads its contents.
        Pass these contents to the mutation engine to... mutate them
        """
        input_filename = self._get_input_filename()

        # Get the file extension
        extension = input_filename.split('.')[-1]

        # Get random name for the new mutation
        new_name = self.utils.random_alphabetical_string(
            maxlen = 16, exact = True)
        self.mo.filename = "%s.%s" % (new_name, extension)

        input_file_path = os.path.join(self.mutations_dir, input_filename)

        with open(input_file_path, 'rb') as f:
            original_contents = f.read()

        return original_contents

    def _initialize_plugins(self):
        """Initialize plugins

        Load the selected plugins and makes
        them available to Cthulhu
        :return: None
        """
        self.ae.m_warn("Initializing plugins...")

        for p in self.plugins.get_plugins():
            self.ae.m_info("Loading plugin %s..." % p['name'])
            self.plugin_list.append(p)

    def _apply_pre_processing(self, file_contents):
        """Plugin Pre-processing

        Applies the selected plugins in order to
        extract the raw data to be mutated
        :param file_contents: eeeh... the input file contents :)
        :return: extracted data
        """
        data = file_contents

        for p in self.plugin_list:
            plugin = self.plugins.load_plugin(p)
            data, self.data_to_post = plugin.pre(data)

        return data

    def _apply_post_processing(self, mutated_buffer):
        """Plugin Post-processing

        Applies the selected plugins in *reverse* order
        to recreate the original file format
        :param mutated_buffer: eeeh... the mutated buffer :)
        :return: new file contents
        """
        data = mutated_buffer

        for p in self.plugin_list[::-1]:
            # The plugins are applied in reverse order
            plugin = self.plugins.load_plugin(p)
            data = plugin.post(data, self.data_to_post)

        return data

    def generate_test_case(self):
        """It creates the test case CONTENTS

        This function is exposed.
        ADAPTER PATTERN.
        :returns: Mutation Object
        """

        # Initialize with defaults
        self.mo = MutationObject()

        original_contents = self._prep_mutation_file()
        self.mo.data = self.engine.yield_mutation(original_contents)
        self.parent.g_id += 1

        return self.mo

    def test_case_to_file(self, test_case_data, filename):
        """Write the mutated contents TO FILE

        This function is exposed.
        :return: mutation filename or None
        """
        mutation_filename = os.path.join(self.mutations_dir, filename)

        try:
            with open(mutation_filename, 'wb') as fh:
                fh.write(test_case_data)

            return mutation_filename

        except Exception:
            return None

    def delete_current_test_case(self):
        """The mutation is not interesting

        Kill it with fire
        """
        mutation_filename = os.path.join(self.mutations_dir, self.mo.filename)
        os.remove(mutation_filename)
