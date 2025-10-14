import pandas as pd
from pandas.testing import assert_frame_equal
import yaml
from google_sheets_extractor.processor import reconcile_and_calculate

def test_reconcile_and_calculate(tmp_path):
    # Create a dummy metrics.yaml file
    metrics_config = {
        'metrics': {
            'total_pontos': {'column': 'pontos', 'agg': 'sum'},
            'ocorrencias': {'column': 'evento', 'agg': 'count'},
            'armas_unicas': {'column': 'arma', 'agg': 'count_non_zero'}
        }
    }
    config_path = tmp_path / "metrics.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(metrics_config, f)

    # Create sample data
    data_dict = {
        'Pontuação': pd.DataFrame({
            'matricula': ['101', '102', '103'],
            'pontos': [10, 20, 30],
            'periodo': ['202301', '202301', '202302']
        }),
        'Ocorrência': pd.DataFrame({
            'matricula': ['101', '102', '104'],
            'evento': ['A', 'B', 'C'],
            'periodo': ['202301', '202301', '202302']
        }),
        'Armas': pd.DataFrame({
            'matricula': ['101', '103', '104'],
            'arma': [1, 0, 1],
            'periodo': ['202301', '202302', '202302']
        })
    }

    # Convert dataframes to list of dictionaries to simulate the real input
    data_dict_list = {k: v.to_dict('records') for k, v in data_dict.items()}

    # Expected output
    expected_df = pd.DataFrame({
        'matricula': ['101', '102', '103', '104'],
        'total_pontos': [10.0, 20.0, 30.0, 0.0],
        'ocorrencias': [1, 1, 0, 1],
        'armas_unicas': [1, 0, 0, 1]
    })


    # Run the function
    result_df = reconcile_and_calculate(data_dict_list, str(config_path))

    # Sort by matricula to ensure order doesn't affect the test
    result_df = result_df.sort_values(by='matricula').reset_index(drop=True)
    expected_df = expected_df.sort_values(by='matricula').reset_index(drop=True)

    # Also sort columns to ensure order doesn't affect the test
    result_df = result_df.reindex(sorted(result_df.columns), axis=1)
    expected_df = expected_df.reindex(sorted(expected_df.columns), axis=1)

    # Check the results
    assert_frame_equal(result_df, expected_df, check_dtype=False)