# cloudatcost_fabric
Cloud At Cost is a crappy provider that's OK for throwaway servers.
This script makes setting up new machines a bit less of a miserable experience.

## usage:
```
% virtualenv env
...
% source env/bin/activate
(env) % pip install -r requirements.txt
...
(env) % ./cloudatcost_fabric.py -h
```

Fabric will take care of asking for hostname or IP address and credentials.
