import pandas as pd
from functools import reduce

def reconcile_and_calculate(data_dict: dict) -> pd.DataFrame:
    """
    Reconciles data from multiple sheets and calculates metrics.

    Args:
        data_dict (dict): A dictionary where keys are sheet titles (e.g., 'Pontuação', 'Ocorrência')
                          and values are lists of dictionaries (normalized data for that sheet).

    Returns:
        pd.DataFrame: A DataFrame with the consolidated and calculated metrics,
                      grouped by 'matricula' and 'periodo'.
    """
    if not data_dict:
        return pd.DataFrame()

    # Convert each sheet's data into a DataFrame
    dfs = []
    for sheet_title, data in data_dict.items():
        if data:
            df = pd.DataFrame(data)
            # Ensure 'matricula' is a common key and handle potential missing columns
            if 'matricula' in df.columns:
                dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    # Perform a full outer merge on 'matricula'
    merged_df = reduce(lambda left, right: pd.merge(left, right, on='matricula', how='outer'), dfs)

    # --- METRIC CALCULATIONS ---
    # Fill NaN values that resulted from the merge
    merged_df['pontuacao'] = merged_df['pontuacao'].fillna(0)
    merged_df['ocorrencia'] = merged_df['ocorrencia'].fillna(0)
    # If other columns like 'armas' need to be counted or handled, they can be added here.

    # Example metrics: Sum of scores, count of occurrences
    # Group by 'matricula' and 'periodo' if it exists.
    grouping_keys = ['matricula']
    if 'periodo' in merged_df.columns:
        grouping_keys.append('periodo')
        # Forward-fill 'periodo' to associate it with all records for a 'matricula' if it's sparse
        merged_df['periodo'] = merged_df.groupby('matricula')['periodo'].ffill().bfill()


    # Perform aggregation
    metrics = merged_df.groupby(grouping_keys).agg(
        total_pontuacao=('pontuacao', 'sum'),
        quantidade_ocorrencias=('ocorrencia', lambda x: (x != 0).sum()),
        # Add other metrics as needed. For example, counting weapons:
        # quantidade_armas=('arma_de_fogo', 'count')
    ).reset_index()

    return metrics