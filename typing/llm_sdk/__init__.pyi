import torch


class Small_LLM_Model:
    def encode(self, text: str) -> torch.Tensor:
        pass

    def decode(self, ids: torch.Tensor | list[int]) -> str:
        pass

    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        pass
