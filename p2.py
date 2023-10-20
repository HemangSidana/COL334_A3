import socket
import hashlib
import time

server_ip = '10.184.12.231'
server_port = 9801

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
send_size_command = "SendSize\n\nReset\n\n"
client_socket.sendto(send_size_command.encode(), (server_ip, server_port))

response, server_address = client_socket.recvfrom(1024)
num_bytes = int(response.decode().split()[1])

miss=0
offset = 0
chunk_size = 1448
burst=10
gap=0.01
gap2=0.01
num_packets=num_bytes//chunk_size
packets=[b""]*num_packets
visited=[False]*num_packets
remaining=[]
for i in range(num_packets):
    remaining.append(i)

while len(remaining)>0:
    if len(remaining)<burst:
        burst=len(remaining)
    rem=[]
    iterations=len(remaining)//burst
    for i in range(iterations):
        for k in range(burst):
            request = f"Offset: {remaining[i*burst+k]*chunk_size}\nNumBytes: {chunk_size}\n\n"
            client_socket.sendto(request.encode(), (server_ip, server_port))

        time.sleep(gap)
        k=0
        while k<burst:
            client_socket.settimeout(gap2)
            try:
                response, server_address = client_socket.recvfrom(2000)
                response_lines = response.decode().split('\n')
                received_offset = int(response_lines[0].split()[1])
                received_bytes = int(response_lines[1].split()[1])
                data=b""
                if response_lines[2]=="Squished":
                    data = response_lines[4].encode()
                    for x in range(5,len(response_lines)):
                        data+="\n".encode()
                        data+=response_lines[x].encode()
                else:
                    data = response_lines[3].encode()
                    for x in range(4,len(response_lines)):
                        data+="\n".encode()
                        data+=response_lines[x].encode()
                ind=remaining[i*burst+k]
                if received_offset!= (ind)*chunk_size:
                    ind_recv= received_offset//chunk_size
                    if not visited[ind_recv]:
                        packets[ind_recv]=data
                        visited[ind_recv]=True
                    else:
                        miss+=1
                    rem.append(ind)
                else: 
                    packets[ind]=data
                    visited[ind]=True
                k+=1

            except socket.timeout:
                break
        while k<burst: 
            rem.append(remaining[i*burst+k])
            k+=1
    for j in range(iterations*burst,len(remaining)):
        rem.append(remaining[j])
    remaining=[]
    for q in range(len(rem)):
        if not visited[rem[q]]:
            remaining.append(rem[q])

received_data = b""
for i in range(num_packets):
    received_data+=packets[i]

while True and num_bytes%chunk_size!=0 :
    request = f"Offset: {num_packets*chunk_size}\nNumBytes: {num_bytes%chunk_size}\n\n"
    client_socket.sendto(request.encode(), (server_ip, server_port))
    client_socket.settimeout(gap)
    try:
        response, server_address = client_socket.recvfrom(2000)
        response_lines = response.decode().split('\n')
        received_offset = int(response_lines[0].split()[1])
        received_bytes = int(response_lines[1].split()[1])
        data=b""
        if response_lines[2]=="Squished":
            data = response_lines[4].encode()
            for i in range(5,len(response_lines)):
                data+="\n".encode()
                data+=response_lines[i].encode()
        else:
            data = response_lines[3].encode()
            for i in range(4,len(response_lines)):
                data+="\n".encode()
                data+=response_lines[i].encode()
        if received_offset== num_packets*chunk_size:
            received_data+=data
            break
    except socket.timeout:
        pass
        
# print(received_data.decode())
print(miss)
md5_hash = hashlib.md5(received_data)
md5_hex = md5_hash.hexdigest()

submit_command = f"Submit: aseth@col334-672\nMD5: {md5_hex}\n\n"
client_socket.sendto(submit_command.encode(), (server_ip, server_port))

response, server_address = client_socket.recvfrom(1024)
print("Validation Response:", response.decode())

client_socket.close()
