from pydantic_core import PydanticCustomError
from pydantic import BaseModel, model_validator
import json
from typing import Self
from enum import Enum


class ArgType(Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    NULL = "null"


class CallingFunction(BaseModel):
    promt: str


class DefinedFunction(BaseModel):
    name: str
    description: str
    parameters: dict[str, dict[str, ArgType]]
    returns: dict[str, ArgType]

    @model_validator(mode="after")
    def validate_dict(self) -> Self:
        for x in self.parameters:
            if len(self.parameters[x]) != 1:
                raise ValueError(f"wrong amount of parameter arguments in {x}",
                                 f"suspected 1 got: {self.parameters[x]}")
            if "type" not in self.parameters[x]:
                raise PydanticCustomError("paramter_error",
                                          f"missing key='type' got: {x}")

        for x in self.returns:
            if len(self.returns) != 1:
                raise ValueError("wrong amount of argument in 'return'"
                                 f"suspected 1 got: {self.returns}")
            if "type" not in self.returns:
                raise PydanticCustomError("returns_error",
                                          f"missing key='type' got: {x}")
        return self


def create_def_func_list(s: str) -> list[DefinedFunction]:
    def_func = []
    try:
        with open(s, "r") as f:
            try:
                func = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError("functions_definition: "
                                 f"{e.msg} at line {e.lineno}")
    except OSError as e:
        raise OSError(f"functions_definition: {e}")
    if type(func) is not list:
        raise ValueError("function_define is ",
                         "wrong type excpected 'list[dict]'")
    if len(func) <= 0:
        raise ValueError("function_define list is empty")
    for x in func:
        try:
            def_func.append(DefinedFunction(name=x["name"],
                                            description=x["description"],
                                            parameters=x["parameters"],
                                            returns=x["returns"]
                                            ))
        except KeyError as e:
            raise KeyError(f"missing key={e} got: '{x}'")

    return def_func


def create_cal_func_list(s: str) -> list[CallingFunction]:
    cal_func = []
    try:
        with open(s, "r") as f:
            try:
                func = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"functions_calling: "
                                 f"{e.msg} at line {e.lineno}")
    except OSError as e:
        raise OSError(f"functions_calling: {e}")
    if type(func) is not list:
        raise ValueError("function_define is ",
                         "wrong type excpected 'list[dict]'")
    if len(func) <= 0:
        raise ValueError("function_calling list is empty")
    for x in func:
        try:
            if len(x) != 1:
                raise KeyError(f"dict list must be lenght 1 got: '{x}'")
            cal_func.append(CallingFunction(promt=x["prompt"]))
        except KeyError:
            raise KeyError(f"suspected key='prompt' got: '{x}'")
    return cal_func


if __name__ == "__main__":
    try:
        test = create_cal_func_list("data/input/function_calling_tests.json")
        work = create_def_func_list("data/input/functions_definition.json")
        for x in test:
            print(x)
        for a in work:
            print(a)
    except Exception as e:
        print(f"[ERROR]{e}")
