from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nbgExtract.notebook import GraderNotebook
import ast
import logging
from pathlib import Path
from typing import List, Tuple
from textwrap import indent
from nbgExtract.cells import Cell, NbgraderCellMetadata, NbgraderCellType


logger = logging.getLogger(__name__)


class NbgCodeGenerator:
    """
    Generate python code from nbgrader notebook with cell context control
    """

    def __init__(self):
        pass

    def generate_file(self, notebook: GraderNotebook, target: Path):
        """
        Extract code and generate python  file at given target
        Args:
            notebook: notebook to extract code from
            target: target dir location to store the file
        """
        code = self.generate(notebook)
        file_name = notebook.name
        file_name = "".join(x if x.isalnum() else "_" for x in file_name)
        file_path = target.joinpath(f"test_{file_name}.py")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, mode="w") as fp:
            fp.write(code)

    def generate(self, notebook: GraderNotebook) -> str:
        code = ""
        code += self._imports()
        code += self._header()
        code += f'''
class TestNbgraderNotebook(unittest.TestCase):
    """
    Test {notebook.name}
    """

    def setUp(self) -> None:
        self.show_output = True
        self.suppress_exception = False

    def test_cells(self):
        notebook_context = NotebookContext(
                name="{notebook.name}",
                show_output=self.show_output, 
                suppress_exception=self.suppress_exception
        )
'''
        notebook_imports = []
        for cell in notebook.cells:
            if cell.cell_type == "markdown":
                continue
            nbg_metadata = cell.get_nbg_metadata()
            if nbg_metadata:
                nbg_cell_type = nbg_metadata.get_type()
            else:
                nbg_cell_type = None
            cell_source = self.get_cell_sourcecode(cell)
            sourcecode, cell_imports = self.separate_imports(cell_source)
            notebook_imports.extend(cell_imports)
            if nbg_cell_type is NbgraderCellType.AUTOGRADED_TESTS:
                sourcecode = self.add_score_printout(sourcecode, nbg_metadata)
            sourcecode += "\npass"  # to avoid issues with empty cells
            # ToDo: simplify this part
            if nbg_cell_type in [NbgraderCellType.AUTOGRADED_ANSWER, NbgraderCellType.AUTOGRADED_TESTS, NbgraderCellType.READ_ONLY]:
                cell_record = cell.__dict__
                for key in ["source", "outputs"]:
                    if key in cell_record:
                        cell_record.pop(key)
                if "nbgrader" in cell_record.get("metadata"):
                    if "notebook" in cell_record.get("metadata").get("nbgrader"):
                        cell_record.get("metadata").get("nbgrader").pop("notebook")
            else:
                cell_record = None
            cell_context = f"with notebook_context(cell_metadata={cell_record}):\n"
            cell_context += indent(sourcecode, " "*4)
            code += indent(cell_context, " "*8)
            code += "\n"
        nbg_res_handling = """
print(notebook_context.tests)
notebook_context.store_notebook_result(Path("results.json"))
"""
        code += indent(nbg_res_handling, " "*8)
        additional_imports = "\n".join(notebook_imports)
        code = f"{additional_imports}\n{code}\n"
        code += self.cmdline_tool()
        return code

    def _imports(self):
        return """
import sys
import argparse
import unittest
from pathlib import Path
from nbgExtract.gen.context import NotebookContext
"""

    def _header(self) -> str:
        """
        Imports and helper classes
        """
        header = """
class HTML:
    def __init__(self, markup: str):
        self.markup = markup

    def __str__(self):
        return self.markup

def display(text: str):
    print(text)
"""
        return header

    def get_cell_sourcecode(self, cell: Cell) -> str:
        """
        Get cell sourcecode
        Remove lines that use the magic commands
        Args:
            cell:

        Returns:

        """
        code = ""
        if cell.source:
            for line in cell.source:
                if line.startswith("%"):
                    line = f"#{line}"
                if line.strip().startswith("!"):
                    line = f"#{line}"
                code += line
        return code

    def separate_imports(self, sourcecode: str) -> Tuple[str, List[str]]:
        """
        remove all import statements and return them as separate list
        Args:
            sourcecode:

        Returns:

        """
        try:
            root = ast.parse(sourcecode)
        except:
            return sourcecode, []
        cell_import_nodes = []
        for node in ast.walk(root):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                cell_import_nodes.append(node)
            else:
                continue
        cell_imports = [ast.unparse(i) for i in cell_import_nodes]
        for cell_import in cell_imports:
            sourcecode = sourcecode.replace(cell_import, f"#{cell_import}")
        return sourcecode, cell_imports

    def add_score_printout(self, sourcecode: str, metadata: NbgraderCellMetadata) -> str:
        try:
            parsed_cell_code = ast.parse(sourcecode)
        except:
            logger.error("Not able to find expression that prints out reached points in autograded test")
            return sourcecode
        if parsed_cell_code and len(parsed_cell_code.body) > 0:
            score_exp = parsed_cell_code.body[-1]
            if isinstance(score_exp, ast.Assert):
                sourcecode += f"\nprint({metadata.points})"
            else:
                sourcecode += f"\nprint({ast.unparse(score_exp)})"
        else:
            pass
        return sourcecode

    def cmdline_tool(self):
        code = """
def main(argv=None):
    import argparse
    if argv is None:
        argv = sys.argv
    parser = argparse.ArgumentParser(prog='nbgrader extracted code cells')
    parser.add_argument('--hide_cell_output', action="store_true")
    parser.add_argument('--suppress_exception', action='store_true')
    args = parser.parse_args()
    notebook = TestNbgraderNotebook()
    notebook.show_output = not args.hide_cell_output
    notebook.suppress_exception = args.suppress_exception
    notebook.test_cells()


if __name__ == '__main__':
    sys.exit(main())
        """
        return code
