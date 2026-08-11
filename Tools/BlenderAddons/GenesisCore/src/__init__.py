import bpy

reg_modules = [
    "preference",
    "i18n",
    "server",
    "timer",
    "client",
    "operator",
    "props",
    "ui",
    "utils",
    "watcher",
]

reg, unreg = bpy.utils.register_submodule_factory(__package__, reg_modules)


class PkgInstaller:
    source = [
        "https://mirrors.aliyun.com/pypi/simple/",
        "https://pypi.tuna.tsinghua.edu.cn/simple/",
        "https://pypi.mirrors.ustc.edu.cn/simple/",
        "https://pypi.python.org/simple/",
        "https://pypi.org/simple",
    ]
    fast_url = ""

    @staticmethod
    def select_pip_source():
        if not PkgInstaller.fast_url:
            import requests

            t, PkgInstaller.fast_url = 999, PkgInstaller.source[0]
            for url in PkgInstaller.source:
                try:
                    tping = requests.get(url, timeout=1).elapsed.total_seconds()
                except Exception:
                    continue
                if tping < 0.1:
                    PkgInstaller.fast_url = url
                    break
                if tping < t:
                    t, PkgInstaller.fast_url = tping, url
        return PkgInstaller.fast_url

    @staticmethod
    def is_installed(package):
        import importlib

        try:
            return importlib.import_module(package)
        except ModuleNotFoundError:
            return False

    @staticmethod
    def prepare_pip():
        import ensurepip

        if PkgInstaller.is_installed("pip"):
            return True
        try:
            ensurepip.bootstrap()
            return True
        except BaseException:
            ...
        return False

    @staticmethod
    def try_install(*packages):
        if not PkgInstaller.prepare_pip():
            return False
        need = [pkg for pkg in packages if not PkgInstaller.is_installed(pkg)]
        from pip._internal import main

        if need:
            url = PkgInstaller.select_pip_source()
        for pkg in need:
            try:
                from urllib.parse import urlparse

                site = urlparse(url)
                # 避免build
                command = ["install", pkg, "-i", url, "--prefer-binary"]
                command.append("--trusted-host")
                command.append(site.netloc)
                main(command)
                if not PkgInstaller.is_installed(pkg):
                    return False
            except Exception:
                return False
        return True


# Registration functions
def register():
    PkgInstaller.try_install(
        "mcp",
        "websockets",
    )
    reg()


def unregister():
    unreg()
