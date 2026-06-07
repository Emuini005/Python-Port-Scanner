"""
Advanced Port Scanner
Scans a range of ports on a target host and identifies open ports.
Includes comprehensive error handling, logging, and follows Python best practices.
"""

import socket
import logging
import sys
import argparse
import threading
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime
import ipaddress

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('port_scanner.log')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """Data class to store port scan results"""
    host: str
    port: int
    is_open: bool
    service: Optional[str] = None
    error_message: Optional[str] = None


class PortScanner:
    """
    A comprehensive port scanner that can scan a range of ports on a target host.
    Supports multi-threaded scanning for improved performance.
    """
    
    # Common service ports for identification
    COMMON_SERVICES = {
        20: 'FTP-DATA',
        21: 'FTP',
        22: 'SSH',
        23: 'Telnet',
        25: 'SMTP',
        53: 'DNS',
        80: 'HTTP',
        110: 'POP3',
        143: 'IMAP',
        443: 'HTTPS',
        465: 'SMTPS',
        587: 'SMTP',
        993: 'IMAPS',
        995: 'POP3S',
        3306: 'MySQL',
        3389: 'RDP',
        5432: 'PostgreSQL',
        5000: 'HTTP (Alt)',
        5900: 'VNC',
        8080: 'HTTP (Alt)',
        8443: 'HTTPS (Alt)',
        27017: 'MongoDB',
        6379: 'Redis',
    }
    
    def __init__(self, host: str, start_port: int = 1, end_port: int = 65535, 
                 timeout: float = 2.0, max_threads: int = 50):
        """
        Initialize the port scanner.
        
        Args:
            host: Target host IP address or hostname
            start_port: Starting port number (default: 1)
            end_port: Ending port number (default: 65535)
            timeout: Socket connection timeout in seconds (default: 2.0)
            max_threads: Maximum number of concurrent scanning threads (default: 50)
        
        Raises:
            ValueError: If port range is invalid or host cannot be resolved
        """
        self.host = host
        self.timeout = timeout
        self.max_threads = max_threads
        self.results: List[ScanResult] = []
        self.lock = threading.Lock()
        
        # Validate port range
        if not (1 <= start_port <= 65535):
            raise ValueError(f"Start port must be between 1 and 65535, got {start_port}")
        if not (1 <= end_port <= 65535):
            raise ValueError(f"End port must be between 1 and 65535, got {end_port}")
        if start_port > end_port:
            raise ValueError(f"Start port ({start_port}) cannot be greater than end port ({end_port})")
        
        self.start_port = start_port
        self.end_port = end_port
        
        # Resolve hostname to IP address
        try:
            self.target_ip = socket.gethostbyname(host)
            logger.info(f"Resolved host '{host}' to IP: {self.target_ip}")
        except socket.gaierror as e:
            logger.error(f"Failed to resolve hostname '{host}': {e}")
            raise ValueError(f"Cannot resolve host '{host}'") from e
    
    def _is_valid_ip(self, ip: str) -> bool:
        """
        Validate if a string is a valid IP address.
        
        Args:
            ip: String to validate
        
        Returns:
            bool: True if valid IP address, False otherwise
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _get_service_name(self, port: int) -> Optional[str]:
        """
        Get the service name for a given port.
        
        Args:
            port: Port number
        
        Returns:
            Optional[str]: Service name if known, None otherwise
        """
        if port in self.COMMON_SERVICES:
            return self.COMMON_SERVICES[port]
        
        # Try to look up service name from /etc/services (Unix-like systems)
        try:
            return socket.getservbyport(port)
        except (OSError, TypeError):
            return None
    
    def scan_port(self, port: int) -> ScanResult:
        """
        Attempt to connect to a specific port on the target host.
        
        Args:
            port: Port number to scan
        
        Returns:
            ScanResult: Result object containing scan information
        """
        try:
            # Create a TCP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Set connection timeout
            sock.settimeout(self.timeout)
            
            # Attempt to connect
            try:
                sock.connect((self.target_ip, port))
                
                # Port is open
                service = self._get_service_name(port)
                result = ScanResult(
                    host=self.host,
                    port=port,
                    is_open=True,
                    service=service
                )
                logger.debug(f"Port {port} is OPEN (Service: {service or 'Unknown'})")
                return result
            
            except socket.timeout:
                # Connection timed out - port is likely filtered
                result = ScanResult(
                    host=self.host,
                    port=port,
                    is_open=False,
                    error_message="Timeout"
                )
                logger.debug(f"Port {port} is CLOSED/FILTERED (Timeout)")
                return result
            
            except ConnectionRefusedError:
                # Connection refused - port is closed
                result = ScanResult(
                    host=self.host,
                    port=port,
                    is_open=False,
                    error_message="Connection refused"
                )
                logger.debug(f"Port {port} is CLOSED")
                return result
            
            finally:
                # Always close the socket
                sock.close()
        
        except socket.error as e:
            logger.warning(f"Socket error scanning port {port}: {e}")
            return ScanResult(
                host=self.host,
                port=port,
                is_open=False,
                error_message=f"Socket error: {str(e)}"
            )
        
        except Exception as e:
            logger.error(f"Unexpected error scanning port {port}: {e}")
            return ScanResult(
                host=self.host,
                port=port,
                is_open=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def scan_range(self) -> None:
        """
        Scan the port range using multi-threading for improved performance.
        Results are stored in self.results list.
        """
        logger.info(f"Starting port scan on {self.host} ({self.target_ip})")
        logger.info(f"Port range: {self.start_port} - {self.end_port}")
        logger.info(f"Timeout: {self.timeout}s, Max threads: {self.max_threads}")
        
        threads = []
        start_time = datetime.now()
        
        try:
            # Create and start threads for port scanning
            for port in range(self.start_port, self.end_port + 1):
                # Wait if we've reached max threads
                while threading.active_count() > self.max_threads + 1:
                    pass
                
                # Create thread for this port
                thread = threading.Thread(
                    target=self._scan_port_thread,
                    args=(port,),
                    daemon=True
                )
                thread.start()
                threads.append(thread)
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=self.timeout + 5)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Scan completed in {duration:.2f} seconds")
            logger.info(f"Total ports scanned: {self.end_port - self.start_port + 1}")
            logger.info(f"Open ports found: {len([r for r in self.results if r.is_open])}")
        
        except KeyboardInterrupt:
            logger.warning("Scan interrupted by user")
            raise
        except Exception as e:
            logger.error(f"Error during port scan: {e}")
            raise
    
    def _scan_port_thread(self, port: int) -> None:
        """
        Thread-safe wrapper for scanning a single port.
        
        Args:
            port: Port number to scan
        """
        result = self.scan_port(port)
        
        # Thread-safe append to results list
        with self.lock:
            self.results.append(result)
    
    def get_open_ports(self) -> List[ScanResult]:
        """
        Get list of all open ports found during scan.
        
        Returns:
            List[ScanResult]: List of open port results
        """
        return [result for result in self.results if result.is_open]
    
    def print_results(self, detailed: bool = False) -> None:
        """
        Print scan results in a formatted manner.
        
        Args:
            detailed: If True, show all port results; if False, show only open ports
        """
        print("\n" + "=" * 80)
        print(f"PORT SCAN RESULTS FOR: {self.host} ({self.target_ip})")
        print("=" * 80)
        
        if not self.results:
            print("No scan results available.")
            return
        
        # Filter results based on detailed flag
        results_to_show = self.results if detailed else self.get_open_ports()
        
        if not results_to_show and not detailed:
            print("No open ports found.")
        else:
            print(f"\n{'Port':<8} {'Status':<12} {'Service':<20} {'Details':<30}")
            print("-" * 80)
            
            for result in sorted(results_to_show, key=lambda x: x.port):
                status = "OPEN" if result.is_open else "CLOSED"
                service = result.service or "Unknown"
                details = result.error_message or ""
                
                print(f"{result.port:<8} {status:<12} {service:<20} {details:<30}")
        
        print("=" * 80)
        print(f"Total ports scanned: {len(self.results)}")
        print(f"Open ports: {len(self.get_open_ports())}")
        print()
    
    def export_results(self, filename: str) -> None:
        """
        Export scan results to a file.
        
        Args:
            filename: Output filename
        """
        try:
            with open(filename, 'w') as f:
                f.write(f"Port Scan Report for {self.host} ({self.target_ip})\n")
                f.write(f"Scan Time: {datetime.now().isoformat()}\n")
                f.write(f"Port Range: {self.start_port} - {self.end_port}\n")
                f.write("=" * 80 + "\n\n")
                
                open_ports = self.get_open_ports()
                f.write(f"Open Ports Found: {len(open_ports)}\n")
                f.write("-" * 80 + "\n")
                
                for result in sorted(open_ports, key=lambda x: x.port):
                    f.write(f"Port {result.port}: {result.service or 'Unknown Service'}\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"Total ports scanned: {len(self.results)}\n")
            
            logger.info(f"Results exported to {filename}")
        
        except IOError as e:
            logger.error(f"Failed to export results to {filename}: {e}")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Advanced Port Scanner - Scan ports on a target host',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s localhost
  %(prog)s 192.168.1.1 -s 1 -e 1000
  %(prog)s example.com -s 80 -e 8080 -t 1 -j 100
  %(prog)s 192.168.1.1 -s 1 -e 10000 -o results.txt
        '''
    )
    
    parser.add_argument(
        'host',
        help='Target host (IP address or hostname)'
    )
    
    parser.add_argument(
        '-s', '--start-port',
        type=int,
        default=1,
        help='Starting port number (default: 1)'
    )
    
    parser.add_argument(
        '-e', '--end-port',
        type=int,
        default=1000,
        help='Ending port number (default: 1000)'
    )
    
    parser.add_argument(
        '-t', '--timeout',
        type=float,
        default=2.0,
        help='Connection timeout in seconds (default: 2.0)'
    )
    
    parser.add_argument(
        '-j', '--threads',
        type=int,
        default=50,
        help='Maximum number of threads (default: 50)'
    )
    
    parser.add_argument(
        '-d', '--detailed',
        action='store_true',
        help='Show all ports (including closed ones)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Export results to a file'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point for the port scanner"""
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Set logging level based on verbose flag
        if args.verbose:
            logger.setLevel(logging.DEBUG)
            for handler in logger.handlers:
                handler.setLevel(logging.DEBUG)
        
        # Validate timeout
        if args.timeout <= 0:
            logger.error("Timeout must be positive")
            sys.exit(1)
        
        # Validate thread count
        if args.threads <= 0:
            logger.error("Number of threads must be positive")
            sys.exit(1)
        
        # Create port scanner instance
        scanner = PortScanner(
            host=args.host,
            start_port=args.start_port,
            end_port=args.end_port,
            timeout=args.timeout,
            max_threads=args.threads
        )
        
        # Perform scan
        scanner.scan_range()
        
        # Display results
        scanner.print_results(detailed=args.detailed)
        
        # Export results if requested
        if args.output:
            scanner.export_results(args.output)
    
    except ValueError as e:
        logger.error(f"Invalid argument: {e}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        logger.warning("\nPort scan interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
