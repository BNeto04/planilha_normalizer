def create_filter_view_request(sheet_id: int, end_row: int, end_column: int) -> dict:
    """Creates the request body for adding a filter view."""
    return {
        "addFilterView": {
            "filter": {
                "title": "Filtro por Matrícula e Período",
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": end_row,
                    "startColumnIndex": 0,
                    "endColumnIndex": end_column
                }
            }
        }
    }

def create_chart_request(sheet_id: int, end_row: int, end_column: int) -> dict:
    """Creates the request body for adding a chart."""
    return {
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Métricas por Matrícula",
                    "basicChart": {
                        "chartType": "COLUMN",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {"position": "BOTTOM_AXIS", "title": "Matrícula"},
                            {"position": "LEFT_AXIS", "title": "Valores"}
                        ],
                        "domains": [{
                            "domain": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": sheet_id,
                                        "startRowIndex": 0,
                                        "endRowIndex": end_row,
                                        "startColumnIndex": 0,
                                        "endColumnIndex": 1
                                    }]
                                }
                            }
                        }],
                        "series": [
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": sheet_id,
                                            "startRowIndex": 0,
                                            "endRowIndex": end_row,
                                            "startColumnIndex": 2,
                                            "endColumnIndex": 3
                                        }]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS"
                            },
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": sheet_id,
                                            "startRowIndex": 0,
                                            "endRowIndex": end_row,
                                            "startColumnIndex": 3,
                                            "endColumnIndex": 4
                                        }]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS"
                            }
                        ]
                    }
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": sheet_id,
                            "rowIndex": 1,
                            "columnIndex": end_column + 1
                        }
                    }
                }
            }
        }
    }

def create_slicer_request(sheet_id: int, end_row: int, end_column: int) -> dict:
    """Creates the request body for adding a slicer."""
    return {
        "addSlicer": {
            "slicer": {
                "spec": {
                    "dataRange": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": end_row,
                        "startColumnIndex": 0,
                        "endColumnIndex": end_column
                    },
                    "title": "Filtro por Período",
                    "columnIndex": 1
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": sheet_id,
                            "rowIndex": 1,
                            "columnIndex": end_column + 7
                        }
                    }
                }
            }
        }
    }

def create_auto_resize_columns_request(sheet_id: int, end_column: int) -> dict:
    """Creates the request body for auto-resizing columns."""
    return {
        "autoResizeDimensions": {
            "dimensions": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 0,
                "endIndex": end_column
            }
        }
    }