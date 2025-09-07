#!/usr/bin/env python3
"""
Log Monitor - Real-time ModSecurity log file monitoring
Monitors log file changes and automatically updates attack map database
"""

import os
import time
import threading
from pathlib import Path
from datetime import datetime
import logging

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

try:
    from waf_log_parser import WAFLogParser
    from attack_map_parser import AttackMapParser
except ImportError:
    WAFLogParser = None
    AttackMapParser = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogFileHandler(FileSystemEventHandler):
    """Handler for log file changes"""
    
    def __init__(self, log_file_path, callback):
        super().__init__()
        self.log_file_path = log_file_path
        self.callback = callback
        self.last_position = 0
        
        # Get initial file size
        if os.path.exists(log_file_path):
            self.last_position = os.path.getsize(log_file_path)
    
    def on_modified(self, event):
        """Called when log file is modified"""
        if event.is_directory:
            return
            
        if event.src_path == self.log_file_path:
            logger.info(f"Log file modified: {event.src_path}")
            self.process_new_entries()
    
    def process_new_entries(self):
        """Process new log entries since last check"""
        try:
            if not os.path.exists(self.log_file_path):
                return
                
            current_size = os.path.getsize(self.log_file_path)
            
            # Check if file was truncated (log rotation)
            if current_size < self.last_position:
                logger.info("Log file was rotated, resetting position")
                self.last_position = 0
            
            # Read new content
            if current_size > self.last_position:
                with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.last_position)
                    new_content = f.read()
                    
                if new_content.strip():
                    logger.info(f"Processing {len(new_content)} new bytes from log")
                    self.callback(new_content)
                    
                self.last_position = current_size
                
        except Exception as e:
            logger.error(f"Error processing new log entries: {e}")

class LogMonitor:
    """Real-time log file monitor"""
    
    def __init__(self):
        self.observer = None
        self.parser = None
        self.monitoring = False
        self.log_files = [
            '/var/log/nginx/modsec_audit.log',
            '/var/log/modsec_audit.log',
            '/etc/nginx/logs/modsec_audit.log'
        ]
        
        # Initialize parser
        if WAFLogParser:
            self.parser = WAFLogParser()
        elif AttackMapParser:
            self.parser = AttackMapParser()
        else:
            logger.error("No parser available")
    
    def find_log_file(self):
        """Find the first existing log file"""
        for log_file in self.log_files:
            if os.path.exists(log_file):
                logger.info(f"Found log file: {log_file}")
                return log_file
        return None
    
    def process_new_log_content(self, content):
        """Process new log content with error handling"""
        try:
            if not self.parser:
                logger.error("No parser available")
                return
                
            lines = content.strip().split('\n')
            processed_count = 0
            error_count = 0
            
            for line in lines:
                if line.strip():
                    try:
                        if hasattr(self.parser, 'parse_modsec_log_line'):
                            attack_data = self.parser.parse_modsec_log_line(line)
                            if attack_data:
                                # Save to database with retry mechanism
                                if hasattr(self.parser, 'save_attacks_to_db'):
                                    retry_count = 0
                                    max_retries = 3
                                    
                                    while retry_count < max_retries:
                                        try:
                                            self.parser.save_attacks_to_db([attack_data])
                                            processed_count += 1
                                            break
                                        except Exception as db_error:
                                            retry_count += 1
                                            if retry_count >= max_retries:
                                                logger.error(f"Failed to save attack data after {max_retries} retries: {db_error}")
                                                error_count += 1
                                            else:
                                                logger.warning(f"Database save failed, retrying ({retry_count}/{max_retries}): {db_error}")
                                                time.sleep(0.1 * retry_count)  # Exponential backoff
                    except Exception as e:
                        error_count += 1
                        logger.debug(f"Error parsing line: {e}")
                        continue
            
            if processed_count > 0:
                logger.info(f"Processed {processed_count} new attack records")
            if error_count > 0:
                logger.warning(f"Encountered {error_count} errors while processing")
                
        except Exception as e:
            logger.error(f"Critical error processing log content: {e}")
            # Try to reinitialize parser as fallback
            try:
                self._reinitialize_parser()
            except Exception as reinit_error:
                logger.error(f"Failed to reinitialize parser: {reinit_error}")
    
    def start_monitoring(self):
        """Start monitoring log files"""
        if not WATCHDOG_AVAILABLE:
            logger.error("Watchdog not available, cannot start file monitoring")
            return False
            
        if self.monitoring:
            logger.info("Already monitoring")
            return True
            
        log_file = self.find_log_file()
        if not log_file:
            logger.error("No log file found to monitor")
            return False
            
        try:
            # Create observer
            self.observer = Observer()
            
            # Create handler
            handler = LogFileHandler(log_file, self.process_new_log_content)
            
            # Watch the directory containing the log file
            log_dir = os.path.dirname(log_file)
            self.observer.schedule(handler, log_dir, recursive=False)
            
            # Start observer
            self.observer.start()
            self.monitoring = True
            
            logger.info(f"Started monitoring {log_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting monitor: {e}")
            return False
    
    def _reinitialize_parser(self):
        """Reinitialize parser as fallback mechanism"""
        try:
            from waf_log_parser import WAFLogParser
            self.parser = WAFLogParser()
            logger.info("Parser reinitialized successfully")
        except Exception as e:
            logger.error(f"Failed to reinitialize parser: {e}")
            raise
    
    def stop_monitoring(self):
        """Stop monitoring log files"""
        if self.observer and self.monitoring:
            self.observer.stop()
            self.observer.join()
            self.monitoring = False
            logger.info("Stopped log monitoring")
    
    def is_monitoring(self):
        """Check if currently monitoring"""
        return self.monitoring

# Global monitor instance
_monitor_instance = None

def get_monitor():
    """Get global monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = LogMonitor()
    return _monitor_instance

def start_background_monitoring():
    """Start background monitoring in a separate thread"""
    monitor = get_monitor()
    if monitor.start_monitoring():
        logger.info("Background log monitoring started")
        return True
    return False

def stop_background_monitoring():
    """Stop background monitoring"""
    monitor = get_monitor()
    monitor.stop_monitoring()
    logger.info("Background log monitoring stopped")

def is_monitoring():
    """Check if monitoring is active"""
    monitor = get_monitor()
    return monitor.is_monitoring()

if __name__ == '__main__':
    # Test monitoring
    print("Starting log monitor test...")
    
    if not WATCHDOG_AVAILABLE:
        print("Error: watchdog package not available")
        print("Install with: pip install watchdog")
        exit(1)
    
    monitor = LogMonitor()
    
    try:
        if monitor.start_monitoring():
            print("Monitoring started. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        else:
            print("Failed to start monitoring")
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop_monitoring()
        print("Monitor stopped.")