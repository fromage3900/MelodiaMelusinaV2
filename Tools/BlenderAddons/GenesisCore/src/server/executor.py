import functools
import logging
import json
from ..timer import Timer
from .utils import rounding_dumps
from ..logger import getLogger

logger = getLogger("BlenderExecutor")


class BlenderExecutor:
    instance = None

    @classmethod
    def get(cls) -> "BlenderExecutor":
        return cls.instance or cls()

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def send_function_call(self, func, params):
        name = func.__name__
        command = {"func": func, "name": name,"params": params or {}}

        logger.info(f"收到命令: {name} 参数: {params}")
        response = Timer.wait_run_with_context(self.execute_function)(command)
        logger.info(f"执行状态: {response.get('status', 'unknown')}")

        if response.get("status") == "error":
            logger.error(f"Blender error: {response.get('message')}")
            raise Exception(response.get("message", "Unknown error from Blender"))
        result_str = rounding_dumps(response.get("result", {}), ensure_ascii=False)
        print("\n--------------------------------", flush=True)
        print(f"\t所选工具: {name}")
        print(f"\t执行结果: {result_str}")
        print("--------------------------------\n", flush=True)
        return result_str

    def execute_function(self, command):
        func = command.get("func")
        name = command.get("name") or func.__name__
        try:
            params = command.get("params", {})
            logger.info(f"命令执行: {name} 参数: {params}")
            result = func(**params)
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Error execute {name}: {str(e)}")
            return {"status": "error", "message": str(e)}
