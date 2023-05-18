from typing import List
import logging
logger = logging.getLogger(__name__)

from transformers import AutoTokenizer

from bycha.tokenizers import AbstractTokenizer, register_tokenizer


@register_tokenizer
class HuggingfaceTokenizer(AbstractTokenizer):
    """
    HuggingfaceTokenizer use `huggingface/transformers` lib to do tokenization
    see huggingface/transformers(https://github.com/huggingface/transformers)

    Args:
        tokenizer_name: tokenizer names
    """

    def __init__(self, tokenizer_name, *args, **kwargs):
        super().__init__()
        self._tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, *args, **kwargs)

    @staticmethod
    def learn(*args, **kwargs):
        """
        HuggingfaceTokenizer are used for pretrained model, and is usually directly load from huggingface.
        """
        logger.info('learn vocab not supported for huggingface tokenizer')
        raise NotImplementedError

    def __len__(self):
        return len(self._tokenizer)

    def encode(self, input, *args, **kwargs) -> List[int]:
        """
        Encode a textual sentence into a list of index.
        """
        if len(input) == 1:
            input = input[0]
        return self._tokenizer.encode(input, *args, **kwargs)

    def decode(self, *args, **kwargs) -> str:
        """
        Decode a list of index back into a textual sentence
        """
        return self._tokenizer.decode(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self._tokenizer(*args, **kwargs)

    def token2index(self, *args) -> List[int]:
        """
        Only map a textual sentence to index
        """
        return self.encode(*args)[1:-1]

    @property
    def max_length(self):
        return self._tokenizer.model_max_length

    @property
    def bos(self):
        return self._tokenizer.bos_token_id

    @property
    def eos(self):
        return self._tokenizer.eos_token_id

    @property
    def unk(self):
        return self._tokenizer.unk_token_id

    @property
    def pad(self):
        return self._tokenizer.pad_token_id

    @property
    def bos_token(self):
        return self._tokenizer.bos_token

    @property
    def eos_token(self):
        return self._tokenizer.eos_token

    @property
    def unk_token(self):
        return self._tokenizer.unk_token

    @property
    def pad_token(self):
        return self._tokenizer.pad_token
