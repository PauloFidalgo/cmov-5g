#!/bin/bash

UE_IF="oaitun_ue1"
UE1_IP=$(ip -4 addr show $UE_IF 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
CORE_IP="192.168.70.135"

set -m

cleanup() {
  echo "Cleaning up..."
  pkill -P $$
}

trap cleanup EXIT

show_progress() {
  local duration=$1
  local interval=1
  local elapsed=0
  while [ $elapsed -le $duration ]; do
    percent=$(( elapsed * 100 / duration ))
    bar_length=$(( percent / 5 ))
    bar=$(printf "%-${bar_length}s" "#" | tr ' ' '#')
    spaces=$(printf "%-$((20 - bar_length))s" " ")
    printf "\rProgress: [%s%s] %3d%% (%ds left)" "$bar" "$spaces" $percent "$((duration - elapsed))"
    sleep $interval
    ((elapsed++))
  done
  echo -e "\rProgress: [####################] 100% (0s left)     "
}


usage() {
  echo "Usage: $0 -l <dl|ul> -t <rtt|udp|tcp> [-d <duration_seconds>] -b <20|80>"
  echo "  -l link direction: dl (downlink) or ul (uplink)"
  echo "  -t traffic type: rtt, udp, or tcp"
  echo "  -d duration in seconds (optional, if omitted runs indefinitely)"
  echo "  -b bandwidth in Mbps: 20 or 80"
  echo "  -2 optional second UE IP address"
  exit 1
}

while getopts ":2:l:t:d:b:" opt; do
  case $opt in
    l) link=$OPTARG ;;
    t) traffic=$OPTARG ;;
    d) duration=$OPTARG ;;
    b) bandwidth=$OPTARG ;;
    2) UE2_IP=$OPTARG ;;
    \?) echo "Invalid option -$OPTARG" >&2; usage ;;
    :) echo "Option -$OPTARG requires an argument." >&2; usage ;;
  esac
done

if [[ -z "$link" || -z "$traffic" || -z "$bandwidth" ]]; then
  echo "Error: Missing required arguments."
  usage
fi

if [[ "$link" != "dl" && "$link" != "ul" ]]; then
  echo "Error: -l must be 'dl' or 'ul'."
  usage
fi

if [[ "$traffic" != "rtt" && "$traffic" != "udp" && "$traffic" != "tcp" ]]; then
  echo "Error: -t must be 'rtt', 'udp' or 'tcp'."
  usage
fi

if [[ -n "$duration" ]]; then
  if ! [[ "$duration" =~ ^[0-9]+$ ]]; then
    echo "Error: -d duration must be a non-negative integer."
    usage
  fi
fi

if [[ "$bandwidth" != "20" && "$bandwidth" != "80" ]]; then
  echo "Error: -b bandwidth must be 20 or 80."
  usage
fi

run_time_param=""
echo "Running test with:"
echo "UE1 IP: $UE1_IP"
[[ -n "$UE2_IP" ]] && echo "UE2 IP: $UE2_IP"
echo " Link direction: $link"
echo " Traffic type: $traffic"
if [[ -n "$duration" ]]; then
  echo " Duration: $duration seconds"
  if [[ $duration -gt 0 ]]; then
    run_time_param="-t $duration"
  else
    run_time_param="-t 0"
  fi
else
  echo " Duration: indefinite"
  run_time_param="-t 0"
fi
echo " Bandwidth: $bandwidth"

