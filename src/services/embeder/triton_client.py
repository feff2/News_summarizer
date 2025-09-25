from dataclasses import dataclass
from typing import Tuple, List

import torch
import numpy as np
from pytriton.client import AsyncioModelClient


from ..shared.logger import LoggerWrapper


@dataclass(frozen=True)
class InferResultBiEncoder:
    result: np.ndarray


@dataclass(frozen=True)
class InferResultCrossEncoder:
    result: np.ndarray


class TritonClient:
    def __init__(
        self: "TritonClient",
        inference_host: str,
        bi_encoder_port: int,
        inference_timeout_s: int,
        bi_encoder_name: str,
        device: torch.device,
        logger: LoggerWrapper,
    ) -> None:
        self.__inference_host = inference_host
        self.__bi_encoder_port = bi_encoder_port
        self.__inference_timeout_s = inference_timeout_s
        self.__bi_encoder_name = bi_encoder_name
        self.__device = device
        self.logger = logger

    async def encode(
        self: "TritonClient",
        text: str,
    ) -> InferResultBiEncoder:
        sequence = np.array([text])
        sequence = np.char.encode(sequence, "utf-8")

        msg = f"Sequence={str(sequence)}"  # noqa: RUF010
        self.logger.debug(msg)

        result_dict = await self.__bi_encoder_client.infer_sample(
            sequence,
        )

        return InferResultBiEncoder(
            result=result_dict["embeding"].tolist(),
        )


    async def destroy(self: "TritonClient") -> None:
        await self.__bi_encoder_client.close()
        await self.__cross_encoder_client.close()

    def create_model(self: "TritonClient") -> None:
        self.__bi_encoder_client = AsyncioModelClient(
            url=f"{self.__inference_host}:{self.__bi_encoder_port}",
            model_name=self.__bi_encoder_name,
            inference_timeout_s=self.__inference_timeout_s,
        )
        msg = "Bi encoder client started"
        self.logger.info(msg)