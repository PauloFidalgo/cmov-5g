```
#!/bin/bash

# Check input
if [[ $# -ne 1 || ! "$1" =~ ^[1-6]$ ]]; then
  echo "Usage: $0 <test_number: 1-6>"
  exit 1
fi

test_number=$1

show_progress() {
  local duration=$1
  local interval=1
  local elapsed=0

  while [ $elapsed -le $duration ]; do
    # Calculate percentage done
    percent=$(( elapsed * 100 / duration ))
    # Calculate bar length (20 chars width)
    bar_length=$(( percent / 5 ))
    bar=$(printf "%-${bar_length}s" "#" | tr ' ' '#')
    spaces=$(printf "%-$((20 - bar_length))s" " ")

    # Print progress bar
    printf "\rProgress: [%s%s] %3d%% (%ds left)" "$bar" "$spaces" $percent "$((duration - elapsed))"

    sleep $interval
    ((elapsed++))
  done
  echo -e "\rProgress: [####################] 100% (0s left)"
}

echo "Running test scenario $test_number..."

IP_UE1=10.0.0.4
IP_UE2=10.0.0.5
case $test_number in
  1)
    echo "[UE1] ping 192.168.70.135 -I $IP_UE1"
    echo "[UE2] ping 192.168.70.135 -I $IP_UE2"
    ping 192.168.70.135 -I $IP_UE1 > /dev/null &
    # ping 192.168.70.135 -I $IP_UE2
    (show_progress 100) & 
    ./flexric/build/examples/xApp/c/monitor/xapp_kpm_moni 100 > ue2_dl_rtt_b80.txt
    ;;
  2)
    echo "[CORE] sudo docker exec -i oai-ext-dn ping $IP_UE1"
    echo "[CORE] sudo docker exec -i oai-ext-dn ping $IP_UE2"
    sudo docker exec -i oai-ext-dn ping -c 100 $IP_UE1  > /dev/null &
    sudo docker exec -i oai-ext-dn ping -c 100 $IP_UE2  > /dev/null &
    (show_progress 100) & 
    ./flexric/build/examples/xApp/c/monitor/xapp_kpm_moni 100 > ue2_ul_rtt_b80_2.txt
    ;;
  3)
    echo "[CORE] DL UDP to UE1 and UE2"
    sudo docker exec -i oai-ext-dn iperf -u -t 100 -i 1 -fk -B 192.168.70.135 -b 10M -c $IP_UE1 > /dev/null &
    sudo docker exec -i oai-ext-dn iperf -u -t 100 -i 1 -fk -B 192.168.70.135 -b 10M -c $IP_UE2 > /dev/null &
    echo "[UE1] UDP server on $IP_UE1"
    iperf -s -u -i 1 -B $IP_UE1 > /dev/null &
    echo "[UE2] UDP server on $IP_UE2"
    # iperf -s -u -i 1 -B $IP_UE2
    (show_progress 100) & 
    ./flexric/build/examples/xApp/c/monitor/xapp_kpm_moni 100 > ue2_dl_udp_b80.txt
    ;;
  4)
    echo "[CORE] UL UDP server"
    sudo docker exec -i oai-ext-dn iperf -u -s -i 1 -fk -B 192.168.70.135 > /dev/null &
    echo "[UE1] UL UDP client from $IP_UE1"
    iperf -u -t 100 -i 1 -B $IP_UE1 -b 10M -c 192.168.70.135 > /dev/null &
    echo "[UE2] UL UDP client from $IP_UE2"
    # iperf -u -t 100 -i 1 -B $IP_UE2 -b 10M -c 192.168.70.135
    (show_progress 100) & 
    ./flexric/build/examples/xApp/c/monitor/xapp_kpm_moni 100 > ue2_ul_udp_b80.txt
    ;;
  5)
    echo "[CORE] DL TCP to UE1 and UE2"
    sudo docker exec -i oai-ext-dn iperf -t 100 -i 1 -fk -B 192.168.70.135 -c $IP_UE1 > /dev/null &
    sudo docker exec -i oai-ext-dn iperf -t 100 -i 1 -fk -B 192.168.70.135 -c $IP_UE2 > /dev/null &
    echo "[UE1] TCP server on $IP_UE1"
    iperf -s -i 1 -B $IP_UE1 > /dev/null &
    echo "[UE2] TCP server on $IP_UE2"
    # iperf -s -i 1 -B $IP_UE2
    (show_progress 100) & 
    ./flexric/build/examples/xApp/c/monitor/xapp_kpm_moni 100 > ue2_dl_tcp_b80.txt
    ;;
  6)
    echo "[CORE] UL TCP server"
    sudo docker exec -i oai-ext-dn iperf -s -i 1 -fk -B 192.168.70.135 > /dev/null &
    echo "[UE1] UL TCP client from $IP_UE1"
    iperf -t 100 -i 1 -B $IP_UE1 -c 192.168.70.135 > /dev/null &
    echo "[UE2] UL TCP client from $IP_UE2"
    # iperf -t 100 -i 1 -B $IP_UE2 -c 192.168.70.135
    (show_progress 100) & 
    ./flexric/build/examples/xApp/c/monitor/xapp_kpm_moni 100 > ue2_ul_tcp_b80.txt
    ;;
esac

echo "Completed test scenario $test_number"
```