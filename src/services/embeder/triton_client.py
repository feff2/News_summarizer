from dataclasses import dataclass
from typing import Tuple, List

import torch
import numpy as np
from pytriton.client import AsyncioModelClient


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
        embeder_port: int,
        inference_timeout_s: int,
        embeder_name: str,
        logger,
    ) -> None:
        self.__inference_host = inference_host
        self.embeder_port = embeder_port
        self.__inference_timeout_s = inference_timeout_s
        self.embeder_name = embeder_name
        self.logger = logger

    async def encode(
        self: "TritonClient",
        text: str,
    ) -> InferResultBiEncoder:
        sequence = np.array([text])
        sequence = np.char.encode(sequence, "utf-8")

        msg = f"Sequence={str(sequence)}"  # noqa: RUF010
        self.logger.debug(msg)

        result_dict = await self.embeder_client.infer_sample(
            sequence,
        )

        return InferResultBiEncoder(
            result=result_dict["embeding"].tolist(),
        )


    async def destroy(self: "TritonClient") -> None:
        await self.embeder_client.close()

    def create_model(self: "TritonClient") -> None:
        self.embeder_client = AsyncioModelClient(
            url=f"{self.__inference_host}:{self.embeder_port}",
            model_name=self.embeder_name,
            inference_timeout_s=self.__inference_timeout_s,
        )
        msg = "Embeder client started"
        self.logger.info(msg)