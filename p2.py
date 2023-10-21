import socket
import hashlib
import time

begin=time.time()
server_ip = 'vayu.iitd.ac.in'
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
gap=0.02
gap2=0.02
num_packets=num_bytes//chunk_size
packets=[b""]*num_packets
visited=[False]*num_packets
remaining=[]
count1=0
count2=0
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
        flag=False
        time.sleep(gap)
        while True:
            client_socket.settimeout(0.01)
            try:
                response, server_address = client_socket.recvfrom(2000)
                response_lines = response.decode().split('\n')
                received_offset = int(response_lines[0].split()[1])
                received_bytes = int(response_lines[1].split()[1])
                if(response.decode().count('Offset'))!=1:
                    print(response.decode().count('Offset'))
                ind_recv= received_offset//chunk_size
                if not visited[ind_recv]:
                    data=b""
                    if response_lines[2]=="Squished":
                        count1+=1
                        data = response_lines[4].encode()
                        for x in range(5,len(response_lines)):
                            data+="\n".encode()
                            data+=response_lines[x].encode()
                        flag=True
                    else:
                        data = response_lines[3].encode()
                        for x in range(4,len(response_lines)):
                            data+="\n".encode()
                            data+=response_lines[x].encode()
                    packets[ind_recv]=data
                    visited[ind_recv]=True
            except socket.timeout:
                count2+=1
                #flag=True
                break
            if flag:
                #print("hi")
                flag=False
                gap=0.05
            else:
                #print("hello")
                gap=0.02

    count2-=iterations

    for j in range(len(remaining)):
        if not visited[remaining[j]]:
            rem.append(remaining[j])
    remaining=rem

received_data = b""
for i in range(num_packets):
    received_data+=packets[i]

time.sleep(0.1)

while True and num_bytes%chunk_size!=0 :
    request = f"Offset: {num_packets*chunk_size}\nNumBytes: {num_bytes%chunk_size}\n\n"
    client_socket.sendto(request.encode(), (server_ip, server_port))
    client_socket.settimeout(0.1)
    try:
        response, server_address = client_socket.recvfrom(2000)
        response_lines = response.decode().split('\n')
        received_offset = int(response_lines[0].split()[1])
        received_bytes = int(response_lines[1].split()[1])
        data=b""
        if response_lines[2]=="Squished":
            count1+=1
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
time.sleep(0.1)
print(miss)
md5_hash = hashlib.md5(received_data)
md5_hex = md5_hash.hexdigest()

submit_command = f"Submit: aseth@col334-672\nMD5: {md5_hex}\n\n"
client_socket.sendto(submit_command.encode(), (server_ip, server_port))
time.sleep(0.1)
while True:
    client_socket.settimeout(0.1)
    try:
        response, server_address = client_socket.recvfrom(2000)
        if response.decode().count('Time') and response.decode().count('Penalty'):
            print("Validation Response:", response.decode())
    except socket.timeout:
        client_socket.sendto(submit_command.encode(), (server_ip, server_port))
        break
print("Count1: ", count1)
print("Count2: ", count2)
print(time.time()-begin)
client_socket.close()