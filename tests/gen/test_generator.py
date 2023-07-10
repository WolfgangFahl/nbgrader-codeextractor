import contextlib
import tempfile
import unittest
from pathlib import Path
import io
from runpy import run_path

from nbgExtract.gen.generator import NbgCodeGenerator
from nbgExtract.notebook import GraderNotebook, Submissions


class TestNbgCodeGenerator(unittest.TestCase):

    def setUp(self) -> None:
        """
        setup test env
        """
        self.resource_dir = f"{Path(__file__).parent.parent.absolute()}/resources"

    def test_generate_file(self):
        """
        test code generation with NotebookContext
        """
        source_file = f"{self.resource_dir}/python_addition/python_addition_source.ipynb"
        zip_file = f"{self.resource_dir}/python_addition/submissions.zip"
        with tempfile.TemporaryDirectory() as target:
            submissions = Submissions.from_zip(zip_file)
            source_notebook = GraderNotebook(source_file)
            for submission in submissions.submissions:
                s_merged = submission.merge_code(source_notebook)
                generator = NbgCodeGenerator()
                generator.generate_file(s_merged, Path(target))
            expected_file = Path(target).joinpath("test_Group 1_122542_assignsubmission_file", "python_addition_correct_submission.py")
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                x = run_path(expected_file)
                x.get("main")()
            output = f.getvalue()
            self.assertIn("[NbgCellTestResult(grade_id='cell-744e5dbe470759ae', max_points=1, points=1.0)]", output)


if __name__ == '__main__':
    unittest.main()
