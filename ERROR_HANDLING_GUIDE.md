# Client-Server Communication System - Error Handling Guide

## Overview
This guide explains the error handling mechanisms implemented in the basic client-server communication system.

---

## Server Error Handling (`server.py`)

### 1. **Startup Errors**
| Error Type | Cause | Handling |
|-----------|-------|----------|
| `socket.error` | Port already in use, permission denied | Logs error and returns False, prevents server start |
| `OSError` | OS-level socket issues | Catches and logs, prevents server start |
| `socket.SO_REUSEADDR` | Allows reusing address if server restarts | Prevents "Address already in use" error |

### 2. **Connection Acceptance Errors**
| Error Type | Cause | Handling |
|-----------|-------|----------|
| `socket.timeout` | Timeout while waiting for connections | Continues listening for next connection |
| `OSError` | OS error accepting connection | Logs error, breaks loop if server is running |

### 3. **Client Handling Errors**
| Error Type | Cause | Handling |
|-----------|-------|----------|
| `socket.timeout` | Client doesn't send data within 30 seconds | Sends timeout message to client |
| `UnicodeDecodeError` | Invalid UTF-8 encoding in message | Logs error, sends error response to client |
| `socket.error` | Socket communication failure | Catches and logs the error |
| `ConnectionResetError` | Client forcefully closes connection | Handled gracefully, client marked as closed |

### 4. **Resource Cleanup**
```python
finally:
    try:
        client_socket.close()
    except:
        pass
```
- Ensures sockets are always closed
- Prevents resource leaks even if errors occur
- Uses bare except to catch all closure errors

### 5. **Multi-threading Safety**
```python
with self.client_lock:
    self.client_count += 1
```
- Thread lock protects shared client counter
- Prevents race conditions in multi-client scenarios
- Ensures consistent client numbering

---

## Client Error Handling (`client.py`)

### 1. **Connection Errors**

#### Timeout Error
```python
except socket.timeout:
    logger.error(f"Connection timeout...")
    return False
```
- Occurs when server doesn't respond within timeout period
- Prevents indefinite waiting
- User-friendly error message

#### Connection Refused
```python
except ConnectionRefusedError:
    logger.error(f"Connection refused...")
    return False
```
- Server is not listening on specified port
- Indicates server may not be running

#### Address Resolution Error
```python
except socket.gaierror as e:
    logger.error(f"Address error...")
    return False
```
- Hostname cannot be resolved to IP
- Invalid host name or DNS issues

### 2. **Message Communication Errors**

#### Encoding Error
```python
except UnicodeEncodeError as e:
    logger.error(f"Encoding error...")
    return None
```
- Message contains characters that can't be encoded to UTF-8
- Prevents sending corrupted data

#### Decoding Error
```python
except UnicodeDecodeError as e:
    logger.error(f"Decoding error...")
    return None
```
- Server response contains invalid UTF-8
- Indicates data corruption

#### Connection Reset
```python
except ConnectionResetError:
    logger.error(f"Connection reset...")
    return None
```
- Server forcefully closes connection
- Triggers automatic reconnection attempt

#### Broken Pipe
```python
except BrokenPipeError:
    logger.error(f"Broken pipe...")
    return None
```
- Connection is broken during transmission
- Indicates network or server issue

### 3. **Message Validation**
```python
if not message or not isinstance(message, str):
    logger.error("Invalid message...")
    return None
```
- Validates message before sending
- Prevents type errors
- Rejects empty messages

### 4. **Reconnection Logic**
```python
if response is None:
    logger.warning("Failed to send message, attempting to reconnect...")
    if not client.connect():
        logger.error("Failed to reconnect to server")
        break
```
- Automatically attempts reconnection on failed send
- Gracefully exits if reconnection fails
- Provides user feedback on connection status

### 5. **Graceful Shutdown**
```python
finally:
    client.close()
```
- Ensures socket is closed even if errors occur
- Cleans up resources properly
- Prevents socket leaks

---

## Error Handling Strategies

### Logging
- **All errors are logged** with timestamps and severity levels
- Helps with debugging and monitoring
- Uses Python's `logging` module for structured logging

### Timeout Management
- **Server**: 30-second timeout per client
- **Client**: 10-second timeout for all operations
- Prevents indefinite waiting and resource exhaustion

### Graceful Degradation
- Errors don't crash the application
- Server continues accepting new connections
- Client can reconnect automatically

### Resource Cleanup
- All sockets properly closed in `finally` blocks
- Prevents file descriptor leaks
- Ensures OS resources are freed

### User-Friendly Messages
- Clear logging messages for all errors
- Helps users understand what went wrong
- Guides troubleshooting steps

---

## Testing Error Scenarios

### Test Case 1: Server Not Running
```bash
python client.py
# Expected: ConnectionRefusedError, user-friendly message
```

### Test Case 2: Network Timeout
```bash
# Stop server mid-communication
# Expected: socket.timeout, automatic reconnection attempt
```

### Test Case 3: Invalid Encoding
```bash
# Send binary data instead of UTF-8
# Expected: UnicodeDecodeError, error message to client
```

### Test Case 4: Port Already in Use
```bash
# Start server, then try starting another on same port
# Expected: OSError, clear error message
```

### Test Case 5: Keyboard Interrupt
```bash
# Press Ctrl+C during operation
# Expected: Graceful shutdown, proper cleanup
```

---

## Best Practices Implemented

1. **Specific Exception Handling** - Catches specific errors rather than generic ones
2. **Logging** - All errors logged for debugging
3. **Resource Cleanup** - Proper `finally` blocks and cleanup
4. **Timeouts** - Prevents indefinite waiting
5. **Validation** - Input validation before processing
6. **Thread Safety** - Locks for shared resources
7. **Graceful Degradation** - System continues running despite errors
8. **User Feedback** - Clear messages for all scenarios

---

## Running the System

### Terminal 1 (Server):
```bash
python server.py
# Output: Server started on localhost:5000
```

### Terminal 2 (Client):
```bash
python client.py
# Enter messages when prompted
```

### Example Session:
```
Successfully connected to server at localhost:5000

Enter message to send (or 'quit' to exit): Hello Server
Sending message: Hello Server
Received from server: Server received: Hello Server

Enter message to send (or 'quit' to exit): quit
Exiting client
Connection closed
```

---

## Summary

The error handling system includes:
- ✅ Socket errors (connection, timeout, etc.)
- ✅ Data encoding/decoding errors
- ✅ Resource cleanup in all paths
- ✅ Multi-threading safety
- ✅ Automatic reconnection
- ✅ Comprehensive logging
- ✅ Graceful shutdown
- ✅ Input validation
