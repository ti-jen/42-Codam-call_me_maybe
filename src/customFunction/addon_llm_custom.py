from pydantic import BaseModel, ConfigDict
from .json_convert import DefinedFunction, CallingFunction
from llm_sdk import Small_LLM_Model
from typing import Any


class OutputFunction(BaseModel):
    prompt: str
    name: str
    parameters: dict[str, Any]


def is_float(str: str) -> bool:
    try:
        float(str)
        return True
    except ValueError:
        return False


class LLmcustom(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    func_def: dict[str, DefinedFunction]
    model: Small_LLM_Model = Small_LLM_Model()

    def get_func(self, promt: CallingFunction) -> str:
        des = """
        You are a function selector.
        Select the single function that best matches the user's request.

        Use the function descriptions to determine the intended action.
        Return only the selected function name.
        """
        des += f"user:{promt}\n"
        for x in self.func_def:
            des += (f"function_name={self.func_def[x].name}, "
                    "function_description={self.func_def[x].description}\n")
        des += "answer:\n"

        input_ids = self.model.encode(des)[0].tolist()
        anwser: list[int] = []
        logits = self.model.get_logits_from_input_ids(input_ids)
        while 1:
            next_id = max(range(len(logits)), key=lambda i: logits[i])
            test = anwser.copy()
            test.append(next_id)
            valid = False
            for p in self.func_def:
                if self.func_def[p].name.startswith(self.model.decode(test)):
                    valid = True
                    break
            if len(self.model.decode(next_id)) == 0:
                break
            if not valid:
                logits[next_id] = float('-inf')
            else:
                input_ids.append(next_id)
                anwser.append(next_id)
                logits = self.model.get_logits_from_input_ids(input_ids)
            if len(self.model.decode(next_id)) == 0:
                break
        return str(self.model.decode(anwser))

    def get_par(self, promt: CallingFunction,
                func: DefinedFunction) -> dict[str, str]:
        result = {}
        des = f"user's request={promt.promt}\n"
        des += (f"function used for request={func.name}, "
                f"function description={func.description}\n")
        des += "format paramter:\n"
        for p in func.parameters:
            des += (f"parameter {p} "
                    f"input=<{func.parameters[p]["type"].value}>, ")
        des += "input paramter:\n"
        for x in func.parameters:
            des += f"parameter {x} input="
            anwser: list[int] = []
            input_ids = self.model.encode(des)[0].tolist()
            logits = self.model.get_logits_from_input_ids(input_ids)
            while 1:
                next_id = max(range(len(logits)), key=lambda i: logits[i])
                test = anwser.copy()
                test.append(next_id)
                if (len(anwser) != 0 and
                        self.model.decode(next_id) == ","):
                    break
                if (self.model.decode(test) in promt.promt and
                    (func.parameters[p]["type"].value == "number" and
                     is_float(self.model.decode(test)) or
                    ((func.parameters[p]["type"].value == "string" and
                      not is_float(self.model.decode(test))))
                        and not self.model.decode(test).startswith(" "))):
                    input_ids.append(next_id)
                    anwser.append(next_id)
                    logits = self.model.get_logits_from_input_ids(input_ids)
                else:
                    logits[next_id] = float('-inf')
            result[x] = self.model.decode(anwser)
            des += f"{self.model.decode(anwser)}, "
        return result

    def get_ouput(self, promt: CallingFunction) -> OutputFunction:
        func = self.get_func(promt)
        parm = self.get_par(promt, self.func_def[func])
        return OutputFunction(prompt=promt.promt,
                              name=func,
                              parameters=parm)
