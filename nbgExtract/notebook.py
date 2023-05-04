import copy
import dataclasses
import io
import json
import re
import traceback
import typing
import zipfile
from dataclasses import dataclass
from pathlib import Path
from . import logger


@dataclass
class Cell:
    """
    cell of a jupyter notebook
    """
    cell_type: str
    id: str = None
    metadata: dict = None
    source: typing.List[str] = None
    execution_count: int = None
    outputs: typing.List[str] = None
    attachments: dict = None


class GraderNotebook:
    """
    a jupyter Notebook to be graded
    """

    def __init__(
            self,
            notebook_content_or_filepath: typing.Union[dict, str],
            name: str = None,
            debug: bool=False
    ):
        """
        constructor

        Args:
            notebook_content_or_filepath(object): json notebook file path or content
            name(str): name of the notebook
        """
        self.debug=debug
        self.name = name
        self.notebook = None
        self.notebook_filepath = "?"
        self.loaded = False
        # init action ..
        self.load(notebook_content_or_filepath)
        
    def handleException(self,ex):
        """
        handle the given exception
        """
        trace = traceback.format_exc() if self.debug else ""
        logger.error(f"{self.notebook_filepath}:{str(ex)}{trace}")

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

    def load(self, notebook: typing.Union[dict, str]):
        """
        load my notebook metadata from the ipynb json files
        """
        if self.loaded:
            return
        try:
            self.solutions = {}
            self.code_cells = {}
            if isinstance(notebook, str):
                self.notebook_filepath = notebook
                with open(notebook) as nbf:
                    self.notebook = json.load(nbf)
            elif isinstance(notebook, io.BytesIO):
                self.notebook_filepath = notebook.name
                self.notebook = json.load(notebook)
            self.cells = []
            for record in self.notebook["cells"]:
                try: 
                    cell=Cell(**record) 
                    self.cells.append(cell)
                except Exception as ex:
                    raise ex
                    pass
            for cell in self.cells:
                nbgrader = self.nbgrader_metadata(cell)
                if nbgrader is not None:
                    gradeid = nbgrader["grade_id"]
                    self.code_cells[gradeid] = cell
                    if nbgrader["solution"]:
                        self.solutions[gradeid] = cell  # raise Exception(f"grade_id missing for {cell}")
            self.loaded = True
        except Exception as ex:
            self.handleException(ex)

    def as_python_code(self, template_filepath: str = None,with_cell_comments:bool=False) -> str:
        """
        convert my source to pythonCode
s
        Args:
            template_filepath: template file to use of None default template is used

        Returns:
            str: the python code
        """
        if template_filepath is None:
            template_filepath = f"{Path(__file__).parent.absolute()}/resources/unittest_template.tpy"
        code = ""
        for cell_id, code_cell in self.code_cells.items():
            code += f"\n# id: {cell_id}\n"
            nbgrader = self.nbgrader_metadata(code_cell)
            if  with_cell_comments:                
                if nbgrader is not None:
                    for key, value in nbgrader.items():
                        code += f"#{key}={value}\n"
            if code_cell.source is not None:
                for line in code_cell.source:
                    if line.startswith("!"):
                        pass
                    else:
                        code += line
        path = Path(template_filepath)
        if not path.exists() or not path.is_file():
            logger.info(f"template file for python generation '{template_filepath}' is not a file or does not exist")
        else:
            with open(path, mode="r") as f:
                template = f.read()
        template_var_regex = "{{ *code *}}"
        indent, line_to_replace = self._get_indented_by(template_var_regex, template)
        if indent is not None:
            code = self._indent_string(code, indent)
            code = template.replace(line_to_replace, code)
        return code

    @classmethod
    def _indent_string(cls, string: str, indent: int) -> str:
        """
        indent given string
        Args:
            string: string to indent
            indent: number of spaces

        Returns:
            indented string
        """
        lines = string.split("\n")
        res = ""
        for line in lines:
            res += " " * indent
            res += line
            res += "\n"
        return res

    @classmethod
    def _get_indented_by(cls, key: str, template: str) -> typing.Union[typing.Tuple[int, str], typing.Tuple[None, None]]:
        """
        Find the line were the key occurs and return the indentation of the key
        Args:
            key: regex compatible key for which the indentation should be checked

        Returns:
            int, str: level of indentation, line to replace
            None: if key was not found
        """
        pattern = f'(?P<key> +' + key + ')'
        matches = re.finditer(pattern, template)
        for match in matches:
            line = match.group("key")
            if line is not None:
                indent = len(line) - len(line.lstrip())
                return indent, line
        return None, None


