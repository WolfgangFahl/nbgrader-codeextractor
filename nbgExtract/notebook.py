import argparse
import copy
import dataclasses
import json
import os
import sys
import traceback
import typing
from dataclasses import dataclass


@dataclass
class Cell:
    """
    cell of a jupyter notebook
    """
    cell_type: str
    id: str
    metadata: dict = None
    source: typing.List[str] = None
    execution_count: int = None
    outputs: typing.List[str] = None


class GraderNotebook:
    """
    a jupyter Notebook to be graded
    """

    def __init__(self, notebook: typing.Union[dict, str], debug: bool = False):
        """
        constructor

        Args:
            notebook(object): json notebook file path or content
            debug(bool): if True show debug information
        """
        self.notebook = notebook
        self.debug = debug
        self.loaded = False
        self.load()

    @classmethod
    def nbgrader_metadata(cls, cell: Cell):
        """
        get the nbgrade metadata of a given cell
        """
        if cell.cell_type == "code":
            metadata = cell.metadata
            if "nbgrader" in metadata:
                return metadata["nbgrader"]
        return None

    def load(self):
        """
        load my notebook metadata from the ipynb json files
        """
        if self.loaded:
            return
        try:
            self.jFile = "?"
            self.solutions = {}
            self.code_cells = {}
            if isinstance(self.notebook, str):
                self.jFile = self.notebook
                with open(self.notebook) as nbf:
                    self.nbdata = json.load(nbf)
            else:
                self.nbdata = self.notebook
            self.cells = [Cell(**record) for record in self.nbdata["cells"]]
            for cell in self.cells:
                nbgrader = self.nbgrader_metadata(cell)
                if nbgrader is not None:
                    gradeid = nbgrader["grade_id"]
                    self.code_cells[gradeid] = cell
                    if nbgrader["solution"]:
                        self.solutions[gradeid] = cell  # raise Exception(f"grade_id missing for {cell}")
            self.loaded = True
        except Exception as ex:
            trace = traceback.format_exc() if self.debug else ""
            print(f"{self.jFile}:{str(ex)}{trace}")

    def as_python_code(self, code_preamble: str = "", add_try_catch: bool = False) -> str:
        """
        convert my source to pythonCode

        Args:
            code_preamble(str): the preamble for the code
            add_try_catch(bool): add  try/catch block

        Returns:
            str: the python code
        """
        code = "import traceback\n"
        code += code_preamble + "\n"
        indent = ""
        if add_try_catch:
            code += f"""try:\n"""
            indent = "  "
        for cell_id, code_cell in self.code_cells.items():
            code += f"\n# id: {cell_id}\n"
            nbgrader = self.nbgrader_metadata(code_cell)
            if nbgrader is not None:
                for key, value in nbgrader.items():
                    code += f"{indent}#{key}={value}\n"
            if code_cell.source is not None:
                for line in code_cell.source:
                    if line.startswith("!"):
                        pass
                    else:
                        code += indent + line
        if add_try_catch:
            code += "\nexcept Exception as ex:\n"
            code += "  print(traceback.format_exc())\n"
        return code


class Submission(GraderNotebook):
    """
    a submission of a jupyter notebook for grading
    """

    def __init__(self, notebook: typing.Union[dict, str], debug: bool = False):
        """
        constructor

        Args:
            notebook(object): json notebook file path or content
            debug(bool): if True show debug information
        """
        GraderNotebook.__init__(self, notebook, debug)

    def merge_failure(self, cell_id: str):
        """
        handles a merge failure
        Args:
            cell_id: id of the cell that could not be merged
        """
        if self.debug:
            print(f"couldn't merge solution code cell {cell_id}")

    def merge_code(self, source_notebook: GraderNotebook) -> "Submission":
        """
        merge my code with the code of the given submission Notebook
        Args:
            source_notebook: source notebook of the exercise that holds the tests for the submission

        Returns:
            Submission - Submission merged with its source
        """
        merge_result = copy.deepcopy(self)
        merge_result.code_cells = {}
        for cell_id, code_cell in source_notebook.code_cells.items():
            nbgrader = self.nbgrader_metadata(code_cell)
            if nbgrader is not None:
                merge_cell = dataclasses.replace(code_cell)
                jFile = source_notebook.jFile
                if nbgrader["solution"]:
                    if cell_id in self.code_cells:
                        merge_cell = dataclasses.replace(self.code_cells[cell_id])
                    else:
                        self.merge_failure(cell_id)
                        merge_cell = Cell(
                                cell_type="code",
                                id=cell_id,
                                metadata={"nbgrader": {}}
                        )
                    jFile = self.jFile
                merge_result.code_cells[cell_id] = merge_cell
                merge_nbgrader = self.nbgrader_metadata(merge_cell)
                merge_nbgrader["notebook"] = jFile
        return merge_result


def main(argv=None):
    '''
    main routine
    '''
    if argv is None:
        argv = sys.argv
    program_name = os.path.basename(sys.argv[0])
    debug = False
    try:
        parser = argparse.ArgumentParser(description='nbg-code - extract code cells from the submission and merge the cells with the test cells from the source')
        parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="show debug info")
        parser.add_argument("--submission", help="location of the submission notebook")
        parser.add_argument("--source", help="location of the source notebook for the submission")
        parser.add_argument("--outputPython", default="/tmp/submission.py", help="target file to store the result")

        args = parser.parse_args(argv[1:])
        debug = args.debug
        source = GraderNotebook(args.source)
        submission = Submission(args.submission)
        merged_submission = submission.merge_code(source)
        with open(args.outputPython, mode="w") as fp:
            fp.write(merged_submission.as_python_code())

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 1
    except Exception as e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        if debug:
            print(traceback.format_exc())
        return 2

if __name__ == '__main__':
    sys.exit(main())