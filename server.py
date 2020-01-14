from flask import Flask, render_template, request
import requests
import config
import gpu_helper
from statistics import get_stats_df, get_time_str
import logging
import time

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.logger.setLevel(logging.INFO)


@app.route('/')
def index():
    return render_template('index.html', stats_time=get_time_str())

@app.route('/gpu_usage')
def gpu_usage():
    show_all = (request.args.get('show_all', '0') == '1')
    infos = {server: gpu_helper.get_remote_info(server) for server in config.servers}

    return render_template('usage.html', infos=infos, show_all=show_all)

@app.route('/statistics')
def statistics():
    df = get_stats_df()
    columns=['Name', 'GPU Time', 'Used Power [Wh]', 'Generated CO2 [kg]', 'Trees * year to offset', 'Avg. Util [%]']

    return df.to_html(index=False, table_id='stats_table', classes='tablesorter', columns=columns)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000, help="port to run server on")
    parser.add_argument('--host', default='0.0.0.0', help="which host to listen on")
    parser.add_argument('--config', help="json config file")
    
    args = parser.parse_args()
    if args.config is not None:
        config.update_config(args.config)

    gpu_helper.setup()
    app.run(debug=True, host=args.host, port=args.port) 