#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import heapq
import subprocess
import threading
import concurrent.futures
from typing import Dict, List, Tuple

import click
from tqdm import tqdm


class DNSSpeedTester:
    """DNS服务器速度测试工具"""
    
    def __init__(self, dns_file: str, test_domain: str = "www.baidu.com"):
        """初始化DNS速度测试器
        
        Args:
            dns_file: DNS服务器地址列表文件路径
            test_domain: 用于测试的域名
        """
        self.dns_file = dns_file
        self.test_domain = test_domain
        self.dns_servers = self._load_dns_servers()
        self.results: Dict[str, float] = {}
        self.fastest_dns: List[Tuple[float, str]] = []
        self.lock = threading.Lock()
    
    def _load_dns_servers(self) -> List[str]:
        """从文件加载DNS服务器地址列表"""
        with open(self.dns_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    
    def _test_dns_speed(self, dns_server: str) -> Tuple[str, float]:
        """测试单个DNS服务器的响应时间
        
        Args:
            dns_server: DNS服务器地址
            
        Returns:
            包含DNS服务器地址和响应时间(ms)的元组
        """
        try:
            cmd = f"dig @{dns_server} {self.test_domain} | grep 'Query time'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            output = result.stdout.strip()
            
            # 提取响应时间
            match = re.search(r'Query time: (\d+) msec', output)
            if match:
                response_time = float(match.group(1))
                return dns_server, response_time
            return dns_server, float('inf')  # 如果无法提取响应时间，返回无穷大
        except subprocess.TimeoutExpired:
            return dns_server, float('inf')  # 超时返回无穷大
        except Exception as e:
            print(f"测试DNS {dns_server} 时出错: {e}")
            return dns_server, float('inf')
    
    def _update_heap(self, dns_server: str, response_time: float):
        """更新大根堆，保持堆中只有10个最快的DNS服务器
        
        使用负的响应时间作为优先级，这样最快的DNS会有最高的优先级
        
        Args:
            dns_server: DNS服务器地址
            response_time: 响应时间(ms)
        """
        with self.lock:
            self.results[dns_server] = response_time
            
            # 如果堆中元素少于10个，直接添加
            if len(self.fastest_dns) < 10:
                heapq.heappush(self.fastest_dns, (-response_time, dns_server))
            else:
                # 如果当前DNS比堆顶元素快，替换堆顶
                if -response_time > self.fastest_dns[0][0]:
                    heapq.heappushpop(self.fastest_dns, (-response_time, dns_server))
    
    def _test_dns_and_update(self, dns_server: str, pbar: tqdm):
        """测试DNS并更新结果
        
        Args:
            dns_server: DNS服务器地址
            pbar: 进度条对象
        """
        dns_server, response_time = self._test_dns_speed(dns_server)
        self._update_heap(dns_server, response_time)
        pbar.update(1)
    
    def run_test(self, max_workers: int = 10):
        """运行DNS速度测试
        
        Args:
            max_workers: 最大工作线程数
            
        Returns:
            最快的DNS服务器列表
        """
        print(f"开始测试 {len(self.dns_servers)} 个DNS服务器的响应速度...")
        
        # 创建一个进度条
        with tqdm(total=len(self.dns_servers), desc="测试进度") as pbar:
            # 使用线程池执行测试
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                futures = [executor.submit(self._test_dns_and_update, dns, pbar) for dns in self.dns_servers]
                # 等待所有任务完成
                concurrent.futures.wait(futures)
        
        # 获取最快的DNS服务器（按速度从快到慢排序）
        with self.lock:
            self.fastest_dns.sort(key=lambda x: -x[0])  # 按负的响应时间排序（实际上是从小到大）
            fastest_servers = [server for _, server in self.fastest_dns]
        
        return fastest_servers
    
    def set_system_dns(self, dns_servers: List[str], interface: str = "Wi-Fi"):
        """设置系统DNS服务器
        
        Args:
            dns_servers: 要设置的DNS服务器地址列表
            interface: 要设置DNS的网络接口名称
        """
        if not dns_servers:
            print("没有可用的DNS服务器")
            return
        
        dns_str = " ".join(dns_servers)
        try:
            # 设置系统DNS
            print(f"\n正在设置{interface}接口的DNS...")
            cmd = f"sudo networksetup -setdnsservers {interface} {dns_str}"
            subprocess.run(cmd, shell=True, check=True)
            
            # 刷新DNS缓存
            print("正在刷新DNS缓存...")
            subprocess.run("sudo killall -HUP mDNSResponder", shell=True, check=True)
            
            print(f"\n成功设置{interface}接口的DNS为最快的 {len(dns_servers)} 个服务器")
        except subprocess.CalledProcessError as e:
            print(f"设置系统DNS时出错: {e}")
        except Exception as e:
            print(f"发生错误: {e}")


@click.command()
@click.option('--dns-file', '-f', default='dns_servers.txt', help='DNS服务器地址列表文件')
@click.option('--test-domain', '-d', default='www.baidu.com', help='用于测试的域名')
@click.option('--max-workers', '-w', default=10, help='最大工作线程数')
@click.option('--set-dns/--no-set-dns', default=True, help='是否设置系统DNS')
@click.option('--top-n', '-n', default=10, help='选择最快的前N个DNS服务器')
@click.option('--interface', '-i', default='Wi-Fi', help='要设置DNS的网络接口名称')
def main(dns_file: str, test_domain: str, max_workers: int, set_dns: bool, top_n: int, interface: str):
    """DNS服务器速度测试工具，测试DNS服务器响应速度并设置最快的DNS"""
    # 清除之前的输出
    os.system('clear' if os.name == 'posix' else 'cls')
    
    tester = DNSSpeedTester(dns_file, test_domain)
    fastest_servers = tester.run_test(max_workers)
    
    # 只取前top_n个最快的服务器
    fastest_servers = fastest_servers[:top_n]
    
    # 显示最快的DNS服务器
    print("\n最快的DNS服务器:")
    for i, (neg_time, server) in enumerate(tester.fastest_dns[:top_n], 1):
        print(f"{i}. {server} - {-neg_time:.2f} ms")
    
    if set_dns and fastest_servers:
        tester.set_system_dns(fastest_servers, interface)


if __name__ == '__main__':
    main()