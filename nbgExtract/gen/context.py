import io
import json
import logging
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from nbgExtract.cells import Cell, NbgraderCellType

logger = logging.getLogger(__name__)


class NotebookContext:
    """
    jupyter notebook cell context to execute cell code and
    keep control over output, exceptions and received points in case of nbgrader test cells
    """

    def __init__(self, name: str, show_output: bool = True, suppress_exception: bool = False):
        """
        constructor
        Args:
            name: name of the notebook
            show_output: If True show output of cells otherwise cell output is not shown
            suppress_exception: If False when a cell raises an exception the execution of the other cells is not influenced
        """
        self.name = name
        self.show_output = show_output
        self.suppress_exception = suppress_exception
        self.cell_output = io.StringIO()
        self.output_catcher = redirect_stdout(self.cell_output)
        self._current_cell = None
        self.tests: List[NbgCellTestResult] = []

    def __enter__(self):
        self._reset_cell_output()
        self.output_catcher.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.output_catcher.__exit__(exc_type, exc_val, exc_tb)
        cell_output = self.cell_output.getvalue()
        self._reset_cell_output()
        if self.show_output:
            print(cell_output)
        if exc_val:
            if self.suppress_exception:
                return True
            else:
                raise exc_val
        if isinstance(self._current_cell, Cell):
            nbg_metadata = self._current_cell.get_nbg_metadata()
            nbg_cell_type = nbg_metadata.get_type()
            if nbg_cell_type is NbgraderCellType.AUTOGRADED_TESTS:
                score = self.score_from_output(cell_output)
                cell_res = NbgCellTestResult(
                        grade_id=nbg_metadata.grade_id,
                        max_points=nbg_metadata.points,
                        points=score
                )
                self.tests.append(cell_res)
        self._current_cell = None

    def __call__(self, cell_metadata: Optional[dict] = None):
        try:
            self._current_cell = Cell(**cell_metadata)
        except:
            logger.error(f"Cell metadata could not be converted to cell object: {cell_metadata}")
            pass
        return self

    def _reset_cell_output(self):
        self.cell_output.truncate(0)
        self.cell_output.seek(0)

    def score_from_output(self, output: str) -> Optional[float]:
        """
        Get received points from output
        Assumption: score is printed as last expression as usual in nbgrader notebook
        Args:
            output:

        Returns:

        """
        score_str = output.strip().split("\n")[-1]  # ToDo: Make fail safe
        try:
            score = float(score_str)
        except ValueError:
            score = None
        return score

    def generate_notebook_result(self):
        record = {
            "notebook": self.name,
            "total": sum([test_res.points for test_res in self.tests if test_res.points is not None]),
            **{test_res.grade_id: test_res.points for test_res in self.tests}
        }
        return record

    def store_notebook_result(self, target: Path):
        """
        Store the notebook result by appending the record to the given target
        Args:
            target: location to store the record
        """
        res = self.generate_notebook_result()
        with open(target, mode="a") as fp:
            json_str = json.dumps(res)
            fp.write(json_str)
            fp.write("\n")


@dataclass
class NbgCellTestResult:
    """
    Holds nbgrader cell test result
    """
    grade_id: str
    max_points: float
    points: float