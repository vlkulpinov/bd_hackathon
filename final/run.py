import flask
import sys
import requests
import datetime

import emoji

app = flask.Flask(__name__)

@app.route('/')
def hello_world():
    return flask.render_template('main.html')


@app.route('/block_info', methods=['GET'])
def block_info():
    block = flask.request.args.get('block_hash')

    try:
        r = requests.get('https://blockchain.info/rawblock/' + block)
        d = r.json()
        d['chain_name'] = 'Bitcoin Core'
        d['ts'] = datetime.datetime.utcfromtimestamp(d['time'])
        d['tx_count'] = d['n_tx']
        d['e'] = emoji.emojify(block)
        print('Core')
        return flask.jsonify(d)
    except Exception as ex:
        print 'Error 1'
        print r
        print ex
        pass

    try:
        r = requests.get('https://bitcoincash.blockexplorer.com/api/block/' + block)
        d = r.json()
        d['mrkl_root'] = d['merkleroot']
        d['chain_name'] = 'Bitcoin Cash'
        d['ts'] = datetime.datetime.utcfromtimestamp(d['time'])
        d['tx_count'] = len(d['tx'])
        print('Cash')
        return flask.jsonify(d) 
    except Exception as ex:
        print 'Error 2'
        print r
        print ex
        pass

    try:
        r = requests.get('https://nodes.wavesnodes.com/blocks/signature/' + block)
        d = r.json()
        d['mrkl_root'] = 'N/A'
        d['chain_name'] = 'Waves Mainnet'
        d['ts'] = datetime.datetime.utcfromtimestamp(d['timestamp'] / 1000)
        d['tx_count'] = len(d['transactions'])
        return flask.jsonify(d)
    except Exception as ex:
        print 'Error 3'
        print r 
        print ex
        pass

    return flask.jsonify({"mrkl_root": "123", "ts": "01/01/2017 00:00:00", "chain_name": "test1"})

if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True, host='0.0.0.0')