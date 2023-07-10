from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class NbgraderCellType(Enum):
    """
    nbgrader cell types
    """
    AUTOGRADED_ANSWER = "Autograded answer"
    AUTOGRADED_TESTS = "Autograded tests"
    MANUALLY_GRADED_ANSWER = "Manually graded answer"
    MANUALLY_GRADED_TASK = "Manually graded task"
    READ_ONLY = "Read-only"


@dataclass
class NbgraderCellMetadata:
    """
    nbgrader cell metadata
    see https://nbgrader.readthedocs.io/en/stable/contributor_guide/metadata.html
    """
    schema_version: int
    grade: bool
    grade_id: str
    solution: bool
    locked: bool
    points: Optional[int] = None
    checksum: Optional[str] = None
    notebook: Optional[dict] = None
    cell_type: Optional[str] = None  # added with v2
    task: Optional[bool] = None  # added with v3?

    def get_type(self) -> Optional[NbgraderCellType]:
        """
        Get nbgrader cell type

        Returns:
            NbgraderCellType:
            None: If cell type is not known or not set
        """
        nbg_cell_type = None
        if not self.grade and self.solution and not self.task:
            nbg_cell_type = NbgraderCellType.AUTOGRADED_ANSWER
        elif self.grade and not self.solution and not self.task:
            nbg_cell_type = NbgraderCellType.AUTOGRADED_TESTS
        elif self.grade and self.solution and not self.task:
            nbg_cell_type = NbgraderCellType.MANUALLY_GRADED_ANSWER
        elif not self.grade and not self.solution and self.task:
            nbg_cell_type = NbgraderCellType.MANUALLY_GRADED_TASK
        elif self.locked and not self.grade and not self.solution and not self.task:
            nbg_cell_type = NbgraderCellType.READ_ONLY
        return nbg_cell_type


@dataclass
class Cell:
    """
    cell of a jupyter notebook
    """
    cell_type: str
    id: str = None
    metadata: dict = None
    source: List[str] = None
    execution_count: int = None
    outputs: List[str] = None
    attachments: dict = None

    def get_nbg_metadata(self) -> Optional[NbgraderCellMetadata]:
        """

        Returns:
            NbgraderCellMetadata: if the cell has nbgrader metadata
            None: otherwise
        """
        nbg_metadata = None
        metadata_key = "nbgrader"
        if metadata_key in self.metadata:
            try:
                nbg_metadata = NbgraderCellMetadata(**self.metadata.get(metadata_key))
            except TypeError as ex:
                pass
        return nbg_metadata
