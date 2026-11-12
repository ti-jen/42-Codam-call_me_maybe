from llm_sdk import Small_LLM_Model
from pydantic import BaseModel, ConfigDict
from .json_convert import DefinedFunction, CallingFunction, ArgType
from torch import tensor
from typing import Any
import time
import threading
import re

additions = [
    (['asterisks'], '*'),
    (['"question"'], '?'),
    (['exclamation'], '!'),
    (['dashes, dash'], '-'),
    (['colons, colon'], ':'),
    (['dots, dot'], '.'),
    (['vowel', 'vowels'], '([aeiouAEIOU])'),
    (['numb', 'number', 'numbers', 'digits'], '([0123456789])'),
    (['char', 'character', 'characters', 'letters'], '([a-zA-Z])'),
    (['uppercase', 'uppercases', 'upper'], '([A-Z])'),
    (['lowercase', 'lowercases', 'lower'], '([a-z])'),
    (['underscores', 'underscore'], '_'),
    (['consonant', 'consonants'],
     '([bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ])')
]


class OutputFunction(BaseModel):
    prompt: str
    name: str
    parameters: dict[str, Any]


def is_float(str: str) -> bool:
    "checks if the str is a float value and returns a bool"
    if str == "-":
        return True
    try:
        float(str)
        return True
    except ValueError:
        return False


def split_line(str: str) -> list[str]:
    "splits the line in a list that the llm can choose from as  the paramter"
    base = [x for x in re.split(r'[ ,.]+', str) if not is_float(x)]
    resultA = re.findall(r'"(.*?)"', str)
    resultB = re.findall(r"'(.*?)'", str)
    resultC = [item.strip() for item in str.split(':')]
    numbers = re.findall(r'-?\d*[.,]?\d+', str)
    base += resultA + resultB + resultC
    for x in "'\"":
        for p in range(len(base)):
            base[p] = base[p].replace(x, "")
    for keywords, patern in additions:
        for keyword in keywords:
            if keyword in base:
                base.append(patern)
    return list(dict.fromkeys(base)) + numbers


class LLmcustom(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    func_def: dict[str, DefinedFunction]
    model: Small_LLM_Model = Small_LLM_Model()
    loading: bool = True

    def spinner(self, text: str) -> None:
        """imports a str and makes it a loading text
        with a spinning line at the start"""
        while self.loading:
            for frame in ["|", "/", "-", "\\"]:
                print(f"\r{frame} {text}", end="\r", flush=True)
                time.sleep(0.1)

    def set_anwser_type(self, anwser: str, type: str) -> float | int | str:
        if (is_float(anwser) and
                ArgType(type) == ArgType.NUMBER):
            return float(anwser)
        elif (is_float(anwser) and
                ArgType(type) == ArgType.INTEGER):
            return int(anwser)
        else:
            return anwser

    def get_func(self, promt: CallingFunction) -> str | None:
        "gets the function name for the givin promt"
        des = f"user's request={promt.promt}\n"
        des += "function options:\n"
        for x in self.func_def:
            des += (f"function_name={self.func_def[x].name}, "
                    f"function_description={self.func_def[x].description}\n")
        des += "the single function that best matches the user's request="

        input_ids = self.model.encode(des)[0].tolist()
        anwser: list[int] = []
        logits = self.model.get_logits_from_input_ids(input_ids)
        wrongs = 0
        while wrongs < 500:
            next_id = max(range(len(logits)), key=lambda i: logits[i])
            test = anwser.copy()
            test.append(next_id)
            valid = False
            for p in self.func_def:
                if self.func_def[p].name.startswith(self.model.decode(test)):
                    valid = True
                    break
            if self.model.decode(tensor(next_id)) == "\n":
                break
            if not valid:
                wrongs += 1
                logits[next_id] = float('-inf')
            else:
                input_ids.append(next_id)
                anwser.append(next_id)
                logits = self.model.get_logits_from_input_ids(input_ids)
            if len(self.model.decode(tensor(next_id))) == 0:
                break
        if wrongs >= 500:
            return None
        return str(self.model.decode(tensor(anwser)))

    def get_par(self, promt: CallingFunction,
                func: DefinedFunction) -> dict[str, str]:
        "gets the paramter inputs for the givin promt and funcion"
        result: dict[str, Any] = {}
        options = split_line(promt.promt)
        des = f"user's request={promt.promt}\n"
        des += (f"function used for request={func.name}, "
                f"function description={func.description}\n")
        des += "format paramter:\n"
        for p in func.parameters:
            des += (f"parameter_{p}_"
                    f"input=<single input that best matches the request>\n")
        des += "input paramter:\n"
        for x in func.parameters:
            des += f"parameter_{x}_input="
            anwser: list[int] = []
            input_ids = self.model.encode(des)[0].tolist()
            logits = self.model.get_logits_from_input_ids(input_ids)
            wrongs = 0
            while wrongs < 500:
                next_id = max(range(len(logits)), key=lambda i: logits[i])
                test = self.model.decode(anwser + [next_id])
                test = test.lstrip()
                if (len(self.model.decode(anwser)) != 0 and
                        "\n" in self.model.decode(tensor(next_id))):
                    break
                valid = [word for word in options if
                         word.startswith(test)]
                if (valid and len(test) != 0 and
                    ((ArgType.NUMBER ==
                      ArgType(func.parameters[x]["type"].value) and
                      is_float(test)
                      ) or
                     (ArgType.STRING ==
                      ArgType(func.parameters[x]["type"].value) and not
                     is_float(test)
                      ) or
                     (ArgType.INTEGER ==
                      ArgType(func.parameters[x]["type"].value) and
                     is_float(test)
                      )
                     )):
                    input_ids.append(next_id)
                    anwser.append(next_id)
                    logits = self.model.get_logits_from_input_ids(input_ids)
                    if len(valid) == 1:
                        break
                else:
                    logits[next_id] = float('-inf')
                    wrongs += 1
            if wrongs >= 500:
                result[x] = None
                des += "None\n"
            elif len(valid) == 1:
                result[x] = self.set_anwser_type(valid[0],
                                                 func.parameters[x]
                                                 ["type"].value)
                options.remove(valid[0])
                des += f"{result[x]}\n"
            else:
                result[x] = self.set_anwser_type(self.model.decode(anwser),
                                                 func.parameters[x]
                                                 ["type"].value)
                des += f"{result[x]}\n"
        return result

    def get_ouput(self, promt: CallingFunction) -> OutputFunction:
        "generates the promt and paramters with the giving visuals"
        print(f"\033[33m[{promt.promt}]\033[0m")
        self.loading = True
        thread = threading.Thread(target=self.spinner,
                                  args=("choosing function...",))
        thread.start()
        func = self.get_func(promt)
        self.loading = False
        thread.join()
        print(f"function: {func}            ")
        if func is None:
            return OutputFunction(prompt=promt.promt,
                                  name="null",
                                  parameters={"error": None})
        self.loading = True
        thread = threading.Thread(target=self.spinner,
                                  args=("choosing parameters...",))
        thread.start()
        parm = self.get_par(promt, self.func_def[func])
        self.loading = False
        thread.join()
        print(f"parameters: {parm}          \n")
        return OutputFunction(prompt=promt.promt,
                              name=func,
                              parameters=parm)