case "$traffic" in
  "rtt")
    if [[ "$link" == "dl" ]]; then
      echo "[UE] ping $CORE_IP -I $UE1_IP"
      ping $CORE_IP -I $UE1_IP > /dev/null &
      if [[ -n "$UE2_IP" ]]; then
        echo "[UE2] ping $CORE_IP -I $UE2_IP"
      fi
    else
      echo "[GNB] sudo docker exec -i oai-ext-dn ping $UE1_IP"
      sudo docker exec -i oai-ext-dn ping $UE1_IP > /dev/null &
      if [[ -n "$UE2_IP" ]]; then
        echo "[GNB] sudo docker exec -i oai-ext-dn ping $UE2_IP"
        sudo docker exec -i oai-ext-dn ping $UE2_IP > /dev/null &
      fi
    fi
    ;;

  "udp")
    if [[ "$link" == "dl" ]]; then
      echo "[GNB] sudo docker exec -i oai-ext-dn iperf -u $run_time_param -i 1 -fk -B $CORE_IP -b 10M -c $UE1_IP"
      sudo docker exec -i oai-ext-dn iperf -u $run_time_param -i 1 -fk -B $CORE_IP -b 10M -c $UE1_IP > /dev/null &
      echo "[UE] iperf -s -u -i 1 -B $UE1_IP"
      iperf -s -u -i 1 -B $UE1_IP > /dev/null &
      if [[ -n "$UE2_IP" ]]; then
        echo "[GNB] docker exec -i oai-ext-dn iperf -u $run_time_param -i 1 -fk -B $CORE_IP -b 10M -c $UE2_IP"
        sudo docker exec -i oai-ext-dn iperf -u $run_time_param -i 1 -fk -B $CORE_IP -b 10M -c $UE2_IP > /dev/null &
        echo "[UE2] iperf -s -u -i 1 -B $UE2_IP"
      fi
    else
      echo "[GNB] sudo docker exec -i oai-ext-dn iperf -u -s -i 1 -fk -B $CORE_IP"
      sudo docker exec -i oai-ext-dn iperf -u -s -i 1 -fk -B $CORE_IP > /dev/null &
      echo "[UE] iperf -u $run_time_param -i 1 -B $UE1_IP -b 10M -c $CORE_IP"
      iperf -u $run_time_param -i 1 -B $UE1_IP -b 10M -c $CORE_IP > /dev/null &
      if [[ -n "$UE2_IP" ]]; then
        echo "[UE2] iperf -u $run_time_param -i 1 -B $UE2_IP -b 10M -c $CORE_IP &"
      fi
    fi
    ;;

  "tcp")
    if [[ "$link" == "dl" ]]; then
      echo "[GNB] sudo docker exec -i oai-ext-dn iperf $run_time_param -i 1 -fk -B $CORE_IP -c $UE1_IP"
      sudo docker exec -i oai-ext-dn iperf $run_time_param -i 1 -fk -B $CORE_IP -c $UE1_IP > /dev/null &
      echo "[UE] iperf -s -i 1 -B $UE1_IP"
      iperf -s -i 1 -B $UE1_IP > /dev/null &
      if [[ -n "$UE2_IP" ]]; then
        echo "[GNB] sudo docker exec -i oai-ext-dn iperf $run_time_param -i 1 -fk -B $CORE_IP -c $UE2_IP"
        sudo docker exec -i oai-ext-dn iperf $run_time_param -i 1 -fk -B $CORE_IP -c $UE2_IP > /dev/null &
        echo "[UE] iperf -s -i 1 -B $UE2_IP"
      fi
    else
      echo "[GNB] sudo docker exec -i oai-ext-dn iperf -s -i 1 -fk -B $CORE_IP"
      sudo docker exec -i oai-ext-dn iperf -s -i 1 -fk -B $CORE_IP > /dev/null &
      echo "[UE] iperf $run_time_param -i 1 -B $UE1_IP -c $CORE_IP"
      iperf $run_time_param -i 1 -B $UE1_IP -c $CORE_IP > /dev/null &
      if [[ -n "$UE2_IP" ]]; then
        echo "[UE2] iperf $run_time_param -i 1 -B $UE2_IP -c $CORE_IP"
      fi
    fi
    ;;

  *)
    echo "Unsupported traffic type"
    exit 1
    ;;
esac

prefix="ue"
[[ -n "$UE2_IP" ]] && prefix="ue2"

if [[ -n "$duration" ]]; then
  filename="${prefix}_${link}_${traffic}_b${bandwidth}_${duration}.txt"
else
  filename="${prefix}_${link}_${traffic}_b${bandwidth}.txt"
fi

echo "Logging xApp output to $filename"

if [[ -n "$duration" ]]; then
  (show_progress $duration) &
  ../../flexric/build/examples/xApp/c/monitor/xapp_kpm_moni $duration > "$filename"
else
  ../../flexric/build/examples/xApp/c/monitor/xapp_kpm_moni > "$filename"
fi

chown $SUDO_USER:$SUDO_USER "$filename"
echo "Output written to $filename"