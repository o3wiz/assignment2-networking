# Daniel Aviv 209228154
# Tal Lavi    314952730
import socket
import os
import sys


# Receive status class:
#     Valid - received bytes correctly
#     Empty - received empty bytes
#     Timeout - waited too long
class ReceiveStatus:
    VALID, EMPTY, TIMEOUT = range(3)


# reads from sock until provided term_bytes or timeout is reached.
# returns received bytes, and status.
def read_form_socket_until_term(sock: socket.socket, term_bytes: bytes, secs_timeout: float, chunk_size: int) -> tuple[bytes, int]:
    buffer = b""
    status = ReceiveStatus.VALID
    try:
        sock.settimeout(secs_timeout)   # setting timeout
        while not buffer.endswith(term_bytes) and (data := sock.recv(chunk_size)):
            buffer += data              # reading until term_bytes or no data is read
    except socket.timeout:              # timeout occurred
        status = ReceiveStatus.TIMEOUT
    finally:
        sock.settimeout(None)           # disabling timeout
    if not buffer and status != ReceiveStatus.TIMEOUT:
        status = ReceiveStatus.EMPTY    # received nothing
    return (buffer, status)


# checks wether path is exist or not
def path_exists(path: str) -> bool:
    return os.path.exists(path)


def get_binary_file_content(path: str) -> bytes:
    with open(path, "rb") as file:
        return file.read()


# http request (GET) class
class HTTPRequest:
    def __init__(self, payload: str) -> None:
        # parse http get payload to its path, and connection status
        file_start_idx = payload.find("/") + 1
        file_end_idx = payload.find(" ", file_start_idx)
        self.__path = payload[file_start_idx:file_end_idx]
        connection_start_idx = payload.find("Connection: ") + len("Connection: ")
        connection_end_idx = payload.find("\r\n", connection_start_idx)
        self.__connection = payload[connection_start_idx:connection_end_idx]

    # path getter
    @property
    def path(self) -> str:
        return self.__path

    # connection getter
    @property
    def connection(self) -> str:
        return self.__connection


class Server:
    # HTTPServer globals
    RECV_BUFFER_SIZE = 1024
    HTTP_REQUEST_BYTES_TERM = b"\r\n\r\n"  # terminating bytes of a http request
    HTTP_404_BYTES_MESSAGE = b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n"  # 404 http message
    # http result.html redirection message
    HTTP_REDIRECT_BYTES_MESSAGE = b"HTTP/1.1 301 Moved Permanently\r\nConnection: close\r\nLocation: /result.html\r\n\r\n"
    # http send file template
    HTTP_SEND_FILE_BYTES_FORMAT = b"HTTP/1.1 200 OK\r\nConnection: %b\r\nContent-Length: %d\r\n\r\n%b"
    SERVER_FILES_FOLDER = "files"  # files location
    RECV_TIMEOUT_SECS_DURATION = 1.0  # receive timeout duration
    def __init__(self, port_number: int) -> None:
        # Initializing the server with port number
        self.__port_number = port_number

    def run(self) -> None:
        # creating server TCP socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("", self.__port_number))
        server_socket.listen(5)
        while True:
            # accepting new client
            (client_socket, _) = server_socket.accept()
            keep_connection_open = True
            while keep_connection_open:  # as long as the connection is still open
                # getting request payload and its status
                payload, status = self.__get_http_request(client_socket)
                # if the status is not valid (empty or timeout)
                if status in {ReceiveStatus.EMPTY, ReceiveStatus.TIMEOUT}:
                    break  # end loop and close the connection
                # displaying client (valid) request
                client_request = payload.decode()
                print(client_request)
                # creating client's response, and updating keep_connection_open for next iteration
                (response_bytes, keep_connection_open) = self.__get_response(payload)
                client_socket.sendall(response_bytes)
            # closing current client's socket
            client_socket.close()

    # reads from client's socket until term_bytes, and returns the bytes, and receive status
    def __get_http_request(self, client_socket: socket.socket) -> tuple[bytes, int]:
        return read_form_socket_until_term(client_socket,
                                        self.HTTP_REQUEST_BYTES_TERM,
                                        self.RECV_TIMEOUT_SECS_DURATION,
                                        self.RECV_BUFFER_SIZE)

    # generating response based on client's http request, return bytes, and whether to leave the connection open
    def __get_response(self, payload: bytes) -> tuple[bytes, bool]:
        # http request construction from given payload
        http_request = HTTPRequest(payload.decode())
        connection = http_request.connection
        # if the client asks to leave the connection opened ("keep-alive")
        keep_connection_open = "keep-alive" == connection
        # making "" to "index.html" (if needed)
        request_path = http_request.path if http_request.path else "index.html"
        if "redirect" == request_path:  # if the client sent the path "redirect"
            # we are sending predefined response that set new location to result.html
            # and tells the server to close the connection
            return (self.HTTP_REDIRECT_BYTES_MESSAGE, False)
        # actual path is server's files location concatenated with the path in the request
        path = os.path.join(self.SERVER_FILES_FOLDER, request_path)
        if not path_exists(path):  # the file does not exist
            # sends back 404 message and tell the server to close the connection
            return (self.HTTP_404_BYTES_MESSAGE, False)
        # reading file content in binary
        content = get_binary_file_content(path)
        file_length = len(content)
        # constructing http response with file's size and content
        response_bytes = self.HTTP_SEND_FILE_BYTES_FORMAT % (connection.encode(), file_length, content)
        # returning the response and whether to keep the connection open or not
        return (response_bytes, keep_connection_open)


def main() -> None:
    # if no argument is provided
    if len(sys.argv) < 2:
        # if port number is missing it throws an exception
        raise ValueError("Usage: python3 server.py <port_number>")
    # parse given port number
    port_number = int(sys.argv[1])
    # making the server and running it
    server = Server(port_number)
    server.run()


if "__main__" == __name__:
    main()
