## **DDoS attacker**

This tool allows you to organize DDoS attacks on both websites and any other types of servers. It sends about **20 MB** of data per second, but the strength still depends on your Internet, such a power of the attack was obtained at a speed of **80-90 Mbit / s**. At the moment, there are **19547** servers in the botnet, but you can add more.
Attacks types:
1. HTTP flood (for sites)
2. SYN flood
3. ICMP-echo flood

There are few attacks yet, but I will improve this tool in the future.

[========]

### How to use?
- First, copy the repository:
`git clone https://github.com/IvanProkshin/DDoS_botnet`

- Go to the directory:
`cd DDoS_botnet-main`

- Run *main.py* as root:
`sudo python main.py`

[========]

### How to add server?
The servers in this botnet are just http proxies, so if you want to add your own servers, just add them to the *botnet.py* like this:
```python
proxies = """104.17.64.1:80
203.30.189.226:80
185.162.229.253:80
104.25.0.173:80
...
...
...
198.41.201.219:80
203.13.32.219:80
203.32.121.239:80
ISERT YOUR PROXIES HERE
""".split("\n")

proxies = list(set(proxies))
print(f"Botnet servers: {len(proxies)}")

```

[========]

### Examples of work:
**Server code: **
```python
from flask import *

app = Flask(__name__)

@app.route("/")
def hello():
    return("Hello, world!<br>"*100)

app.run(host="0.0.0.0", port=80)
```
\** testing was done without a botnet, because the site is on a local network*
Denies service after 7s

##### Have a good use!
