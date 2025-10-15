from pydantic import BaseModel, Field
from typing import List

class PontuacaoRow(BaseModel):
    matricula: str
    pontos: int
    periodo: str

class OcorrenciaRow(BaseModel):
    matricula: str
    evento: str
    periodo: str

class ArmasRow(BaseModel):
    matricula: str
    arma: int
    periodo: str

SCHEMA_MAP = {
    "Pontuação": PontuacaoRow,
    "Ocorrência": OcorrenciaRow,
    "Armas": ArmasRow,
}

def validate_data(sheet_title: str, data: List[dict]):
    """
    Validates a list of dictionaries against a Pydantic schema.

    Args:
        sheet_title (str): The title of the sheet, used to look up the schema.
        data (List[dict]): The data to validate.

    Raises:
        ValueError: If the validation fails.
    """
    if sheet_title not in SCHEMA_MAP:
        print(f"Warning: No schema found for sheet '{sheet_title}'. Skipping validation.")
        return

    schema = SCHEMA_MAP[sheet_title]
    try:
        [schema.model_validate(row) for row in data]
        print(f"Data for sheet '{sheet_title}' successfully validated against schema.")
    except Exception as e:
        raise ValueError(f"Schema validation failed for sheet '{sheet_title}': {e}")