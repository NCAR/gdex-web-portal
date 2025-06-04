import json
import pdb

def get_builder():
    """Factory for creating a builder object.
    """
    return NBBuilder()


class NBBuilder(object):
    """Class to help construct a Jupyter Notebook
    """

    def __init__(self):
        self.root = {}
        self.root['cells'] = []
        self.root['metadata'] = self.get_init_metadata()
        self.root['nbformat'] = 4
        self.root['nbformat_minor'] = 2

    def get_init_metadata(self):
        metadata = {}
        metadata['kernelspec'] = {
                'display_name' : 'Python 3',
                'language' : 'python',
                'name' : 'python3'
                }
        metadata['language_info'] = {
                'codemirror' : {'name' : 'ipython','version': 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": self.get_python_version()
                }
        return metadata

    def get_python_version(self):
        """Get the python version.
        TODO: get real version.
        """
        return "3.6.5"

    def add_newlines(self, str_list):
        for n,s in enumerate(str_list):
            str_list[n] = s+"\n"
        str_list[-1] = str_list[-1][:-1]

    def add_markdown_block(self, *argv):
        self.add_block('markdown', argv, {})

    def add_code_block(self, *argv):
        argv = list(argv)
        self.add_newlines(argv)
        self.add_block('code', argv, {}, outputs=[], execution_count=None)

    def add_block(self, cell_type, source, metadata, **extras):
        cell_dict = {}
        cell_dict['cell_type'] = cell_type
        cell_dict['metadata'] = metadata
        cell_dict['source'] = source
        for k,v in extras.items():
            cell_dict[k] = v
        self.root['cells'].append(cell_dict)

    def write_to_file(self,filename):
        with open(filename, 'w',) as fh:
            fh.write(json.dumps(self.root))


    def __str__(self):
        return json.dumps(self.root)

    __repr__ = __str__


class CodeBlock(object):

    def __init__(self):
        print("\n")

