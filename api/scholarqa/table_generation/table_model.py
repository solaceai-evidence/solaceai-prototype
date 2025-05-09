# Data structure to represent a table
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class TableWidget(BaseModel):
    id: str = Field(description="Unique identifier for the table widget")
    rows: List["TableRow"] = Field(
        default_factory=list, description="List of rows in the table"
    )
    columns: List["TableColumn"] = Field(
        default_factory=list, description="List of columns in the table"
    )
    cells: Dict[str, "TableCell"] = Field(
        default_factory=dict,
        description="Dictionary of cells in the table. Key is in the format ${row.id}-${column.id}",
    )
    title: Optional[str] = Field(default=None, description="Title for table generated")

    def add_rows(self, new_rows: List["TableRow"]) -> None:
        self.rows.extend(new_rows)

    def add_columns(self, new_columns: List["TableColumn"]) -> None:
        self.columns.extend(new_columns)
    
    def to_dict(self) -> dict:
        table = {}
        table["id"] = self.id
        table["title"] = self.title
        table["rows"] = [row.__dict__ for row in self.rows]
        table["columns"] = [column.__dict__ for column in self.columns]
        table["cells"] = {k: v.__dict__ for k, v in self.cells.items()}
        return table


class TableRow(BaseModel):
    id: str = Field(description="Unique identifier for the row")
    display_value: Optional[str] = Field(
        default=None, description="Display value of the row"
    )
    paper_corpus_id: Optional[int] = Field(description="Corpus id of a paper")


class TableColumn(BaseModel):
    id: str = Field(description="Unique identifier for the column")
    name: str = Field(description="Name of the column")
    description: str = Field(description="Description of the column")
    is_metadata: Optional[bool] = Field(
        default=False,
        description="Flag indicating whether the column to be populated is a metadata column or not",
    )
    tools: List[str] = Field(
        description="List of tools used to generate the column values"
    )


class TableCell(BaseModel):
    id: str = Field(
        description="Unique identifier for the cell. In the format ${row.id}-${column.id}"
    )
    value: Optional[str | int] = Field(default=None, description="Value of the cell")
    display_value: str = Field(description="Display value of the cell")
    is_loading: bool = Field(
        default=False, description="Whether the cell is still loading"
    )
    error: Optional[str] = Field(default=None, description="Error message if any")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Metadata of the cell"
    )
    edited_value: Optional[str] = Field(
        default=None,
        description="overridden cell value by a user, nora, or other 3rd party",
    )
    edited_by_uuid: Optional[str] = Field(
        default=None, description="Who last edited the table cell"
    )