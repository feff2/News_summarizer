import numpy as np
from pytriton.decorators import batch
from pytriton.model_config import DynamicBatcher, ModelConfig, Tensor
from pytriton.triton import Triton, TritonConfig
from FlagEmbedding import BGEM3FlagModel

class TritonServer:
    def __init__(self, model: BGEM3FlagModel, settings, logger):
        self.triton_config = TritonConfig(metrics_config=["summary_latencies=true"])
        self.model = model 
        self.logger = logger
        self.settings = settings

    @batch
    def _biecoder_infer_fn(self, text: np.ndarray) -> dict[str, np.ndarray]:
        sequence = [np.char.decode(c.astype("bytes"), "utf-8").item() for c in text]

        embedding = self.model.encode(sequence)['dense_vecs']
        return {"embeding": embedding}
    
    def setup_embeder(self, triton):
        self.logger.info(
            f"Start triton inference MAX_BATCH_SIZE={self.settings.MAX_BATCH_SIZE}, "
            f"MAX_QUEUE_DELAY_MICROSECONDS={self.settings.MAX_QUEUE_DELAY_MICROSECONDS}"
        )
        
        triton.bind(
            model_name=self.settings.MODEL_NAME,
            infer_func=self._biecoder_infer_fn,
            inputs=[
                Tensor(name="text", dtype=np.bytes_, shape=(1,)),
            ],
            outputs=[
                Tensor(name="embeding", dtype=np.float32, shape=(1,)),
            ],
            config=ModelConfig(
                batching=True,
                max_batch_size=self.settings.MAX_BATCH_SIZE,
                batcher=DynamicBatcher(
                    preferred_batch_size=[2, 4, 8],
                    max_queue_delay_microseconds=self.settings.MAX_QUEUE_DELAY_MICROSECONDS,
                ),
            ),
            strict=True,
        )
    
    
    def run(self):
        with Triton(config=self.triton_config) as triton:
            self.setup_embeder(triton)        
            self.logger.info("Serving inference")
            self.logger.info(
                f"USE_GPU={self.settings.USE_GPU}, GPU_INDEX={self.settings.GPU_INDEX}"
            )
            
            triton.serve()