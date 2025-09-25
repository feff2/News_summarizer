import torch
from typing import Dict, List, Optional

from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

from ..shared.logger import LoggerWrapper


class LlmClient:
    def __init__(
        self: "LlmClient",
        model_name: str,
        device: torch.device,
        params: Dict,
        system_prompt: str,
    ):
        self.model_name = model_name
        self.model: Optional[LLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self._system_prompt = system_prompt
        self._params = SamplingParams(**params)
        self._device = device 
        self._logger = LoggerWrapper(llm_client)

    def start(self: "LlmClient") -> None:
        self.model = LLM(
            model_name=self.model_name,
            tensor_parallel_size=1,
            swap_space=4, 
            gpu_memory_utilization=0.9,
            max_model_len=4096, 
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

    def _build_and_check_prompt(self: "LlmClient", text: str) -> str:
        if not self.model or not self.tokenizer:
            raise RuntimeError("Модель не инициализирована. Вызовите метод start().")

        prompt_structure = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": text},
        ]

        final_prompt_str = self.tokenizer.apply_chat_template(
            prompt_structure,
            tokenize=False,
            add_generation_prompt=True,
        )

        max_model_len = self.model.llm_engine.model_config.max_model_len
        max_new_tokens = self._params.max_tokens
        current_tokens = len(self.tokenizer.encode(final_prompt_str))

        if current_tokens + max_new_tokens > max_model_len:
            self._logger.warning(
                f"Warning: Промпт ({current_tokens} токенов) + макс. новых токенов ({max_new_tokens}) "
                f"превышает максимальную длину модели ({max_model_len})."
            )

        return final_prompt_str

    def close(self: "LlmClient") -> None:
        if self.model:
            del self.model
        self.model = None
        self.tokenizer = None
        torch.cuda.empty_cache()

    def generate(self: "LlmClient", text: str) -> str:
        if not self.model or not self.tokenizer:
            raise RuntimeError("Модель не инициализирована. Вызовите метод start().")

        final_prompt = self._build_and_check_prompt(text)
        outputs = self.model.generate([final_prompt], self._params)
        generated_text = outputs[0].outputs[0].text.strip()
        
        return generated_text