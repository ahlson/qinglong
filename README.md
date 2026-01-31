# qinglong
自用青龙脚本
拉库
```
ql repo https://github.com/ahlson/qinglong.git
```

# 要在系统环境中使用 `cron` 工具定时执行脚本，您可以按照以下步骤进行操作：

### 1. 创建脚本文件
首先，将上面的脚本保存为一个文件，例如 `/ql/data/scripts/system_monitor.py`。确保脚本具有可执行权限。您可以使用以下命令：

```bash
chmod +x /ql/data/scripts/system_monitor.py
```

### 2. 测试脚本
在设置 `cron` 之前，您可以手动运行脚本以确保它正常工作：

```bash
python3 /ql/data/scripts/system_monitor.py
```

### 3. 编辑 `crontab`
打开 `crontab` 文件以添加新的定时任务。您可以使用以下命令：

```bash
crontab -e
```

### 4. 添加定时任务
在 `crontab` 文件中，添加一行以定义任务的执行频率。以下是一些示例：

- 每小时执行一次：
    ```bash
    0 * * * * /usr/bin/python3 /ql/data/scripts/system_monitor.py
    ```
  
- 每天中午12点执行：
    ```bash
    0 12 * * * /usr/bin/python3 /ql/data/scripts/system_monitor.py
    ```

- 每5分钟执行一次：
    ```bash
    */5 * * * * /usr/bin/python3 /ql/data/scripts/system_monitor.py
    ```

请根据您的需求选择适合的时间配置。

### 5. 保存并退出
保存 `crontab` 文件并退出编辑器。您的定时任务现在应该已成功添加。

### 6. 检查任务是否正常运行
您可以通过查看 `cron` 日志来检查任务是否按预期执行。在许多系统中，`cron` 日志位于 `/var/log/syslog` 或 `/var/log/cron` 中。您可以使用以下命令查看日志：

```bash
grep CRON /var/log/syslog
```

### 7. 输出日志
如果您希望脚本的输出被记录到文件中，可以修改 `crontab` 任务如下：

```bash
0 * * * * /usr/bin/python3 /ql/data/scripts/system_monitor.py >> /ql/data/scripts/system_monitor.log 2>&1
```

这将把标准输出和错误输出都重定向到 `system_monitor.log` 文件中，方便后续查看。

通过以上步骤，您可以使用 `cron` 在系统环境中定时执行您的脚本。
