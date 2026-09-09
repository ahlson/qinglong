import psutil
import os
import sys
import datetime


# ============================================================
# 青龙通知
# ============================================================

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from notify import send


# ============================================================
# Docker 容器内存
# ============================================================

def get_docker_memory():
    """
    获取 Docker 容器真实内存使用情况
    优先使用 cgroup v2
    """

    # --------------------------------------------------------
    # cgroup v2
    # --------------------------------------------------------
    try:
        memory_max_file = "/sys/fs/cgroup/memory.max"
        memory_current_file = "/sys/fs/cgroup/memory.current"

        if (
            os.path.exists(memory_max_file)
            and os.path.exists(memory_current_file)
        ):

            with open(memory_max_file, "r") as f:
                mem_max = f.read().strip()

            with open(memory_current_file, "r") as f:
                mem_cur = int(f.read().strip())

            used = mem_cur / (1024 ** 3)

            # 未设置内存限制
            if mem_max == "max":
                return (
                    f"【容器内存】"
                    f"{used:.2f} GB "
                    f"(未设置限制)\n"
                )

            if mem_max.isdigit():

                mem_max = int(mem_max)

                total = mem_max / (1024 ** 3)

                percent = (
                    mem_cur / mem_max * 100
                    if mem_max > 0
                    else 0
                )

                return (
                    f"【容器内存】"
                    f"{used:.2f} / "
                    f"{total:.2f} GB "
                    f"({percent:.1f}%)\n"
                )

    except Exception:
        pass


    # --------------------------------------------------------
    # cgroup v1
    # --------------------------------------------------------
    try:

        limit_file = (
            "/sys/fs/cgroup/memory/"
            "memory.limit_in_bytes"
        )

        usage_file = (
            "/sys/fs/cgroup/memory/"
            "memory.usage_in_bytes"
        )

        if (
            os.path.exists(limit_file)
            and os.path.exists(usage_file)
        ):

            with open(limit_file, "r") as f:
                mem_max = int(f.read().strip())

            with open(usage_file, "r") as f:
                mem_cur = int(f.read().strip())

            used = mem_cur / (1024 ** 3)
            total = mem_max / (1024 ** 3)

            percent = (
                mem_cur / mem_max * 100
                if mem_max > 0
                else 0
            )

            return (
                f"【容器内存】"
                f"{used:.2f} / "
                f"{total:.2f} GB "
                f"({percent:.1f}%)\n"
            )

    except Exception:
        pass


    return ""


# ============================================================
# 网络
# ============================================================

def get_network():
    """
    获取青龙 Docker 容器自身累计网络流量

    bytes_sent = 上传
    bytes_recv = 下载

    注意：
    这是容器网络命名空间的累计流量，
    不是宿主机物理网卡总流量。
    """

    try:

        net = psutil.net_io_counters()

        upload_bytes = net.bytes_sent
        download_bytes = net.bytes_recv

        upload_gb = upload_bytes / (1024 ** 2)
        download_gb = download_bytes / (1024 ** 2)

        return (
            f"【网络】"
            f"↑ {upload_gb:.2f} MB "
            f"↓ {download_gb:.2f} MB\n"
        )

    except Exception as e:

        return (
            f"【网络】获取失败：{e}\n"
        )


# ============================================================
# 系统运行时间
# ============================================================

def get_uptime():

    try:

        boot_time = datetime.datetime.fromtimestamp(
            psutil.boot_time()
        )

        now = datetime.datetime.now()

        uptime = now - boot_time

        days = uptime.days

        hours = uptime.seconds // 3600

        minutes = (
            uptime.seconds % 3600
        ) // 60

        return (
            f"【运行】"
            f"{days}天 "
            f"{hours}小时 "
            f"{minutes}分钟\n"
        )

    except Exception as e:

        return (
            f"【运行】获取失败：{e}\n"
        )


# ============================================================
# 服务器状态
# ============================================================

def get_system_info():

    # --------------------------------------------------------
    # 时间
    # --------------------------------------------------------

    now = datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # --------------------------------------------------------
    # CPU
    # --------------------------------------------------------

    # 自动获取逻辑 CPU 核心数
    cpu_cores = (
        psutil.cpu_count(logical=True)
        or 1
    )

    # CPU 使用率
    cpu_percent = psutil.cpu_percent(
        interval=1
    )

    cpu_info = (
        f"【CPU】"
        f"{cpu_percent:.1f}%"
        f"（{cpu_cores}核）\n"
    )


    # --------------------------------------------------------
    # 系统负载
    # --------------------------------------------------------

    try:

        load1, load5, load15 = (
            os.getloadavg()
        )

        # 使用 1 分钟负载计算负载率
        #
        # 例如：
        # 4核 CPU
        # load1 = 2.25
        #
        # 2.25 / 4 × 100
        # = 56.25%

        load_percent = (
            load1 / cpu_cores * 100
        )

        # 这里不限制最大值。
        #
        # 如果 CPU 严重超载，
        # 显示 150%、200% 等反而更有意义。
        #
        # 例如：
        # 4核 CPU
        # load1 = 8
        # 负载率 = 200%

        load_info = (
            f"【负载】"
            f"{load1:.2f} / "
            f"{load5:.2f} / "
            f"{load15:.2f}\n"
            f"【负载率】"
            f"{load_percent:.1f}%\n"
        )

    except Exception as e:

        load_info = (
            f"【负载】获取失败：{e}\n"
        )


    # --------------------------------------------------------
    # 内存
    # --------------------------------------------------------

    mem = psutil.virtual_memory()

    mem_used_gb = (
        mem.used / (1024 ** 3)
    )

    mem_total_gb = (
        mem.total / (1024 ** 3)
    )

    mem_info = (
        f"【内存】"
        f"{mem_used_gb:.2f} / "
        f"{mem_total_gb:.2f} GB "
        f"({mem.percent:.1f}%)\n"
    )


    # --------------------------------------------------------
    # Docker 容器内存
    # --------------------------------------------------------

    docker_mem_info = (
        get_docker_memory()
    )


    # --------------------------------------------------------
    # 磁盘
    # --------------------------------------------------------

    disk = psutil.disk_usage("/")

    disk_used_gb = (
        disk.used / (1024 ** 3)
    )

    disk_total_gb = (
        disk.total / (1024 ** 3)
    )

    disk_info = (
        f"【磁盘】"
        f"{disk_used_gb:.2f} / "
        f"{disk_total_gb:.2f} GB "
        f"({disk.percent:.1f}%)\n"
    )


    # --------------------------------------------------------
    # 网络
    # --------------------------------------------------------

    network_info = get_network()


    # --------------------------------------------------------
    # 运行时间
    # --------------------------------------------------------

    uptime_info = get_uptime()


    # --------------------------------------------------------
    # 最终消息
    # --------------------------------------------------------

    message = (
        f"📊 服务器状态\n"
        f"时间: {now}\n"
        f"{'-' * 24}\n"
        f"{cpu_info}"
        f"{load_info}"
        f"{mem_info}"
        f"{docker_mem_info}"
        f"{disk_info}"
        f"{network_info}"
        f"{uptime_info}"
    )

    return message


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":

    msg = get_system_info()

    # 青龙日志中也显示
    print(msg)

    # 青龙系统通知
    send(
        "服务器状态监控",
        msg
    )
