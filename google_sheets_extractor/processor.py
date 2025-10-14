import pandas as pd
import yaml
from functools import reduce

# --- AGGREGATION MAPPING ---
# Maps the 'agg' string from YAML to a pandas-compatible aggregation function.
AGG_FUNC_MAP = {
    "sum": "sum",
    "count": "count",
    "mean": "mean",
    "max": "max",
    "min": "min",
    "count_non_zero": lambda x: (x != 0).sum()
}

def _load_metrics_config(config_path: str) -> dict:
    """Loads and validates the metrics configuration from a YAML file."""
    print(f"Loading metrics configuration from: {config_path}")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    if 'metrics' not in config or not isinstance(config['metrics'], dict):
        raise ValueError("Metrics configuration must contain a 'metrics' dictionary.")

    # Validate each metric definition
    for name, definition in config['metrics'].items():
        if not all(k in definition for k in ['column', 'agg']):
            raise ValueError(f"Metric '{name}' is missing 'column' or 'agg' key.")
        if definition['agg'] not in AGG_FUNC_MAP:
            raise ValueError(f"Unsupported aggregation function '{definition['agg']}' for metric '{name}'.")

    print("Metrics configuration loaded successfully.")
    return config['metrics']

def reconcile_and_calculate(data_dict: dict, metrics_config_path: str) -> pd.DataFrame:
    """
    Reconciles data, then dynamically calculates metrics based on a YAML configuration.

    Args:
        data_dict (dict): A dictionary of normalized data per sheet.
        metrics_config_path (str): The file path to the metrics.yaml configuration.

    Returns:
        pd.DataFrame: A DataFrame with consolidated and calculated metrics.
    """
    if not data_dict:
        return pd.DataFrame()

    # Load dynamic metrics configuration
    metrics_config = _load_metrics_config(metrics_config_path)

    # Convert each sheet's data into a DataFrame
    dfs = [pd.DataFrame(data) for data in data_dict.values() if data and 'matricula' in pd.DataFrame(data).columns]
    if not dfs:
        return pd.DataFrame()

    # Perform a full outer merge on 'matricula'
    merged_df = reduce(lambda left, right: pd.merge(left, right, on='matricula', how='outer'), dfs)

    # --- DYNAMIC METRIC CALCULATIONS ---
    # Fill NaNs in columns that are specified in the metrics config
    for metric in metrics_config.values():
        col = metric['column']
        if col in merged_df.columns:
            # For count operations, we need to fill with a value that indicates "no event"
            # but for sum, we need to fill with 0.
            if metric['agg'] == 'count':
                # Fill with a value that won't be counted, but preserves the column
                merged_df[col] = merged_df[col].fillna(pd.NA)
            else:
                merged_df[col] = merged_df[col].fillna(0)

    # Define grouping keys
    grouping_keys = ['matricula']
    if 'periodo' in merged_df.columns:
        # Take the first available period for each matricula
        merged_df['periodo'] = merged_df.groupby('matricula')['periodo'].transform('first')

    # Build the aggregation dictionary dynamically from the config
    agg_dict = {}
    for metric_name, definition in metrics_config.items():
        column = definition['column']
        agg_func_key = definition['agg']
        agg_func = AGG_FUNC_MAP[agg_func_key]

        # Ensure the column exists in the dataframe before adding to agg_dict
        if column in merged_df.columns:
            agg_dict[metric_name] = pd.NamedAgg(column=column, aggfunc=agg_func)

    if not agg_dict:
        print("Warning: No metrics could be applied. Check if columns in metrics.yaml exist in the data.")
        return pd.DataFrame()

    # Perform aggregation
    print(f"Aggregating data by {grouping_keys} with metrics: {list(agg_dict.keys())}")
    metrics_df = merged_df.groupby(grouping_keys).agg(**agg_dict).reset_index()

    return metrics_df