"""
Basic Server Script - Listens for client connections
Handles multiple clients with error management
"""

import socket
import threading
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Server:
    def __init__(self, host: str = 'localhost', port: int = 5000, backlog: int = 5):
        """
        Initialize server with host, port, and backlog settings
        
        Args:
            host: Server IP address (default: localhost)
            port: Server port number (default: 5000)
            backlog: Maximum queued connections (default: 5)
        """
        self.host = host
        self.port = port
        self.backlog = backlog
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.client_count = 0
        self.client_lock = threading.Lock()
    
    def start(self) -> bool:
        """
        Start the server and listen for incoming connections
        
        Returns:
            bool: True if server started successfully, False otherwise
        """
        try:
            # Create a socket object
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Allow reusing the address to avoid "Address already in use" errors
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind the socket to the port
            self.server_socket.bind((self.host, self.port))
            
            # Listen for incoming connections
            self.server_socket.listen(self.backlog)
            
            self.running = True
            logger.info(f"Server started on {self.host}:{self.port}")
            logger.info(f"Waiting for connections... (backlog: {self.backlog})")
            
            return True
        
        except socket.error as e:
            logger.error(f"Socket error during server startup: {e}")
            return False
        except OSError as e:
            logger.error(f"OS error during server startup: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during server startup: {e}")
            return False
    
    def accept_connections(self) -> None:
        """
        Accept incoming client connections in a loop
        Each connection is handled in a separate thread
        """
        try:
            while self.running:
                try:
                    # Accept a connection
                    client_socket, client_address = self.server_socket.accept()
                    
                    with self.client_lock:
                        self.client_count += 1
                        client_id = self.client_count
                    
                    logger.info(f"Client {client_id} connected from {client_address}")
                    
                    # Handle each client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address, client_id),
                        daemon=True
                    )
                    client_thread.start()
                
                except socket.timeout:
                    # Socket timeout - continue listening
                    continue
                except OSError as e:
                    if self.running:
                        logger.error(f"Error accepting connection: {e}")
                    break
        
        except Exception as e:
            logger.error(f"Unexpected error in accept_connections: {e}")
        finally:
            self.shutdown()
    
    def handle_client(self, client_socket: socket.socket, client_address: tuple, client_id: int) -> None:
        """
        Handle individual client communication
        
        Args:
            client_socket: Socket object for the client
            client_address: Client address tuple (IP, port)
            client_id: Unique client identifier
        """
        try:
            # Set a timeout for socket operations (30 seconds)
            client_socket.settimeout(30)
            
            # Receive data from client
            data = client_socket.recv(1024)
            
            if data:
                message = data.decode('utf-8')
                logger.info(f"Client {client_id} sent: {message}")
                
                # Send response back to client
                response = f"Server received: {message}"
                client_socket.sendall(response.encode('utf-8'))
                logger.info(f"Response sent to Client {client_id}")
            else:
                logger.info(f"Client {client_id} disconnected (no data received)")
        
        except socket.timeout:
            logger.warning(f"Socket timeout for Client {client_id}")
            try:
                error_msg = "Server: Connection timeout"
                client_socket.sendall(error_msg.encode('utf-8'))
            except:
                pass
        
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error from Client {client_id}: {e}")
            try:
                error_msg = "Server: Invalid message encoding"
                client_socket.sendall(error_msg.encode('utf-8'))
            except:
                pass
        
        except socket.error as e:
            logger.error(f"Socket error with Client {client_id}: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error handling Client {client_id}: {e}")
        
        finally:
            try:
                client_socket.close()
                logger.info(f"Client {client_id} connection closed")
            except:
                pass
    
    def shutdown(self) -> None:
        """Gracefully shutdown the server"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
                logger.info("Server shut down")
            except:
                pass


def main() -> None:
    """Main entry point for the server"""
    server = Server(host='localhost', port=5000)
    
    if server.start():
        try:
            server.accept_connections()
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
            server.shutdown()
    else:
        logger.error("Failed to start server")


if __name__ == '__main__':
    main()
