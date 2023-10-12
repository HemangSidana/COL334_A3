import socket
import hashlib
import time

# Server address and port
server_ip = '10.184.7.7'
server_port = 9801

# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Send SendSize request to get the number of bytes to receive
send_size_command = "SendSize\n\nReset\n\n"
client_socket.sendto(send_size_command.encode(), (server_ip, server_port))

# Receive response from the server
response, server_address = client_socket.recvfrom(1024)
print("Server Response:", response.decode())

# Extract number of bytes from the response
num_bytes = int(response.decode().split()[1])
print(num_bytes)
# Initialize variables
offset = 0
chunk_size = 1448
received_data = b""
filesize=0
content=""
# Loop to receive data in chunks
while offset < num_bytes:
    time.sleep(0.01)
    # Construct request for a specific offset and number of bytes
    try:
        request = f"Offset: {offset}\nNumBytes: {min(num_bytes-offset,chunk_size)}\n\n"
        client_socket.sendto(request.encode(), (server_ip, server_port))
        client_socket.settimeout(0.01)
        # Receive response from the server
        response, server_address = client_socket.recvfrom(2000)

        # Extract offset, number of bytes, and data from the response
        response_lines = response.decode().split('\n')
        received_offset = int(response_lines[0].split()[1])
        received_bytes = int(response_lines[1].split()[1])
        filesize+=received_bytes
       
        data = response_lines[3].encode()
        content+=response_lines[3]
        for i in range(4,len(response_lines)):
            data+='\n'.encode()
            data+=response_lines[i].encode()
            content+='\n'
            content+=response_lines[i]
       

        # print(data)
        # Update offset for the next request
        
        # Verify if the received data matches the expected offset
        if received_offset != offset:
            print("Data integrity compromised!")
            break

        offset += received_bytes
        received_data += data
    except socket.timeout:
        pass
        # print("skipped")

# print(filesize)
# Calculate MD5 hash in hexadecimal format
# print(content)
md5_hash = hashlib.md5(received_data)
md5_hex = md5_hash.hexdigest()

# Submit MD5 hash to the server for validation
submit_command = f"Submit: aseth@col334-672\nMD5: {md5_hex}\n\n"
client_socket.sendto(submit_command.encode(), (server_ip, server_port))

# Receive validation response from the server
response, server_address = client_socket.recvfrom(1024)
print("Validation Response:", response.decode())

# Close the socket
client_socket.close()
