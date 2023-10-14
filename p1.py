import socket
import hashlib
import time

server_ip = '10.184.7.7'
server_port = 9801

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

send_size_command = "SendSize\n\nReset\n\n"
client_socket.sendto(send_size_command.encode(), (server_ip, server_port))

response, server_address = client_socket.recvfrom(1024)
print("Server Response:", response.decode())

# Extract number of bytes from the response
num_bytes = int(response.decode().split()[1])
offset = 0
chunk_size = 1448
received_data = b""

while offset < num_bytes:
    time.sleep(0.01)
    try:
        request = f"Offset: {offset}\nNumBytes: {min(num_bytes-offset,chunk_size)}\n\n"
        client_socket.sendto(request.encode(), (server_ip, server_port))
        client_socket.settimeout(0.01)
        response, server_address = client_socket.recvfrom(2000)

        response_lines = response.decode().split('\n')
        received_offset = int(response_lines[0].split()[1])
        received_bytes = int(response_lines[1].split()[1])
        
        data = response_lines[3].encode()
        for i in range(4,len(response_lines)):
            data+='\n'.encode()
            data+=response_lines[i].encode()

        if received_offset != offset:
            print("Data integrity compromised!")
            break

        offset += received_bytes
        received_data += data
    except socket.timeout:
        pass

md5_hash = hashlib.md5(received_data)
md5_hex = md5_hash.hexdigest()

submit_command = f"Submit: aseth@col334-672\nMD5: {md5_hex}\n\n"
client_socket.sendto(submit_command.encode(), (server_ip, server_port))

response, server_address = client_socket.recvfrom(1024)
print("Validation Response:", response.decode())

client_socket.close()
