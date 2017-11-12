from __future__ import print_function

import requests
import json

rpcPort = 8333
rpcAddrs = ['181.41.188.2', '93.190.205.25', '185.4.24.199']
rpcUser = 'bitcoinrpc'
rpcPassword = '6rVvvA8BqqdhyR4dVcszYdgF2jR8hGkhnmPtXaSDBB4s'
serverUrl = 'http://{rpcUser}:{rpcPassword}@{rpcAddr}:{rpcPort}'.format(
    rpcUser = rpcUser,
    rpcAddr = rpcAddrs[2],
    rpcPassword = rpcPassword,
    rpcPort = rpcPort
)
headers = {'content-type': 'application/json'}
payload = json.dumps({
    "method": "getblockcount"
})
response = requests.get(serverUrl, headers=headers, data=payload)
print(response)
print(response.json())