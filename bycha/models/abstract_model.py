import logging
logger = logging.getLogger(__name__)

import torch
import torch.nn as nn

from bycha.utils.runtime import Environment as E
from bycha.utils.tensor import save_ckpt
from bycha.utils.io import UniIO


class AbstractModel(nn.Module):
    """
    AbstractModel is abstract class for models defining inferfaces.

    Args:
        path: path to restore checkpoints
    """

    def __init__(self, path=None):
        super().__init__()
        self._path = path

        self._mode = 'train'
        self._states = {}

    def build(self, *args, **kwargs):
        """
        Build neural model with task instances.
        It wraps `_build` function with restoring and moving to cuda.
        """
        self._build(*args, **kwargs)
        logger.info('neural network architecture\n{}'.format([_ for _ in self.children()]))
        logger.info('parameter size: {}'.format(sum(p.numel() for p in self.parameters())))

        e = E()
        if self._path is not None:
            logger.info(f'load model from {self._path}')
            self.load(self._path, e.device)

        if e.device.startswith('cuda'):
            logger.info('move model to {}'.format(e.device))
            self.cuda(e.device)

    def _build(self, *args, **kwargs):
        """
        Build neural model with task instances.
        """
        raise NotImplementedError

    def forward(self, *input):
        """
        Compute output with neural input

        Args:
            *input: neural inputs
        """
        raise NotImplementedError

    def load(self, path, device, strict=False):
        """
        Load model from path and move model to device.

        Args:
            path: path to restore model
            device: running device
            strict: load model strictly
        """
        with UniIO(path, 'rb') as fin:
            state_dict = torch.load(fin, map_location=device)
            mismatched = self.load_state_dict(state_dict['model'] if 'model' in state_dict else state_dict, strict=strict)

        if not strict:
            logger.info("keys IN this model but NOT IN loaded model >>> ")
            if len(mismatched.missing_keys) > 0:
                for ele in mismatched.missing_keys:
                    logger.info(f"    - {ele}")
            else:
                logger.info("    - None")
            logger.info("keys NOT IN this model but IN loaded model >>> ")
            if len(mismatched.unexpected_keys) > 0:
                for ele in mismatched.unexpected_keys:
                    logger.info(f"    - {ele}")
            else:
                logger.info("    - None")

    def save(self, path):
        """
        Save model to path.

        Args:
            path: path to save model
        """
        save_ckpt({'model': self.state_dict()}, path)

    def update_states(self, *args, **kwargs):
        """
        Update internal networks states.
        """
        raise NotImplementedError

    @property
    def states(self):
        return self._states

    def reset(self, *args, **kwargs):
        """
        Reset neural model states.
        """
        pass

    def is_pretrained(self):
        return self._path is not None
