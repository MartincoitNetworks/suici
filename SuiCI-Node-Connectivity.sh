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
  [Artifact Testnet RPC6]="46.166.162.34"
  [sui-fullnode-korea]="58.229.105.83"
  [ewr-tnt-sto-00.walrus-testnet.walrus.space]="140.82.3.172"
  [Ruby Nodes Testnet Validator]="45.250.253.69"
  [lhr-tnt-sto-00.walrus-testnet.walrus.space]="45.77.230.234"
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
  [Artifact Testnet RPC6]="Artifact London Latitude"
  [sui-fullnode-korea]="NodeInfra Tokyo Latitude"
  [ewr-tnt-sto-00.walrus-testnet.walrus.space]="ML New York Latitude"
  [Ruby Nodes Testnet Validator]="ML New York Latitude"
  [lhr-tnt-sto-00.walrus-testnet.walrus.space]="ML London Latitude"
)

ME=`hostname`
case "$ME" in
  "london")
        MY_EDGE="ML London Latitude"
        ;;
  "newyork")
        MY_EDGE="ML New York Latitude"
        ;;
          "tokyo")
        MY_EDGE="ML Tokyo Latitude"
        ;;
  *)
        MY_EDGE=""
        ;;
esac

for NODE in "${!IP_MAP[@]}"; do
  EDGE=${EDGE_MAP[$NODE]}

  if [[ "$EDGE" == "$MY_EDGE" ]]; then
    continue
  fi

  IP=${IP_MAP[$NODE]}
    echo -n `date -u`,$ME,
    echo -n $EDGE,$IP,$NODE,
    ROUTE=`ip route show to match $IP | egrep "proto bgp"`
    # if no bgp lines are found in the grep then no route is in place
    if [ "$?" -eq 1 ]; then
        echo -n "Legacy Internet,"
    else
        echo -n "SCION Sui,"
    fi

    PING=`ping -c 5 $IP | egrep '(^rtt min/avg/max/mdev)' | cut -d/ -f5 | cut -d. -f1 2> /dev/null`
    if [ "$?" -eq 1 ]; then
        echo -n "-1"
    else
        echo -n "$PING"
    fi

    echo

done