class Submission(GraderNotebook):
    """
    a submission of a jupyter notebook for grading
    """

    def __init__(self, notebook: typing.Union[dict, str, io.BytesIO],debug:bool=False):
        """
        constructor

        Args:
            notebook(object): json notebook file path or content
        """
        GraderNotebook.__init__(self, notebook,debug=debug)

    def merge_failure(self, cell_id: str):
        """
        handles a merge failure
        Args:
            cell_id: id of the cell that could not be merged
        """
        logger.debug(f"couldn't merge solution code cell {cell_id}")

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
                notebook = source_notebook.notebook
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
                    notebook = self.notebook
                merge_result.code_cells[cell_id] = merge_cell
                merge_nbgrader = self.nbgrader_metadata(merge_cell)
                merge_nbgrader["notebook"] = notebook
        return merge_result


class Submissions:
    """
    holds multiple submissions
    """

    def __init__(
            self,
            submissions: typing.Optional[typing.List[Submission]] = None,
            source_notebook: GraderNotebook = None,
            debug: bool=False
    ):
        """
        constructor
        Args:
            submissions: list of submissions
            source_notebook: source notebook of the submissions
        """
        self.debug=debug
        if submissions is None:
            submissions = []
        self.submissions = submissions
        self.source_notebook = source_notebook

    def add_submission(self, submission: Submission):
        """
        add subission to submissions
        Args:
            submission: submission to add
        """
        logger.debug(f"Adding submission {submission.notebook_filepath}")
        self.submissions.append(submission)

    def __len__(self):
        return len(self.submissions)

    def generate_python_files(self, target_dir: str, template_filepath: str = None, with_cell_comments:bool=False):
        """
        generate python files of the submissions
        Args:
            target_dir: target directory to store the file
            template_filepath: template to use to generate the python files
            with_cell_comments(bool): if true add jupyter cell metadata as python comments 
        """
        path = Path(target_dir)
        if not path.exists():
            logger.info(f"Target directory does not exist → creating directory '{target_dir}'")
            path.mkdir(exist_ok=True, parents=True)
        if not path.is_dir():
            logger.error(f"Target directory '{target_dir}' is not a directory")
            return
        if self.source_notebook is None:
            logger.info("Source notebook is not defined!")
        total = len(self)
        for i, submission in enumerate(self.submissions, start=1):
            merged_notebook: GraderNotebook = submission.merge_code(self.source_notebook)
            py_file_name = f"test_{self.source_notebook.name}_submission_{i:04}.py"
            py_file_path = path.joinpath(py_file_name)
            py_code = merged_notebook.as_python_code(template_filepath,with_cell_comments=with_cell_comments)
            with open(py_file_path, mode="w") as f:
                f.write(py_code)
            logger.debug(f"({i:04}/{total:04}) Generated {py_file_name}")

    @classmethod
    def from_zip(cls, file_path: str,debug:bool=False) -> "Submissions":
        """
        Generate Submissions from given zip file
        Args:
            file_path: zip file path
            source_notebook: source notebook of the submissions

        Returns:
            Submissions
        """
        path = Path(file_path)
        if not path.is_file():
            raise Exception(f"{path} is not a file")
        if not zipfile.is_zipfile(path):
            raise Exception(f"{path} is not a zip file")
        submissions = Submissions(debug=debug)
        # https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile.open
        with zipfile.ZipFile(path, 'r') as archive:
            for file_name in archive.namelist():
                if ".ipynb" in file_name:
                    notebook_content = archive.read(file_name)
                    notebook_file = io.BytesIO(notebook_content)
                    notebook_file.name = file_name
                    submission = Submission(notebook_file,debug=debug)
                    submissions.add_submission(submission)
        return submissions