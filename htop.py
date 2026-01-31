import psutil
import os
import datetime
from notify import send

def get_docker_memory():
    """获取 Docker 容器真实内存限制（cgroup v2 优先）"""
    try:
        with open("/sys/fs/cgroup/memory.max") as f:
            mem_max = f.read().strip()
        with open("/sys/fs/cgroup/memory.current") as f:
            mem_cur = int(f.read().strip())

        if mem_max.isdigit():
            mem_max = int(mem_max)
            used = mem_cur / (1024 ** 3)
            total = mem_max / (1024 ** 3)
            percent = mem_cur / mem_max * 100
            return f"【容器内存】{used:.2f} / {total:.2f} GB ({percent:.1f}%)\n"
    except:
        pass
    return ""

def get_system_info():
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    load1, load5, load15 = os.getloadavg()
    cpu_info = (
        f"【CPU】{cpu_percent}%\n"
        f"【负载】{load1:.2f} / {load5:.2f} / {load15:.2f}\n"
    )

    # 内存（宿主视角）
    mem = psutil.virtual_memory()
    mem_info = f"【内存】{mem.used/1e9:.2f} / {mem.total/1e9:.2f} GB ({mem.percent}%)\n"

    # Docker 容器内存
    docker_mem = get_docker_memory()

    # 磁盘
    disk = psutil.disk_usage('/')
    disk_info = f"【磁盘】{disk.used/1e9:.2f} / {disk.total/1e9:.2f} GB ({disk.percent}%)\n"

    # 网络
    net = psutil.net_io_counters()
    net_info = (
        f"【网络】↑ {net.bytes_sent/1e6:.1f} MB "
        f"↓ {net.bytes_recv/1e6:.1f} MB\n"
    )

    # 运行时间
    boot = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot
    uptime_info = f"【运行】{uptime.days}天 {uptime.seconds//3600}小时\n"

    return (
        f"📊 服务器状态\n"
        f"时间: {now}\n"
        f"{'-'*24}\n"
        f"{cpu_info}{mem_info}{docker_mem}{disk_info}{net_info}{uptime_info}"
    )

# 执行
msg = get_system_info()
send("服务器状态监控", msg)
