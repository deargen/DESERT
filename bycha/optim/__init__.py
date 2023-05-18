from copy import deepcopy
from inspect import getfullargspec
import importlib
import json
import os
import logging
logger = logging.getLogger(__name__)

from torch.optim.optimizer import Optimizer

from bycha.optim.optimizer import Optimizer
from bycha.utils.rate_schedulers import create_rate_scheduler
from bycha.utils.runtime import Environment
from bycha.utils.registry import setup_registry

register_optim, create_optim, registry = setup_registry('optim', Optimizer, force_extend=False)


def build_optimizer(model, configs, enable_apex=False):
    configs = deepcopy(configs)
    name = configs.pop('class')

    kwargs = {}
    for k, v in configs.items():
        try:
            v = eval(v)
        except:
            pass
        finally:
            kwargs[k] = v
    configs = kwargs

    logger.info('Creating {} class with configs \n{}\n'.format(name,
                                                               json.dumps(configs, indent=4, sort_keys=True)))

    lr = configs.pop('lr')
    lr_scheduler = create_rate_scheduler(lr)
    lr_scheduler.build()

    args = getfullargspec(Optimizer).args[4:]
    optimizer_kwargs = {}
    for key in args:
        if key in configs:
            optimizer_kwargs[key] = configs.pop(key)

    if name.lower() in registry:
        cls = registry[name.lower()]
    else:
        import importlib
        mod = importlib.import_module('torch.optim')
        cls = getattr(mod, name)

    if 'no_decay' in configs:
        named_parameters = model.named_parameters()
        no_decay = configs.pop('no_decay')
        weight_decay = configs.pop('weight_decay')
        grouped_parameters = [
            {'params': [p for n, p in named_parameters if not any(nd in n for nd in no_decay)],
             'weight_decay': weight_decay},
            {'params': [p for n, p in named_parameters if any(nd in n for nd in no_decay)],
             'weight_decay': 0.0}
        ]
    else:
        grouped_parameters = model.parameters()

    optimizer = cls(grouped_parameters, lr=lr_scheduler.rate, **configs)

    env = Environment()
    if env.distributed_world > 1:
        import horovod.torch as hvd
        hvd_kwargs = {}
        if 'update_frequency' in optimizer_kwargs:
            hvd_kwargs['backward_passes_per_step'] = optimizer_kwargs['update_frequency']
        if env.fp16 and not enable_apex:
            hvd_kwargs['compression'] = hvd.Compression.fp16
        optimizer = hvd.DistributedOptimizer(optimizer,
                                             named_parameters=model.named_parameters(),
                                             **hvd_kwargs)
        hvd.broadcast_parameters(model.state_dict(), root_rank=0)
        hvd.broadcast_optimizer_state(optimizer, root_rank=0)

    if enable_apex:
        from apex import amp
        update_frequency = optimizer_kwargs['update_frequency'] if 'update_frequency' in optimizer_kwargs else 1
        model, optimizer = amp.initialize(model, optimizer,
                                          opt_level='O1',
                                          num_losses=update_frequency)
    optimizer_kwargs['enable_apex'] = enable_apex

    optimizer = Optimizer(model=model, optimizer=optimizer, lr_scheduler=lr_scheduler, **optimizer_kwargs)
    return model, optimizer


modules_dir = os.path.dirname(__file__)
for file in os.listdir(modules_dir):
    path = os.path.join(modules_dir, file)
    if (
        not file.startswith('_')
        and not file.startswith('.')
        and (file.endswith('.py') or os.path.isdir(path))
    ):
        module_name = file[:file.find('.py')] if file.endswith('.py') else file
        module = importlib.import_module('bycha.optim.' + module_name)

