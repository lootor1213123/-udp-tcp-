import socket
import struct
import time
import threading

IP = "113.249.107.84"
SERVER_PORT = 8888

# 定义一个包的结构，报文头部就是4字节的包序号和4字节的确认号，1024s代表每一个包是数据荷载是1024字节
Packet = struct.Struct("II1024s")


# 建立连接
class Connect:

    def __init__(self, target_ip, target_port):
        # 创建udp socket的属性
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.target_addr = (target_ip, target_port)
        self.seq = 0  # 初始化序号
        self.ack = 0  # 初始化确认号,用于对上一个seq序号的包确认
        self.SYN = 1  # 初始化SYN标志位的值
        self.ACK = 1  # 初始化回复确认号，这里面的ACK和ack含义不同
        self.FIN = 1  # 初始化FIN标志位的值

    # 发送前需要建立三次握手连接
    def handle(self):
        syn_packet = Packet.pack(self.SYN, self.seq, b'\x00' * 1024)

        self.sock.sendto(syn_packet, self.target_addr)

        print("客户端向服务端发起第一次握手请求")

        # 等待服务端返回确认号
        data, addr = self.sock.recvfrom(2048)

        if data:
            SYN, ACK, seq, ack = struct.unpack("IIII", data)
            if SYN == self.SYN and ACK == self.ACK:
                # ack是确认我们客户端发给对方的参数
                if ack - 1 == self.seq:

                    # 前两次握手已经成功完成, 接下来让客户端发送一个包给服务端
                    print("成功接受服务端发送的包")

                    # 这个包用于再次问服务端确认是否已经连接成功
                    # 包结构： ACK seq ack= seq(原先的上一个包) + 1
                    Packet2 = struct.Struct("III")

                    # self.seq指的是自己的seq包，seq + 1 代表对对方的seq + 1
                    syn_packet = Packet2.pack(self.ACK, self.seq + 1, seq + 1)
                    self.sock.sendto(syn_packet, self.target_addr)
                    print("三次握手完毕，开始发送文件")
                    return True

                else:
                    print("三次握手失败，断开,请重试")
                    self.sock.close()


class SendFile:
    def __init__(self, sock, target_addr, file_path):
        self.sock = sock
        self.target_addr = target_addr
        self.file_path = file_path
        self.seq, self.ack = 0, 0

    def send(self, file_path):

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    # 文件读完了，发结束标志
                    fin_packet = Packet.pack(self.seq, self.ack, b'FIN' + b'\x00' * 1021)
                    self.sock.sendto(fin_packet, self.target_addr)
                    print("文件发送完毕")
                    break

                packet = Packet.pack(self.seq, self.ack, chunk)
                self.sock.sendto(packet, self.target_addr)

                # 等待对方发回来确认
                data, _ = self.sock.recvfrom(2048)
                recv_seq, recv_ack, _ = Packet.unpack(data)

                if recv_ack == self.seq + 1:
                    print("成功接受到了对方的包")
                    self.seq += 1


if __name__ == '__main__':
    s1 = Connect(IP, SERVER_PORT)
    send = s1.handle()
    if send:
        file = input("请输入文件路径")
        s2 = SendFile(s1.sock, s1.target_addr, file)
        s2.send(file)
