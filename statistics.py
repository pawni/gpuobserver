from gpu_helper import cache
import pandas as pd

def construct_df():
    users = cache['users']
    user_names = list(users.keys())
    data_cols = list(users[user_names[0]].keys())
    columns = ['user'] + data_cols

    df = pd.DataFrame(columns=columns)
    for user, data in users.items():
        df.loc[len(df)] = [user, ] + [data[k] for k in columns[1:]]

    return df

def get_stats_df() -> pd.DataFrame:
    df = construct_df()
    rows = []
    for _, row in df.iterrows():
        emissions = row['cum_energy'] * 0.30675 / 1000
        info = {
            'Name': row['name'],
            'GPU Time': str(row['time']),
            'Used Power [Wh]': row['cum_energy'],
            'Generated CO2 [kg]': emissions,
            'Trees * year to offset': emissions / 10,
            'Avg. Util [%]': row['cum_util'] / row['inc']
        }
        rows.append(info)

    return pd.DataFrame(rows)

def get_time_str():
    return cache['since'].strftime("%d.%m.%Y at %H:%M:%S")