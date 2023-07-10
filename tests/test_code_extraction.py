import logging
import os
import tempfile
import unittest
from pathlib import Path
import nbgExtract
from nbgExtract.notebook import GraderNotebook, Submission, Submissions
from nbgExtract import logger


class TestGraderNotebook(unittest.TestCase):
    """
    test GraderNotebook
    """

    def setUp(self) -> None:
        """
        setup test env
        """
        self.resource_dir = Path(__file__).parent.absolute().joinpath("resources")
        self.module_resources = Path(nbgExtract.__file__).parent.joinpath("resources")

    def test_extraction(self):
        """
        tests extraction of code cells
        """
        assignment_dir = f"{self.resource_dir}/python_addition"
        test_params = [ # file path of assignment, strings that should be extracted
            (f"{assignment_dir}/python_addition_source.ipynb",
             ["e2d83191-805e-4049-984a-af12d9f04d22", "### BEGIN SOLUTION", "45974d03-58e0-42b6-941a-25aef37fc8f5", "### BEGIN HIDDEN TESTS"]),
            (f"{assignment_dir}/python_addition_release.ipynb",
             ["e2d83191-805e-4049-984a-af12d9f04d22", "# YOUR CODE HERE", "raise NotImplementedError()", "45974d03-58e0-42b6-941a-25aef37fc8f5"]),
            (f"{assignment_dir}/python_addition_correct_submission.ipynb",
             ["e2d83191-805e-4049-984a-af12d9f04d22", "# YOUR CODE HERE", "z = x + y", "45974d03-58e0-42b6-941a-25aef37fc8f5"]),
        ]
        for test_param in test_params:
            with self.subTest(test_param=test_param):
                assignment_filepath, expected_extractions = test_param
                grader_notebook = GraderNotebook(assignment_filepath)
                code = grader_notebook.as_python_code(template_filepath=self.module_resources.joinpath("unittest_template.tpy"))
                print(code)
                for expected in expected_extractions:
                    self.assertIn(expected, code)

    def test__get_indented_by(self):
        """
        tests _get_indented_by
        """
        test_params = [
            (4, r"{{code}}", "import sys\n    {{code}}\n"),
            (4, r"\{\{ *code *\}\}", "import sys\n    {{ code }}\n"),
            (2, "2", "0\n 1\n  2\n   3\n")
        ]
        for test_param in test_params:
            with self.subTest(test_param=test_param):
                expected_indent, key, template = test_param
                actual_indent, line = GraderNotebook._get_indented_by(key, template)
                self.assertEqual(expected_indent, actual_indent)

    def test_nbg_cell_type_extraction(self):
        filepath = self.resource_dir.joinpath("nbgrader_cell_types.ipynb")
        notebook = GraderNotebook(filepath)
        for cell in notebook.cells:
            with self.subTest(cell=cell):
                nbg_metadata = cell.get_nbg_metadata()
                if nbg_metadata:
                    nbg_cell_type = nbg_metadata.get_type()
                    self.assertEqual("".join(cell.source), nbg_cell_type.value)
                else:
                    self.assertEqual("None", "".join(cell.source))


class TestSubmission(unittest.TestCase):
    """
    test Submission
    """

    def setUp(self) -> None:
        """
        setup test env
        """
        self.resource_dir = f"{Path(__file__).parent.absolute()}/resources"
        self.module_resources = Path(nbgExtract.__file__).parent.joinpath("resources")

    def test_merging_code(self):
        """
        tests merging code cells of a submission with its source
        """
        source_file = f"{self.resource_dir}/python_addition/python_addition_source.ipynb"
        submission_file = f"{self.resource_dir}/python_addition/python_addition_correct_submission.ipynb"
        grader_notebook = GraderNotebook(source_file)
        submission = Submission(notebook=submission_file)
        merged_submission = submission.merge_code(grader_notebook)
        code = merged_submission.as_python_code(template_filepath=self.module_resources.joinpath("unittest_template.tpy"))
        expected_lines = ["e2d83191-805e-4049-984a-af12d9f04d22", "# YOUR CODE HERE", "### BEGIN HIDDEN TESTS"]
        for expected_line in expected_lines:
            self.assertIn(expected_line, code)


class TestSubmissions(unittest.TestCase):
    """
    test Submissions
    """

    def setUp(self) -> None:
        """
        setup test env
        """
        self.resource_dir = f"{Path(__file__).parent.absolute()}/resources"
        self.module_resources = Path(nbgExtract.__file__).parent.joinpath("resources")
        logger.setLevel(logging.DEBUG)

    def test_from_zip(self):
        """
        tests parsing submissions from zip file
        """
        source_file = f"{self.resource_dir}/python_addition/python_addition_source.ipynb"
        zip_file = f"{self.resource_dir}/python_addition/submissions.zip"
        source_notebook = GraderNotebook(source_file, name="addition")
        submissions = Submissions.from_zip(zip_file)
        self.assertEqual(2, len(submissions))
        submissions.source_notebook = source_notebook
        with tempfile.TemporaryDirectory() as tmpdirname:
            submissions.generate_python_files(tmpdirname)
            expected_files = [
                'test_Group 1_122542_assignsubmission_file/python_addition_correct_submission.py',
                'test_Group 2_122543_assignsubmission_file/python_addition_release.py'
            ]
            for expected_file in expected_files:
                self.assertTrue(Path(tmpdirname).joinpath(expected_file).is_file())


if __name__ == '__main__':
    unittest.main()
