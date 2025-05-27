#!/usr/bin/env python3
"""
Real-time log simulator for testing the 5G metrics analyzer.
This script continuously appends new log entries to a file to simulate real-time data.
"""

import time
import random
import argparse
from pathlib import Path

def generate_log_entry(entry_id: int) -> str:
    """Generate a single log entry with random but realistic values."""
    
    # Generate realistic latency (around 1.7e15 microseconds base)
    base_latency = 1748351985647759
    latency = base_latency + random.randint(-1000000, 1000000)
    
    # Generate realistic throughput values
    dl_throughput = random.uniform(100000, 1500000)  # 100-1500 kbps
    ul_throughput = random.uniform(1000, 15000)      # 1-15 kbps
    
    # Generate realistic volume values (proportional to throughput)
    dl_volume = int(dl_throughput * random.uniform(0.8, 1.2))
    ul_volume = int(ul_throughput * random.uniform(0.8, 1.2))
    
    # Generate realistic delay values
    rlc_delay = random.uniform(3000, 8000)  # 3-8 ms
    
    # Generate realistic PRB values
    prb_dl = int(dl_throughput * random.uniform(0.1, 0.2))
    prb_ul = int(ul_throughput * random.uniform(0.5, 1.0))
    
    log_entry = f"""
      {entry_id} KPM ind_msg latency = {latency} [μs]
UE ID type = gNB, amf_ue_ngap_id = 1
ran_ue_id = 1
DRB.PdcpSduVolumeDL = {dl_volume} [kb]
DRB.PdcpSduVolumeUL = {ul_volume} [kb]
DRB.RlcSduDelayDl = {rlc_delay:.2f} [μs]
DRB.UEThpDl = {dl_throughput:.2f} [kbps]
DRB.UEThpUl = {ul_throughput:.2f} [kbps]
RRU.PrbTotDl = {prb_dl} [PRBs]
RRU.PrbTotUl = {prb_ul} [PRBs]
"""
    return log_entry

def main():
    parser = argparse.ArgumentParser(description="Simulate real-time 5G log data")
    parser.add_argument(
        "--output", 
        "-o", 
        default="realtime_log.txt",
        help="Output file path (default: realtime_log.txt)"
    )
    parser.add_argument(
        "--interval", 
        "-i", 
        type=float, 
        default=2.0,
        help="Interval between entries in seconds (default: 2.0)"
    )
    parser.add_argument(
        "--entries", 
        "-n", 
        type=int, 
        default=100,
        help="Number of entries to generate (default: 100, use -1 for infinite)"
    )
    
    args = parser.parse_args()
    
    output_file = Path(args.output)
    
    print(f"Starting real-time log simulation...")
    print(f"Output file: {output_file}")
    print(f"Interval: {args.interval} seconds")
    print(f"Entries: {'infinite' if args.entries == -1 else args.entries}")
    print("Press Ctrl+C to stop\n")
    
    # Write initial header if file doesn't exist
    if not output_file.exists():
        with open(output_file, 'w') as f:
            f.write("[UTIL]: Setting the config -c file to /local/etc/flexric/flexric.conf\n")
            f.write("[UTIL]: Setting path -p for the shared libraries to /local/lib/flexric/\n")
            f.write("[xAapp]: Initializing ...\n")
            f.write("[xApp]: nearRT-RIC IP Address = 127.0.0.1, PORT = 36422\n")
            f.write("Connected E2 nodes = 1\n")
            f.write("[xApp]: Successfully subscribed to RAN_FUNC_ID 2\n\n")
    
    entry_id = 1
    try:
        while args.entries == -1 or entry_id <= args.entries:
            log_entry = generate_log_entry(entry_id)
            
            with open(output_file, 'a') as f:
                f.write(log_entry)
                f.flush()  # Ensure data is written immediately
            
            print(f"Added entry {entry_id} at {time.strftime('%H:%M:%S')}")
            
            entry_id += 1
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print(f"\nStopped simulation. Generated {entry_id - 1} entries.")

if __name__ == "__main__":
    main()
