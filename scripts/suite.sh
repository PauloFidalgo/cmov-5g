#!/bin/bash

bandwidth=""
UE1_IP=$(ip -4 addr show $UE_IF 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
UE2_IP=""
AUTO_CONTINUE=false


usage() {
    echo "Usage: $0 -b <bandwidth> [-2 <UE2_IP>]"
    echo "  -b <bandwidth>        Bandwidth in MHz (required, e.g., 20 or 80)"
    echo "  -2 <UE2_IP>           Optional second UE IP"
    echo "  -y                    Run all experiments without prompting"
    exit 1
}

experiment_num=1

prompt_continue() {
  if $AUTO_CONTINUE; then
    echo "Running experiment ($experiment_num)"
    ((experiment_num++))
    return
  fi

  read -p "Run experiment ($experiment_num)? (y/n) " choice
  case "$choice" in
    y|Y )
        ((experiment_num++))
        return
        ;;
    * )
        echo "Aborting."
        exit 0
        ;;
  esac
}


# Parse options
while getopts ":b:2:" opt; do
    case $opt in
        b) bandwidth=$OPTARG ;;
        2) UE2_IP=$OPTARG ;;
        y) AUTO_CONTINUE=true ;;
        \?) echo "Invalid option -$OPTARG" >&2; usage ;;
        :) echo "Option -$OPTARG requires an argument." >&2; usage ;;
    esac
done

if [[ -z "$bandwidth" ]]; then
    echo "Error: Missing required argument bandwidth."
    usage
fi

if [[ "$bandwidth" != "20" && "$bandwidth" != "80" ]]; then
    echo "Error: -b bandwidth must be 20 or 80."
    usage
fi

echo "Running experiments with bandwidth: $bandwidth MHz"

if [[ -n "$UE2_IP" ]]; then
    echo "Using 2 UEs: UE1 IP is $UE1_IP, UE2 IP is $UE2_IP"
else
    echo "Using 1 UE: UE1 IP is $UE1_IP"
fi

case "$bandwidth" in
    "20")
    echo "Running experiments for 20 MHz"
    if [[ -n "$UE2_IP" ]]; then
        prompt_continue
        ./experiment.sh -l dl -t rtt -b 20 -d 100 -2 $UE2_IP
        prompt_continue
        ./experiment.sh -l ul -t rtt -b 20 -d 100 -2 $UE2_IP
        prompt_continue
        ./experiment.sh -l dl -t udp -b 20 -d 100 -2 $UE2_IP
        prompt_continue
        ./experiment.sh -l ul -t udp -b 20 -d 100 -2 $UE2_IP
        prompt_continue
        ./experiment.sh -l dl -t tcp -b 20 -d 100 -2 $UE2_IP
        prompt_continue
        ./experiment.sh -l ul -t tcp -b 20 -d 100 -2 $UE2_IP
    else
        prompt_continue
        ./experiment.sh -l dl -t rtt -b 20 -d 100
        prompt_continue
        ./experiment.sh -l ul -t rtt -b 20 -d 100
        prompt_continue
        ./experiment.sh -l dl -t udp -b 20 -d 100
        prompt_continue
        ./experiment.sh -l ul -t udp -b 20 -d 100
        prompt_continue
        ./experiment.sh -l dl -t tcp -b 20 -d 100
        prompt_continue
        ./experiment.sh -l ul -t tcp -b 20 -d 100 
    fi
    ;;

    "80")
    echo "Running experiments for 80 MHz"
    if [[ -n "$UE2_IP" ]]; then
        prompt_continue
        ./experiment.sh -l dl -t rtt -b 80 -d 100 -2 $UE2_IP
        prompt_continue
        ./experiment.sh -l ul -t rtt -b 80 -d 100 -2 $UE2_IP
        prompt_continue
        ./experiment.sh -l dl -t udp -b 80 -d 100 -2 $UE2_IP
        prompt_continue
        ./experiment.sh -l ul -t udp -b 80 -d 100 -2 $UE2_IP
        prompt_continue
        ./experiment.sh -l dl -t tcp -b 80 -d 100 -2 $UE2_IP
        prompt_continue
        ./experiment.sh -l ul -t tcp -b 80 -d 100 -2 $UE2_IP
    else
        prompt_continue
        ./experiment.sh -l dl -t rtt -b 80 -d 100
        prompt_continue
        ./experiment.sh -l ul -t rtt -b 80 -d 100
        prompt_continue
        ./experiment.sh -l dl -t udp -b 80 -d 100
        prompt_continue
        ./experiment.sh -l ul -t udp -b 80 -d 100
        prompt_continue
        ./experiment.sh -l dl -t tcp -b 80 -d 100
        prompt_continue
        ./experiment.sh -l ul -t tcp -b 80 -d 100
    fi
    ;;
esac

echo "All experiments completed."