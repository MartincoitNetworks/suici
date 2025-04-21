CYBL_NYC_CORE="67-2:0:6e"
CYBL_LON_CORE="65-2:0:6c"
CYBL_TYO_CORE="66-2:0:6d"

INTC_NYC_CORE="67-2:0:26"
INTC_LON_CORE="65-2:0:51"
INTC_TYO_CORE="66-2:0:55"

TYO_EDGE_AS="66-2:0:7f"
TYO_EDGE_IP="66-2:0:7f,72.46.86.107"
NYC_EDGE_AS="67-2:0:7f"
NYC_EDGE_IP="67-2:0:7f,67.213.112.167"
LON_EDGE_AS="65-2:0:89"
LON_EDGE_IP="65-2:0:89,103.219.168.149"

MY_AS=`scion address | cut -d ',' -f1`
MY_ISD=`scion address | cut -d '-' -f1`


scion_ping() {
  DEST_ADDR=$1
  SEQUENCE=$2
  LATENCY=`scion ping --sequence "$SEQUENCE" $DEST_ADDR -c 3 2> /dev/null | egrep '(^rtt min/avg/max/mdev)' | cut -d/ -f5 | cut -d. -f1`
  if [ -z "${LATENCY}" ]; then
          LATENCY=-1
  fi
  echo $LATENCY
  return $LATENCY
}

scion_ping_best() {
  DEST_ADDR=$1
  LATENCY=`echo 0 | scion ping $DEST_ADDR -c 3 -i | egrep '(^rtt min/avg/max/mdev)' | cut -d/ -f5 | cut -d. -f1`
  if [ -z "${LATENCY}" ]; then
          LATENCY=-1
  fi
  echo $LATENCY
  return $LATENCY
}

case "$MY_ISD" in

        "67")
                # North America
                echo -n "NYC,TYO,CYBL,"
                scion_ping $TYO_EDGE_IP "$MY_AS $CYBL_NYC_CORE $CYBL_TYO_CORE $TYO_EDGE_AS"
                echo -n "NYC,TYO,INTC,"
                scion_ping $TYO_EDGE_IP "$MY_AS $INTC_NYC_CORE $INTC_TYO_CORE $TYO_EDGE_AS"
                echo -n "NYC,TYO,BEST,"
                scion_ping_best $TYO_EDGE_IP
                echo -n "NYC,LON,CYBL,"
                scion_ping $LON_EDGE_IP "$MY_AS $CYBL_NYC_CORE $CYBL_LON_CORE $LON_EDGE_AS"
                echo -n "NYC,LON,INTC,"
                scion_ping $LON_EDGE_IP "$MY_AS $INTC_NYC_CORE $INTC_LON_CORE $LON_EDGE_AS"
                echo -n "NYC,LON,BEST,"
                scion_ping_best $LON_EDGE_IP
                ;;
        "66")
                # Asia
                echo -n "TYO,NYC,CYBL,"
                scion_ping $NYC_EDGE_IP "$MY_AS $CYBL_TYO_CORE $CYBL_NYC_CORE $NYC_EDGE_AS"
                echo -n "TYO,NYC,INTC,"
                scion_ping $NYC_EDGE_IP "$MY_AS $INTC_TYO_CORE $INTC_NYC_CORE $NYC_EDGE_AS"
                echo -n "TYO,NYC,BEST,"
                scion_ping_best $NYC_EDGE_IP
                echo -n "TYO,LON,CYBL,"
                scion_ping $LON_EDGE_IP "$MY_AS $CYBL_TYO_CORE $CYBL_LON_CORE $LON_EDGE_AS"
                echo -n "TYO,LON,INTC,"
                scion_ping $LON_EDGE_IP "$MY_AS $INTC_TYO_CORE $INTC_LON_CORE $LON_EDGE_AS"
                echo -n "TYO,LON,BEST,"
                scion_ping_best $LON_EDGE_IP
                ;;

        "65")
                # Europe
                echo -n "LON,NYC,CYBL,"
                scion_ping $NYC_EDGE_IP "$MY_AS $CYBL_LON_CORE $CYBL_NYC_CORE $NYC_EDGE_AS"
                echo -n "LON,NYC,INTC,"
                scion_ping $NYC_EDGE_IP "$MY_AS $INTC_LON_CORE $INTC_NYC_CORE $NYC_EDGE_AS"
                echo -n "LON,NYC,BEST,"
                scion_ping_best $NYC_EDGE_IP
                echo -n "LON,TYO,CYBL,"
                scion_ping $TYO_EDGE_IP "$MY_AS $CYBL_LON_CORE $CYBL_TYO_CORE $TYO_EDGE_AS"
                echo -n "LON,TYO,INTC,"
                scion_ping $TYO_EDGE_IP "$MY_AS $INTC_LON_CORE $INTC_TYO_CORE $TYO_EDGE_AS"
                echo -n "LON,TYO,BEST,"
                scion_ping_best $TYO_EDGE_IP
                ;;

esac
