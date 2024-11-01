import os
import requests
import random
import time
from bs4 import BeautifulSoup

# Function to fetch proxies from various sources
def fetch_proxies():
    proxies = []

    # Define proxy sources
    sources = [
        {
            "url": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&country=US&timeout=1000&ssl=yes&anonymity=elite",
            "parse_html": False
        },
        {
            "url": "https://www.proxy-list.download/api/v1/get?type=https",
            "parse_html": False
        },
        {
            "url": "https://www.proxy-list.download/api/v1/get?type=http",
            "parse_html": False
        },
        {
            "url": "https://www.free-proxy-list.net/",
            "parse_html": True
        },
        # Add other proxy sources here
    ]

    for source in sources:
        try:
            response = requests.get(source["url"], timeout=10)
            response.raise_for_status()  # Check for HTTP errors
            
            if source["parse_html"]:
                # Parse HTML to extract proxies
                soup = BeautifulSoup(response.text, 'html.parser')
                # Find the table with proxies and extract the text from each cell
                table = soup.find('table', {'id': 'proxylisttable'})
                if table:
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # Skip the header row
                        columns = row.find_all('td')
                        if len(columns) > 1:
                            ip = columns[0].text.strip()
                            port = columns[1].text.strip()
                            proxies.append(f"{ip}:{port}")
            else:
                # Directly handle plain text response
                content = response.text
                proxies.extend(content.splitlines())
        
        except requests.RequestException as e:
            print(f"Error fetching proxies from {source['url']}: {e}")
    
    # Remove duplicates and clean up proxies
    proxies = list(set(proxies))  # Remove duplicates
    proxies = [proxy.strip() for proxy in proxies if proxy.strip()]  # Remove empty entries
    
    if not proxies:
        print("No proxies available.")
    return proxies

# Function to set system proxy (using PowerShell)
def set_system_proxy(proxy):
    try:
        ip, port = proxy.split(':')
        command = f'PowerShell -Command "Set-ItemProperty -Path \'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\' -Name ProxyServer -Value \'{ip}:{port}\'"'
        os.system(command)
        os.system('PowerShell -Command "Set-ItemProperty -Path \'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\' -Name ProxyEnable -Value 1"')
        print(f"Proxy set to {proxy}")
    except Exception as e:
        print(f"Failed to set proxy: {e}")

# Function to reset system proxy to default (disable proxy)
def reset_system_proxy():
    try:
        os.system('PowerShell -Command "Set-ItemProperty -Path \'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\' -Name ProxyEnable -Value 0"')
        print("System proxy reset to default.")
    except Exception as e:
        print(f"Failed to reset proxy: {e}")

# Function to check download speed (using a test file)
def check_proxy_speed(proxy):
    try:
        proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        start = time.time()
        url = "http://ipv4.download.thinkbroadband.com/5MB.zip"
        with requests.get(url, proxies=proxy_dict, stream=True, timeout=10) as response:
            response.raise_for_status()
            total_length = int(response.headers.get('content-length', 0))
            if total_length == 0:  # No content length header
                return float('inf')
            total_downloaded = 0
            for chunk in response.iter_content(chunk_size=1024):
                total_downloaded += len(chunk)
                if total_downloaded >= 1024 * 1024:  # 1 MB download for speed test
                    break
        end = time.time()
        download_time = end - start
        speed_mbps = (1 / download_time) * 8  # Mbps for 1 MB downloaded
        return speed_mbps
    except requests.RequestException:
        return 0  # Return 0 Mbps if proxy fails

# Function to load PAC file (optional - you can add your PAC logic here)
def load_pac_file(pac_file_path):
    print(f"Loading PAC file: {pac_file_path}")
    # Placeholder for custom PAC file logic
    return True

# Function to set PAC file URL on Windows system (using PowerShell)
def set_pac_file_system(pac_url):
    try:
        command = f'PowerShell -Command "Set-ItemProperty -Path \'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\' -Name AutoConfigURL -Value \'{pac_url}\'"'
        os.system(command)
        print(f"PAC file set to {pac_url}")
    except Exception as e:
        print(f"Failed to set PAC file: {e}")

# Main logic to rotate proxies and monitor performance
def rotate_proxies(pac_url=None):
    if pac_url:
        set_pac_file_system(pac_url)  # Set PAC file URL permanently
    
    proxies = fetch_proxies()
    if not proxies:
        print("No proxies available.")
        return

    best_proxy = None
    best_speed = 0

    while True:
        proxy = random.choice(proxies)
        set_system_proxy(proxy)
        
        speed = check_proxy_speed(proxy)
        if speed > 0:
            print(f"Proxy {proxy} speed: {speed:.2f} Mbps")
            if speed > best_speed:
                best_speed = speed
                best_proxy = proxy
            if speed < 1:  # Example threshold, can adjust
                print("Speed too low, switching proxy...")
                continue
        else:
            print(f"Proxy {proxy} failed, switching...")
        
        time.sleep(60)  # Test each proxy every minute

        # Optional: Reset to best proxy if speed is too slow
        if best_proxy:
            set_system_proxy(best_proxy)
            print(f"Reverting to best proxy: {best_proxy} with speed {best_speed:.2f} Mbps")

# Example usage (with PAC file, optional)
pac_url = "https://raw.githubusercontent.com/GorstaksWindows/Pac/main/Pac.pac"  # Optional PAC file URL
rotate_proxies(pac_url=pac_url)
