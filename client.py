"""
Basic Client Script - Connects to server and sends messages
Includes comprehensive error handling
"""

import socket
import logging
import sys
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Client:
    def __init__(self, host: str = 'localhost', port: int = 5000, timeout: int = 10):
        """
        Initialize client with server host, port, and timeout
        
        Args:
            host: Server IP address (default: localhost)
            port: Server port number (default: 5000)
            timeout: Connection timeout in seconds (default: 10)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
    
    def connect(self) -> bool:
        """
        Connect to the server
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create a socket object
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Set connection timeout
            self.socket.settimeout(self.timeout)
            
            # Connect to server
            logger.info(f"Attempting to connect to {self.host}:{self.port}...")
            self.socket.connect((self.host, self.port))
            
            logger.info(f"Successfully connected to server at {self.host}:{self.port}")
            return True
        
        except socket.timeout:
            logger.error(f"Connection timeout: Server at {self.host}:{self.port} did not respond within {self.timeout} seconds")
            return False
        
        except ConnectionRefusedError:
            logger.error(f"Connection refused: Server at {self.host}:{self.port} is not listening")
            return False
        
        except socket.gaierror as e:
            logger.error(f"Address error: Could not resolve hostname '{self.host}': {e}")
            return False
        
        except socket.error as e:
            logger.error(f"Socket error during connection: {e}")
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            return False
    
    def send_message(self, message: str) -> Optional[str]:
        """
        Send a message to the server and receive response
        
        Args:
            message: Message to send to server
        
        Returns:
            str: Server response if successful, None otherwise
        """
        if not self.socket:
            logger.error("Not connected to server")
            return None
        
        try:
            # Set timeout for send/receive operations
            self.socket.settimeout(self.timeout)
            
            # Validate message
            if not message or not isinstance(message, str):
                logger.error("Invalid message: message must be a non-empty string")
                return None
            
            # Send message to server
            logger.info(f"Sending message: {message}")
            self.socket.sendall(message.encode('utf-8'))
            
            # Receive response from server
            response = self.socket.recv(1024)
            
            if response:
                response_str = response.decode('utf-8')
                logger.info(f"Received from server: {response_str}")
                return response_str
            else:
                logger.warning("Server closed connection without response")
                return None
        
        except socket.timeout:
            logger.error(f"Socket timeout: No response from server within {self.timeout} seconds")
            return None
        
        except UnicodeEncodeError as e:
            logger.error(f"Encoding error: Could not encode message: {e}")
            return None
        
        except UnicodeDecodeError as e:
            logger.error(f"Decoding error: Could not decode server response: {e}")
            return None
        
        except ConnectionResetError:
            logger.error("Connection reset: Server closed the connection unexpectedly")
            return None
        
        except BrokenPipeError:
            logger.error("Broken pipe: Connection to server is broken")
            return None
        
        except socket.error as e:
            logger.error(f"Socket error during communication: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error during communication: {e}")
            return None
    
    def close(self) -> None:
        """Close the connection to the server"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            finally:
                self.socket = None


def main() -> None:
    """Main entry point for the client"""
    
    # Create client instance
    client = Client(host='localhost', port=5000, timeout=10)
    
    # Connect to server
    if not client.connect():
        logger.error("Failed to connect to server. Exiting.")
        sys.exit(1)
    
    try:
        # Interactive message loop
        while True:
            try:
                # Get user input
                user_input = input("\nEnter message to send (or 'quit' to exit): ").strip()
                
                if user_input.lower() == 'quit':
                    logger.info("Exiting client")
                    break
                
                if not user_input:
                    logger.warning("Empty message, please try again")
                    continue
                
                # Send message and get response
                response = client.send_message(user_input)
                
                if response is None:
                    logger.warning("Failed to send message, attempting to reconnect...")
                    if not client.connect():
                        logger.error("Failed to reconnect to server")
                        break
            
            except KeyboardInterrupt:
                logger.info("\nClient interrupted by user")
                break
            
            except Exception as e:
                logger.error(f"Unexpected error in message loop: {e}")
                break
    
    finally:
        client.close()


if __name__ == '__main__':
    main()
