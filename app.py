#!/usr/bin/env python3
"""
5G Core Network Metrics Visualization Tool

This application allows users to upload 5G network log files and visualize 
the extracted metrics through interactive plots in a web interface.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import subprocess
import tempfile
import os
import io
import time
import threading
from typing import Dict, List, Optional
import re
from pathlib import Path

# Configure the page
st.set_page_config(
    page_title="5G Network Metrics Analyzer",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

def parse_filename_description(filename: str) -> str:
    """
    Parse filename and generate a human-readable description.
    
    Expected format: ue{number}_{direction}_{traffic_type}_b{bandwidth}
    Examples:
    - ue_dl_rtt_b20 -> 1 UE, Downlink, Ping (RTT), 20MHz
    - ue2_up_tcp_b30 -> 2 UE, Uplink, TCP, 30MHz
    - up2_up_udp_b80 -> 2 UE, Uplink, UDP, 80MHz
    
    Args:
        filename: The filename to parse
        
    Returns:
        Human-readable description string
    """
    # Remove file extension
    name = Path(filename).stem
    
    try:
        # Parse the filename pattern
        pattern = r'u[pe](\d*)_([du][pl])_([a-z]+)_b(\d+)'
        match = re.match(pattern, name.lower())
        
        if not match:
            return f"File: {filename}"
        
        ue_count_str, direction, traffic_type, bandwidth = match.groups()
        
        # Determine UE count (default to 1 if not specified)
        ue_count = int(ue_count_str) if ue_count_str else 1
        
        # Parse direction
        direction_map = {
            'dl': 'Downlink (Server → UE)',
            'up': 'Uplink (UE → Server)',
            'ul': 'Uplink (UE → Server)'
        }
        direction_desc = direction_map.get(direction, direction.upper())
        
        # Parse traffic type
        traffic_map = {
            'rtt': 'Ping (RTT)',
            'tcp': 'TCP',
            'udp': 'UDP'
        }
        traffic_desc = traffic_map.get(traffic_type, traffic_type.upper())
        
        # Format bandwidth
        bandwidth_desc = f"{bandwidth}MHz"
        
        # Create description
        ue_desc = f"{ue_count} UE{'s' if ue_count > 1 else ''}"
        
        return f"📊 {ue_desc} | {direction_desc} | {traffic_desc} | {bandwidth_desc}"
        
    except Exception:
        # Fallback to filename if parsing fails
        return f"File: {filename}"

def parse_filename_description(filename: str) -> str:
    """
    Parse filename and generate a human-readable description.
    
    Expected format: ue{number}_{direction}_{traffic_type}_b{bandwidth}
    Examples:
    - ue_dl_rtt_b20 -> 1 UE, Downlink, Ping (RTT), 20MHz
    - ue2_up_tcp_b30 -> 2 UE, Uplink, TCP, 30MHz
    - up2_up_udp_b80 -> 2 UE, Uplink, UDP, 80MHz
    
    Args:
        filename: The filename to parse
        
    Returns:
        Human-readable description string
    """
    # Remove file extension
    name = Path(filename).stem
    
    try:
        # Parse the filename pattern
        pattern = r'u[pe](\d*)_([du][pl])_([a-z]+)_b(\d+)'
        match = re.match(pattern, name.lower())
        
        if not match:
            return f"File: {filename}"
        
        ue_count_str, direction, traffic_type, bandwidth = match.groups()
        
        # Determine UE count (default to 1 if not specified)
        ue_count = int(ue_count_str) if ue_count_str else 1
        
        # Parse direction
        direction_map = {
            'dl': 'Downlink (Server → UE)',
            'up': 'Uplink (UE → Server)',
            'ul': 'Uplink (UE → Server)'
        }
        direction_desc = direction_map.get(direction, direction.upper())
        
        # Parse traffic type
        traffic_map = {
            'rtt': 'Ping (RTT)',
            'tcp': 'TCP',
            'udp': 'UDP'
        }
        traffic_desc = traffic_map.get(traffic_type, traffic_type.upper())
        
        # Format bandwidth
        bandwidth_desc = f"{bandwidth}MHz"
        
        # Create description
        ue_desc = f"{ue_count} UE{'s' if ue_count > 1 else ''}"
        
        return f"📊 {ue_desc} | {direction_desc} | {traffic_desc} | {bandwidth_desc}"
        
    except Exception:
        # Fallback to filename if parsing fails
        return f"File: {filename}"

class RealTimeMetricsProcessor:
    """Processes real-time 5G network log files and monitors for updates."""
    
    def __init__(self, perl_script_path: str = "scripts/script.pl"):
        self.perl_script_path = perl_script_path
        self.last_position = 0
        self.monitoring = False
        
    def read_new_data(self, file_path: str) -> Optional[str]:
        """
        Read new data from file since last position.
        
        Args:
            file_path: Path to the log file being monitored
            
        Returns:
            New content since last read or None if no new data
        """
        try:
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r') as f:
                f.seek(self.last_position)
                new_content = f.read()
                self.last_position = f.tell()
                
            return new_content if new_content.strip() else None
            
        except Exception as e:
            st.error(f"Error reading file {file_path}: {str(e)}")
            return None
    
    def process_incremental_data(self, new_content: str, existing_df: Optional[pd.DataFrame] = None) -> Optional[pd.DataFrame]:
        """
        Process new content and merge with existing DataFrame.
        
        Args:
            new_content: New log content to process
            existing_df: Existing DataFrame to append to
            
        Returns:
            Updated DataFrame with new data
        """
        try:
            # Create temporary file with new content
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                temp_file.write(new_content)
                temp_file_path = temp_file.name
            
            # Run the Perl script on new content
            try:
                result = subprocess.run(
                    ['perl', self.perl_script_path],
                    stdin=open(temp_file_path, 'r'),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and result.stdout:
                    # Parse CSV output
                    csv_data = io.StringIO(result.stdout)
                    new_df = pd.read_csv(csv_data)
                    
                    if existing_df is not None and not existing_df.empty:
                        # Merge with existing data, avoiding duplicates
                        max_id = existing_df['id'].max() if 'id' in existing_df.columns else 0
                        new_df = new_df[new_df['id'] > max_id]
                        
                        if not new_df.empty:
                            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                            return combined_df
                        else:
                            return existing_df
                    else:
                        return new_df
                        
                # Clean up temporary file
                os.unlink(temp_file_path)
                return existing_df
                
            except Exception as e:
                st.error(f"Error processing incremental data: {str(e)}")
                return existing_df
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            st.error(f"Error creating temporary file: {str(e)}")
            return existing_df

    def reset_position(self):
        """Reset file reading position to start."""
        self.last_position = 0

class NetworkMetricsProcessor:
    """Processes 5G network log files and extracts metrics using the Perl script."""
    
    def __init__(self, perl_script_path: str = "scripts/script.pl"):
        self.perl_script_path = perl_script_path
        
    def process_file(self, file_content: str, filename: str) -> Optional[pd.DataFrame]:
        """
        Process a network log file and return extracted metrics as DataFrame.
        
        Args:
            file_content: Content of the uploaded file
            filename: Name of the uploaded file
            
        Returns:
            DataFrame with extracted metrics or None if processing fails
        """
        try:
            # Create temporary file with the content
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # Run the Perl script
            try:
                result = subprocess.run(
                    ['perl', self.perl_script_path],
                    stdin=open(temp_file_path, 'r'),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and result.stdout:
                    # Parse CSV output
                    csv_data = io.StringIO(result.stdout)
                    df = pd.read_csv(csv_data)
                    
                    # Add filename for identification
                    df['source_file'] = filename
                    
                    # Clean up temporary file
                    os.unlink(temp_file_path)
                    
                    return df
                else:
                    st.error(f"Error processing {filename}: {result.stderr}")
                    return None
                    
            except subprocess.TimeoutExpired:
                st.error(f"Processing timeout for {filename}")
                return None
            except Exception as e:
                st.error(f"Error running Perl script for {filename}: {str(e)}")
                return None
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            st.error(f"Error creating temporary file for {filename}: {str(e)}")
            return None

class MetricsVisualizer:
    """Creates interactive visualizations for 5G network metrics."""
    
    @staticmethod
    def create_throughput_plot(df: pd.DataFrame, title: str) -> go.Figure:
        """Create throughput visualization (DL and UL)."""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Downlink Throughput', 'Uplink Throughput'),
            vertical_spacing=0.1
        )
        
        # Downlink throughput
        fig.add_trace(
            go.Scatter(
                x=df['id'],
                y=df['UEThpDl'],
                mode='lines+markers',
                name='DL Throughput',
                line=dict(color='blue', width=2),
                marker=dict(size=6)
            ),
            row=1, col=1
        )
        
        # Uplink throughput
        fig.add_trace(
            go.Scatter(
                x=df['id'],
                y=df['UEThpUl'],
                mode='lines+markers',
                name='UL Throughput',
                line=dict(color='red', width=2),
                marker=dict(size=6)
            ),
            row=2, col=1
        )
        
        fig.update_xaxes(title_text="Measurement ID", row=2, col=1)
        fig.update_yaxes(title_text="Throughput (kbps)", row=1, col=1)
        fig.update_yaxes(title_text="Throughput (kbps)", row=2, col=1)
        fig.update_layout(
            title=f"{title} - Throughput Metrics",
            height=600,
            showlegend=True
        )
        
        return fig
    
    @staticmethod
    def create_volume_plot(df: pd.DataFrame, title: str) -> go.Figure:
        """Create data volume visualization."""
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=df['id'],
                y=df['PdcpSduVolumeDL'],
                mode='lines+markers',
                name='DL Volume',
                line=dict(color='blue', width=2),
                marker=dict(size=6)
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['id'],
                y=df['PdcpSduVolumeUL'],
                mode='lines+markers',
                name='UL Volume',
                line=dict(color='red', width=2),
                marker=dict(size=6)
            )
        )
        
        fig.update_layout(
            title=f"{title} - Data Volume (KB)",
            xaxis_title="Measurement ID",
            yaxis_title="Volume (KB)",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_delay_plot(df: pd.DataFrame, title: str) -> go.Figure:
        """Create RLC delay visualization."""
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=df['id'],
                y=df['RlcSduDelayDl'],
                mode='lines+markers',
                name='RLC SDU Delay DL',
                line=dict(color='orange', width=2),
                marker=dict(size=6)
            )
        )
        
        fig.update_layout(
            title=f"{title} - RLC SDU Delay",
            xaxis_title="Measurement ID",
            yaxis_title="Delay (μs)",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_prb_plot(df: pd.DataFrame, title: str) -> go.Figure:
        """Create PRB (Physical Resource Block) utilization visualization."""
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=df['id'],
                y=df['PrbTotDl'],
                mode='lines+markers',
                name='PRB Total DL',
                line=dict(color='green', width=2),
                marker=dict(size=6)
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['id'],
                y=df['PrbTotUl'],
                mode='lines+markers',
                name='PRB Total UL',
                line=dict(color='purple', width=2),
                marker=dict(size=6)
            )
        )
        
        fig.update_layout(
            title=f"{title} - Physical Resource Blocks",
            xaxis_title="Measurement ID",
            yaxis_title="PRBs",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_latency_plot(df: pd.DataFrame, title: str) -> go.Figure:
        """Create latency visualization."""
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=df['id'],
                y=df['latency'],
                mode='lines+markers',
                name='KMP Indication Latency',
                line=dict(color='darkred', width=2),
                marker=dict(size=6)
            )
        )
        
        fig.update_layout(
            title=f"{title} - KMP Indication Latency",
            xaxis_title="Measurement ID",
            yaxis_title="Latency (μs)",
            height=400
        )
        
        return fig

def real_time_tab():
    """Real-time monitoring tab functionality."""
    st.header("📈 Real-Time Network Monitoring")
    st.markdown("Monitor live 5G network metrics from a continuously updated log file")
    
    # Initialize processors
    rt_processor = RealTimeMetricsProcessor()
    visualizer = MetricsVisualizer()
    
    # File selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        log_file_path = st.text_input(
            "Log File Path",
            placeholder="/path/to/your/realtime.log",
            help="Enter the path to the log file that's being continuously updated"
        )
        
        # Show filename description if path is provided
        if log_file_path:
            filename = Path(log_file_path).name
            description = parse_filename_description(filename)
            st.markdown(f"**Configuration:** {description}")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        monitoring_enabled = st.checkbox("Enable Monitoring", value=False)
    
    # Initialize session state for real-time data
    if 'rt_data' not in st.session_state:
        st.session_state.rt_data = pd.DataFrame()
    if 'rt_last_update' not in st.session_state:
        st.session_state.rt_last_update = None
    if 'rt_monitoring' not in st.session_state:
        st.session_state.rt_monitoring = False
    
    # Control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Reset Data", disabled=not log_file_path):
            st.session_state.rt_data = pd.DataFrame()
            rt_processor.reset_position()
            st.session_state.rt_last_update = None
            st.success("Data reset successfully!")
    
    with col2:
        refresh_interval = st.selectbox(
            "Refresh Interval",
            options=[1, 2, 5, 10],
            index=1,
            format_func=lambda x: f"{x} seconds"
        )
    
    with col3:
        st.markdown(f"**Status:** {'🟢 Monitoring' if monitoring_enabled and log_file_path else '🔴 Stopped'}")
    
    # Auto-refresh logic
    if monitoring_enabled and log_file_path:
        # Create placeholder for auto-refresh
        placeholder = st.empty()
        
        with placeholder.container():
            # Check for new data
            new_content = rt_processor.read_new_data(log_file_path)
            
            if new_content:
                # Process new data
                updated_df = rt_processor.process_incremental_data(new_content, st.session_state.rt_data)
                if updated_df is not None:
                    st.session_state.rt_data = updated_df
                    st.session_state.rt_last_update = time.time()
                    
            # Display current data if available
            if not st.session_state.rt_data.empty:
                display_real_time_metrics(st.session_state.rt_data, visualizer)
            else:
                st.info("📡 Waiting for data... Make sure the log file path is correct and data is being written to it.")
                
        # Auto-refresh the page
        time.sleep(refresh_interval)
        st.rerun()
    
    elif log_file_path and not monitoring_enabled:
        # Manual mode - show current data without auto-refresh
        if not st.session_state.rt_data.empty:
            display_real_time_metrics(st.session_state.rt_data, visualizer)
        else:
            st.info("📡 Click 'Enable Monitoring' to start real-time data collection")
    
    else:
        st.info("📝 Please enter a log file path to begin monitoring")

def display_real_time_metrics(df: pd.DataFrame, visualizer):
    """Display real-time metrics visualization."""
    # Show current statistics
    st.subheader("📊 Live Metrics Dashboard")
    
    # Last update info
    if st.session_state.rt_last_update:
        last_update_str = time.strftime("%H:%M:%S", time.localtime(st.session_state.rt_last_update))
        st.caption(f"Last updated: {last_update_str} | Total measurements: {len(df)}")
    
    # Statistics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Measurements", len(df))
    with col2:
        latest_dl = df['UEThpDl'].iloc[-1] if not df.empty else 0
        avg_dl = df['UEThpDl'].mean() if not df.empty else 0
        delta_dl = latest_dl - avg_dl
        st.metric("Current DL Throughput", f"{latest_dl:.2f} kbps", delta=f"{delta_dl:.2f}")
    with col3:
        latest_ul = df['UEThpUl'].iloc[-1] if not df.empty else 0
        avg_ul = df['UEThpUl'].mean() if not df.empty else 0
        delta_ul = latest_ul - avg_ul
        st.metric("Current UL Throughput", f"{latest_ul:.2f} kbps", delta=f"{delta_ul:.2f}")
    with col4:
        latest_latency = df['latency'].iloc[-1] if not df.empty else 0
        avg_latency = df['latency'].mean() if not df.empty else 0
        delta_latency = latest_latency - avg_latency
        st.metric("Current Latency", f"{latest_latency:.0f} μs", delta=f"{delta_latency:.0f}")
    
    # Show only recent data for performance (last 50 measurements)
    display_df = df.tail(50) if len(df) > 50 else df
    
    # Create visualizations
    st.plotly_chart(
        visualizer.create_throughput_plot(display_df, "Real-Time"),
        use_container_width=True
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            visualizer.create_volume_plot(display_df, "Real-Time"),
            use_container_width=True
        )
        st.plotly_chart(
            visualizer.create_prb_plot(display_df, "Real-Time"),
            use_container_width=True
        )
    
    with col2:
        st.plotly_chart(
            visualizer.create_delay_plot(display_df, "Real-Time"),
            use_container_width=True
        )
        st.plotly_chart(
            visualizer.create_latency_plot(display_df, "Real-Time"),
            use_container_width=True
        )
    
    # Show recent raw data
    with st.expander("📋 Recent Raw Data (Last 10 measurements)"):
        recent_data = df.tail(10)
        st.dataframe(recent_data, use_container_width=True)

def non_real_time_tab():
    """Non-real-time file upload and analysis tab."""
    st.header("📁 File-Based Analysis")
    st.markdown("Upload 5G network log files to visualize performance metrics")
    
    # Initialize processor
    processor = NetworkMetricsProcessor()
    visualizer = MetricsVisualizer()
    
    # Sidebar for file uploads
    st.sidebar.header("File Upload")
    uploaded_files = st.sidebar.file_uploader(
        "Choose log files",
        type=['txt', 'log'],
        accept_multiple_files=True,
        help="Upload 5G network log files in the specified format"
    )
    
    # Initialize session state for processed data
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = {}
    
    # Process uploaded files
    if uploaded_files:
        with st.spinner("Processing uploaded files..."):
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in st.session_state.processed_data:
                    # Read file content
                    file_content = uploaded_file.read().decode('utf-8')
                    
                    # Process the file
                    df = processor.process_file(file_content, uploaded_file.name)
                    
                    if df is not None and not df.empty:
                        st.session_state.processed_data[uploaded_file.name] = df
                        st.sidebar.success(f"✅ {uploaded_file.name}")
                    else:
                        st.sidebar.error(f"❌ Failed to process {uploaded_file.name}")
    
    # Display results if we have processed data
    if st.session_state.processed_data:
        st.subheader("📊 Network Metrics Visualization")
        
        # Create tabs for each file with descriptions
        tab_names = []
        for filename in st.session_state.processed_data.keys():
            # Use just the filename for the tab (keep it short)
            tab_names.append(Path(filename).stem)
        
        tabs = st.tabs(tab_names)
        
        for i, (filename, df) in enumerate(st.session_state.processed_data.items()):
            with tabs[i]:
                # Show filename description
                description = parse_filename_description(filename)
                st.markdown(f"### {description}")
                st.caption(f"Analysis for file: `{filename}`")
                
                # Show basic statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Measurements", len(df))
                with col2:
                    st.metric("Avg DL Throughput", f"{df['UEThpDl'].mean():.2f} kbps")
                with col3:
                    st.metric("Avg UL Throughput", f"{df['UEThpUl'].mean():.2f} kbps")
                with col4:
                    st.metric("Avg RLC Delay", f"{df['RlcSduDelayDl'].mean():.2f} μs")
                
                # Create visualizations
                st.plotly_chart(
                    visualizer.create_throughput_plot(df, filename),
                    use_container_width=True
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(
                        visualizer.create_volume_plot(df, filename),
                        use_container_width=True
                    )
                    st.plotly_chart(
                        visualizer.create_prb_plot(df, filename),
                        use_container_width=True
                    )
                
                with col2:
                    st.plotly_chart(
                        visualizer.create_delay_plot(df, filename),
                        use_container_width=True
                    )
                    st.plotly_chart(
                        visualizer.create_latency_plot(df, filename),
                        use_container_width=True
                    )
                
                # Show raw data
                with st.expander("📋 View Raw Data"):
                    st.dataframe(df.drop('source_file', axis=1), use_container_width=True)
                
                # Download processed data
                csv = df.to_csv(index=False)
                st.download_button(
                    label=f"📥 Download {filename} as CSV",
                    data=csv,
                    file_name=f"{filename}_processed.csv",
                    mime="text/csv"
                )
    
    else:
        # Show instructions when no files are uploaded
        st.info("👆 Please upload one or more 5G network log files using the sidebar")
        
        with st.expander("📖 File Format Information"):
            st.markdown("""
            **Expected Log File Format:**
            
            The application expects log files with KMP indication messages containing metrics like:
            
            ```
            1 KPM ind_msg latency = 1748351985647759 [μs]
            UE ID type = gNB, amf_ue_ngap_id = 1
            ran_ue_id = 1
            DRB.PdcpSduVolumeDL = 1355748 [kb]
            DRB.PdcpSduVolumeUL = 11443 [kb]
            DRB.RlcSduDelayDl = 6611.04 [μs]
            DRB.UEThpDl = 1364419.02 [kbps]
            DRB.UEThpUl = 12819.78 [kbps]
            RRU.PrbTotDl = 2009726 [PRBs]
            RRU.PrbTotUl = 92385 [PRBs]
            ```
            
            **Supported Metrics:**
            - **Latency**: KMP indication message latency
            - **Throughput**: Downlink/Uplink user equipment throughput
            - **Volume**: PDCP SDU data volumes
            - **Delay**: RLC SDU delay
            - **PRB**: Physical Resource Block utilization
            """)

def main():
    """Main application function."""
    st.title("📡 5G Core Network Metrics Analyzer")
    st.markdown("Comprehensive 5G network performance monitoring and analysis platform")
    
    # Main tabs
    tab1, tab2 = st.tabs(["🔴 Real Time", "📁 Non Real Time"])
    
    with tab1:
        real_time_tab()
    
    with tab2:
        non_real_time_tab()

if __name__ == "__main__":
    main()