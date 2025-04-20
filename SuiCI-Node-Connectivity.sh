#!/bin/bash
# verify proper routing and ping to end nodes 

declare -A IP_MAP=(
  [London Perf Monitor]="103.219.168.237"
  [lon-tnt-val-00]="103.50.32.105"
  [lhr-tnt-val-00]="209.250.224.204"
  [New York Perf Monitor]="185.209.178.81"
  [ewr-tnt-val-00]="140.82.3.223"
  [Tokyo Perf Monitor]="45.250.255.74"
  [ty6-tnt-val-00]="45.250.255.101"
  [nrt-tnt-ssfn-scion-00]="202.182.103.246"
  [Artifact Testnet RPC4]="80.93.18.171"
  [sui-fullnode-korea]="58.229.105.83"
)
declare -A EDGE_MAP=(
  [London Perf Monitor]="ML London Latitude"
  [lon-tnt-val-00]="ML London Latitude"
  [lhr-tnt-val-00]="ML London Latitude"
  [New York Perf Monitor]="ML New York Latitude"
  [ewr-tnt-val-00]="ML New York Latitude"
  [Tokyo Perf Monitor]="ML Tokyo Latitude"
  [ty6-tnt-val-00]="ML Tokyo Latitude"
  [nrt-tnt-ssfn-scion-00]="ML Tokyo Latitude"
  [Artifact Testnet RPC4]="Artifact London Latitude"
  [sui-fullnode-korea]="NodeInfra Tokyo Latitude"
)

for NODE in "${!IP_MAP[@]}"; do
  EDGE=${EDGE_MAP[$NODE]}
  IP=${IP_MAP[$NODE]}
    echo -n $EDGE,$IP,$NODE,
    ROUTE=`ip route | grep bgp | egrep "^$IP"`
    # if no bgp lines are found in the grep then no route is in place
    if [ "$?" -eq 1 ]; then
        echo "no route"
        continue
    fi

    ping -c 5 $IP > /dev/null
    if [ "$?" -eq 1 ]; then
        echo "no ping"
        continue
    fi

    echo "OK"
done
