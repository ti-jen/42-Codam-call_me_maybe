from pydantic import BaseModel, ConfigDict
from .json_convert import DefinedFunction, CallingFunction
from llm_sdk import Small_LLM_Model


class LLmcustom(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    func_def: list[DefinedFunction]
    model: Small_LLM_Model = Small_LLM_Model()

    def out(self, promt: CallingFunction):
        des = """
        You are a function selector.
        Select the single function that best matches the user's request.

        Use the function descriptions to determine the intended action.
        Return only the selected function index number.
        """
        des += f" user:{promt}\n"
        for x in range(len(self.func_def)):
            des += f"index={x}, function_name={self.func_def[x].name}, function_description={self.func_def[x].description}\n"
        des += f"answer:\n"



        input_ids = self.model.encode(des)[0].tolist()
        anwser = []
        for _ in range(1):
            logits = self.model.get_logits_from_input_ids(input_ids)
            next_id = max(range(len(logits)), key=lambda i: logits[i])
            input_ids.append(next_id)
            anwser.append(next_id)

        print(self.func_def[int(self.model.decode(anwser))])
        print(promt)