import os
import subprocess
from pyngrok import ngrok

try:
    from google.colab import drive

    colab_env = True
except ImportError:
    colab_env = False

EXTENSIONS = ["ms-python.python", "jithurjacob.nbpreviewer","vscodevim.vim"]
import sys


class Connector:
    def __init__(self, port,option,args):
        self.port = port
        self.option = option
        self.args = args
        self.connection = None

    def connect(self):
        if self.option == "ngrok":
            url = ngrok.connect(port=self.port, options={"bind_tls": True})
            print(f"Code Server can be accessed on: {url}")
        elif self.option == "localtunnel":
            self.connection = subprocess.Popen(
                "lt --port 10000 " + f"{self.args}",
                stdout=subprocess.PIPE,
                shell=True)

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
                print(line.rstrip().decode('utf-8'))
                break


class ColabCode:
    def __init__(self, port=10000, password=None, mount_drive=False,
                 option="localtunnel", add_extensions=None,args='',tunnel_args=''):
        self.port = port
        self.args = args
        self._install_localtunnel()
        print(option)
        self.connection = Connector(self.port, option,args=tunnel_args)
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
            if ext.startswith('http'):
                d = subprocess.call(f'wget {ext}',shell=True)
                ext = os.path.basename(d)
                if d:
                    continue
            subprocess.run(["code-server", "--install-extension", f"{ext}"])

    def _start_server(self):
        self.connection.disconnect()
        self.connection.connect()

    def _run_code(self):
        os.system(f"fuser -n tcp -k {self.port}")
        if self._mount and colab_env:
            drive.mount("/content/drive")
        if self.password:
            code_cmd = f"PASSWORD={self.password} code-server --port {self.port}" + self.args
        else:
            code_cmd = f"code-server --port {self.port} --auth none " + self.args
        with subprocess.Popen(
                [code_cmd],
                shell=True,
                stdout=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True,
        ) as proc:
            for line in proc.stdout:
                print(line, end="")
