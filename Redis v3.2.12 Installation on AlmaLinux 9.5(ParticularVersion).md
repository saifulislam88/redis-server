## Redis v3.2.12 Installation on AlmaLinux 9.5(Particular Version)
🚀TkTp-Memory

### Prerequisites:
- Redis version: 3.2.12
- AlmaLinux 9.5 or similar OS.

### Step-by-Step Redis Installation

#### 1. Remove Previous Redis Versions:
```bash
sudo yum remove redis
```

#### 2. Install Required Development Tools:
```bash
sudo yum groupinstall -y "Development Tools"
sudo dnf install -y gcc make jemalloc-devel tar wget
sudo yum install -y gcc make jemalloc
```

#### 3. Download and Install Redis 3.2.12:
```bash
cd /usr/local/src
sudo curl -O http://download.redis.io/releases/redis-3.2.12.tar.gz
sudo tar xzf redis-3.2.12.tar.gz
cd redis-3.2.12
sudo make MALLOC=jemalloc
make MALLOC=jemalloc
sudo make install
```

#### 4. Verify Redis Installation:
```bash
/usr/local/bin/redis-server --version
/usr/local/bin/redis-cli --version
```

#### 5. Configure Redis:

1. **Create Necessary Directories:**
   ```bash
   sudo mkdir -p /etc/redis /var/lib/redis
   sudo chown -R redis:redis /var/lib/redis /etc/redis /var/log/redis.log
   ```

2. **Copy Redis Configuration:**
   ```bash
   sudo cp /usr/local/src/redis-3.2.12/redis.conf /etc/redis/redis.conf
   sudo chmod 644 /etc/redis/redis.conf
   ```

3. **Update Redis Configuration:**
   ```bash
   sudo sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf  #Configure Redis to use systemd for supervision, enabling better process management 
   sudo sed -i 's/^daemonize no/daemonize yes/' /etc/redis/redis.conf        #Start Redis in the background (daemon mode) so it runs as a background service
   sudo sed -i 's/^dir .\//dir \/var\/lib\/redis\//' /etc/redis/redis.conf   #Change the default Redis working directory to /var/lib/redis for storing data files
   ```

#### 6. Start and Stop Redis Manually:
```bash
/usr/local/bin/redis-server /etc/redis/redis.conf   # Start Redis Server
/usr/local/bin/redis-cli shutdown                  # Stop Redis Server
```

#### 7. Create Symlinks for Easy Access:
```bash
sudo ln -s /usr/local/bin/redis-cli /usr/bin/redis-cli
sudo ln -s /usr/local/bin/redis-server /usr/bin/redis-server
```

#### 8. Test Redis CLI and Server:
```bash
sudo redis-cli
sudo redis-server /etc/redis/redis.conf
sudo redis-cli shutdown
```

#### 9. Configure Redis as a Systemd Service:

1. **Create the systemd Service File:**
   Edit `/etc/systemd/system/redis.service`:
   ```bash
   sudo vim /etc/systemd/system/redis.service
   ```
   Add the following content:
   ```ini
   [Unit]
   Description=Redis In-Memory Data Store
   Documentation=man:redis-server(1)
   After=network.target

   [Service]
   Type=notify
   ExecStartPre=/bin/mkdir -p /run/redis
   ExecStartPre=/bin/chown redis:redis /run/redis
   ExecStart=/usr/local/bin/redis-server /etc/redis/redis.conf --supervised systemd
   ExecStop=/usr/local/bin/redis-cli shutdown
   PIDFile=/run/redis/redis.pid
   User=redis
   Group=redis
   RuntimeDirectory=redis
   RuntimeDirectoryMode=0755
   TimeoutStopSec=5
   Restart=always
   LimitNOFILE=10032

   [Install]
   WantedBy=multi-user.target
   ```

2. **Reload and Enable Redis Service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart redis
   sudo systemctl enable redis
   sudo systemctl status redis
   ```

3. **Stop and Verify Redis:**
   ```bash
   sudo systemctl stop redis
   reboot
   sudo systemctl status redis
   sudo redis-cli --version
   sudo redis-server --version
   sudo redis-cli
   ```

