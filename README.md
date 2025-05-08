# DNSpeedy

### Mac DNS Benchmark & Auto-Switcher

一个用于测试DNS服务器速度并自动设置最快DNS的命令行工具。

## 功能特点

- 从文本文件读取DNS服务器地址列表
- 多线程并行测试DNS服务器响应时间
- 使用大根堆算法自动选择最快的DNS服务器
- 自动设置系统DNS为最快的服务器
- 刷新DNS缓存以立即生效
- 友好的进度条显示测试进度

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/DNSpeedy.git
cd DNSpeedy

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

```bash
# 基本用法
python dnspeedy.py

# 指定DNS服务器列表文件
python dnspeedy.py --dns-file custom_dns_list.txt

# 指定测试域名
python dnspeedy.py --test-domain www.google.com

# 设置线程数
python dnspeedy.py --max-workers 20

# 只测试不设置DNS
python dnspeedy.py --no-set-dns

# 设置最快的前5个DNS服务器（默认为10个）
python dnspeedy.py --top-n 5

# 指定网络接口
python dnspeedy.py --interface en0
```

## 参数说明

- `--dns-file, -f`: DNS服务器地址列表文件路径（默认：dns_servers.txt）
- `--test-domain, -d`: 用于测试的域名（默认：www.baidu.com）
- `--max-workers, -w`: 最大工作线程数（默认：10）
- `--set-dns/--no-set-dns`: 是否设置系统DNS（默认：设置）
- `--top-n, -n`: 选择最快的前N个DNS服务器（默认：10）
- `--interface, -i`: 要设置DNS的网络接口名称（默认：Wi-Fi）

## DNS服务器列表格式

每行一个DNS服务器IP地址，例如：

```
8.8.8.8
8.8.4.4
1.1.1.1
```

## 注意事项

- 需要sudo权限来设置系统DNS和刷新DNS缓存
- 目前仅支持macOS系统
- 默认设置Wi-Fi接口的DNS，可通过`--interface`参数指定其他网络接口

## 许可证

[MIT](LICENSE)