#!/bin/bash

# Check input
if [[ $# -ne 1 || ! "$1" =~ ^[1-6]$ ]]; then
  echo "Usage: $0 <test_number: 1-6>"
  exit 1
fi

test_number=$1

echo "Running test scenario $test_number..."

IP_UE2=10.0.0.3
case $test_number in
  1)
    echo "[UE2] ping 192.168.70.135 -I $IP_UE2"
    ping 192.168.70.135 -I $IP_UE2
    ;;
  2)
    echo "Nothing needs to run in UE2 here!"
    ;;
  3)
    echo "[UE2] UDP server on $IP_UE2"
    iperf -s -u -i 1 -B $IP_UE2
    ;;
  4)
    echo "[UE2] UL UDP client from $IP_UE2"
    iperf -u -t 100 -i 1 -B $IP_UE2 -b 10M -c 192.168.70.135
    ;;
  5)
    echo "[UE2] TCP server on $IP_UE2"
    iperf -s -i 1 -B $IP_UE2
    ;;
  6)
    echo "[UE2] UL TCP client from $IP_UE2"
    iperf -t 100 -i 1 -B $IP_UE2 -c 192.168.70.135
    ;;
esac
