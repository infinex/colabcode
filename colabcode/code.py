import os
import subprocess
from pyngrok import ngrok

try:
    from google.colab import drive

    colab_env = True
except ImportError:
    colab_env = False

EXTENSIONS = ["ms-python.python", "jithurjacob.nbpreviewer","shan.code-settings-sync","vscodevim.vim"]
import sys


class Connector:
    def __init__(self, port, option="ngrok"):
        self.port = port
        self.option = option
        self.connection = None

    def connect(self):
        if self.option == "ngrok":
            url = ngrok.connect(port=self.port, options={"bind_tls": True})
            print(f"Code Server can be accessed on: {url}")
        elif self.option == "localtunnel":
            self.connection = subprocess.Popen(["lt", "--port", str(10000)],
                                               stdout=subprocess.PIPE)

    def disconnect(self):
        if self.option == "localtunnel":
            try:
                self.connection.kill()
            except:
                pass
        elif self.option == "ngrok":
            active_tunnels = ngrok.get_tunnels()
            for tunnel in active_tunnels:
                public_url = tunnel.public_url
                ngrok.disconnect(public_url)

    def get_url(self):
        if self.option == "localtunnel":
            for line in iter(self.connection.stdout.readline, ''):
                print (line.rstrip())
                break


class ColabCode:
    def __init__(self, port=10000, password=None, mount_drive=False,
                 option="ngrok", add_extensions=None):
        self.port = port
        self._install_localtunnel()
        self.connection = Connector(self.port, option)
        self.password = password
        self._mount = mount_drive
        self._install_code()
        self.extensions = EXTENSIONS
        if add_extensions is not None and add_extensions != []:
            if isinstance(add_extensions, list) and isinstance(
                    add_extensions[0], str):
                self.extensions += add_extensions
            else:
                raise TypeError(
                    "You need to pass a list of string(s) e.g. ['ms-python.python']")
        self._install_extensions()
        self._start_server()
        self.connection.get_url()
        self._run_code()

    def _install_code(self):
        subprocess.run(
            ["wget", "https://code-server.dev/install.sh"],
            stdout=subprocess.PIPE
        )
        subprocess.run(["sh", "install.sh"], stdout=subprocess.PIPE)

    def _install_localtunnel(self):
        subprocess.run(
            ["npm", "install", "-g", "localtunnel"], stdout=subprocess.PIPE
        )

    def _install_extensions(self):
        for ext in self.extensions:
            print(f'Install Extension {ext}')
            subprocess.run(["code-server", "--install-extension", f"{ext}"])

    def _start_server(self):
        self.connection.disconnect()
        self.connection.connect()

    def _run_code(self):
        os.system(f"fuser -n tcp -k {self.port}")
        if self._mount and colab_env:
            drive.mount("/content/drive")
        if self.password:
            code_cmd = f"PASSWORD={self.password} code-server --port {self.port} --disable-telemetry"
        else:
            code_cmd = f"code-server --port {self.port} --auth none --disable-telemetry"
        with subprocess.Popen(
                [code_cmd],
                shell=True,
                stdout=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True,
        ) as proc:
            for line in proc.stdout:
                print(line, end="")
