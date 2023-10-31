import socket
import hashlib
import time
import matplotlib.pyplot as plt

server_ip = '10.17.7.218'
server_port = 9802

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
send_size_command = "SendSize\nReset\n\n"
client_socket.sendto(send_size_command.encode(), (server_ip, server_port))

response, server_address = client_socket.recvfrom(1024)
num_bytes = int(response.decode().split()[1])

miss=0
chunk_size = 1448
gap=0.006
num_packets=num_bytes//chunk_size
packets=[b""]*num_packets
visited=[False]*num_packets
remaining=[]
count1=0
count2=0
burst=5
burst_val=[]
burst_itr=[]

for i in range(num_packets):
    remaining.append(i)

while len(remaining)>0:
    i=0
    flag=False
    prev_sent=0
    while i<len(remaining):
        send= True
        req_send=0
        cur_sent=0
        got=0
        first=False
        while True:
            begin=time.time()
            client_socket.settimeout(gap)
            try:
                if i%100==0:
                    print(i)
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
                        # time.sleep(0.01)
                    else:
                        data = response_lines[3].encode()
                        for x in range(4,len(response_lines)):
                            data+="\n".encode()
                            data+=response_lines[x].encode()
                        if i<len(remaining):
                            request = f"Offset: {remaining[i]*chunk_size}\nNumBytes: {chunk_size}\n\n"
                            client_socket.sendto(request.encode(), (server_ip, server_port))
                            i+=1
                            cur_sent+=1
                        #     time.sleep(gap/10)
                    packets[ind_recv]=data
                    visited[ind_recv]=True
                send=False
                got+=1
                first=True
            except socket.timeout:
                if not send and (first or time.time()-begin>10*gap):
                    break
                # if not send:
                #     continue
                if i>=len(remaining):
                    continue
                request = f"Offset: {remaining[i]*chunk_size}\nNumBytes: {chunk_size}\n\n"
                client_socket.sendto(request.encode(), (server_ip, server_port))
                req_send+=1
                i+=1
                # time.sleep(5*gap/burst)
                if req_send+prev_sent>=burst:
                    send=False
        prev_sent=cur_sent
        if got*10<burst*8:
            burst=max(1,burst//2)
            # if burst>5:
            #     burst-=3
            # else:
            #     burst=max(1,burst//2)
            gap*=1.25
        elif flag:
            burst=1
        else:
            gap*=0.9
            burst=min(10,burst+1)
            # burst+=1
        time.sleep(gap)
        burst_val.append(100*got/burst)
        burst_itr.append(i)
        # print(burst)
    rem=[]
    for j in range(len(remaining)):
        if not visited[remaining[j]]:
            rem.append(remaining[j])
    remaining=rem

print(gap)
received_data = b""
for i in range(num_packets):
    received_data+=packets[i]

time.sleep(0.01)

while num_bytes%chunk_size!=0 :
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
print(miss)
md5_hash = hashlib.md5(received_data)
md5_hex = md5_hash.hexdigest()

submit_command = f"Submit: aseth@col334-672\nMD5: {md5_hex}\n\n"
client_socket.sendto(submit_command.encode(), (server_ip, server_port))
while True:
    client_socket.settimeout(0.1)
    try:
        response, server_address = client_socket.recvfrom(2000)
        if response.decode().count('Time') and response.decode().count('Penalty'):
            print("Validation Response:", response.decode())
            break
    except socket.timeout:
        client_socket.sendto(submit_command.encode(), (server_ip, server_port))
    
print("Count1: ", count1)
print("Count2: ", count2)
client_socket.close()

plt.scatter(burst_itr,burst_val,color='blue',marker='o',s=5,label='Burst Size')
plt.show()