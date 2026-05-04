import socket
import os
import struct
import time

IP = "0.0.0.0"
SERVER_PORT = 8888

# 定义一个包的结构，报文头部就是4字节的包序号和4字节的确认号，1024s代表每一个包是数据荷载是1024字节
Packet = struct.Struct("II1024s")


class Connect:

    def __init__(self, target_ip, target_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((target_ip, target_port))
        self.seq = 0  # 初始化序号
        self.ack = 0  # 初始化确认号,用于对上一个seq序号的包确认
        self.SYN = 1  # 初始化SYN标志位的值
        self.ACK = 1  # 初始化回复确认号，这里面的ACK和ack含义不同
        self.FIN = 1  # 初始化FIN标志位的值

    # 建立连接，三次握手
    def handle(self):
        data, client_addr = self.sock.recvfrom(2048)
        if data:

            # 先解包，把字节流转成Python对象
            SYN, seq, data = struct.unpack("II1024s", data)
            if SYN == 1:
                print("成功接收对方的请求,返回一个包给客户端")
                self.ack = seq + 1  # 确认号为收到的seq加1
                packet = struct.pack('IIII', self.SYN, self.ACK, self.seq, self.ack)

                # 服务端接收到来自客户端的seq包，返回ack给客户端确认
                self.sock.sendto(packet, client_addr)
                data, client_addr = self.sock.recvfrom(2048)
                ACK, seq, ack = struct.unpack("III", data)
                if ACK == 1 and ack == self.seq + 1:
                    print("三次握手成功，连接建立!")
                    return True
                else:
                    print("三次握手失败，连接建立失败，请尝试重新连接!")


class RecvFile:
    def __init__(self, sock):
        self.sock = sock  # 直接用握手那个socket，不新建
        # seq和ack用来检测文件
        self.seq, self.ack = 0, 0

    def recv(self):
        with open("received_file", "wb") as f:  # 创建文件
            while True:  # 循环收包

                data, client_addr = self.sock.recvfrom(2048)
                seq, ack, data = Packet.unpack(data)

                # 检查是不是结束标志, startswith是python 字符串/字节串的方法，用来检查开头是不是某个内容
                if data.startswith(b'FIN'):
                    print("文件接收完毕")
                    break

                if seq == self.seq:
                    self.ack = seq + 1
                    # 写入数据
                    f.write(data)

                    # 构造确认包，发回去
                    packet = Packet.pack(self.seq, self.ack, b'\x00' * 1024)
                    self.sock.sendto(packet, client_addr)
                    self.seq += 1


if __name__ == '__main__':
    s1 = Connect(IP, SERVER_PORT)
    recv = s1.handle()
    if recv:
        s2 = RecvFile(s1.sock)
        s2.recv()
