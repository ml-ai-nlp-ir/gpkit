"Scripts to parse and collate substitutions"
from collections import Iterable
import numpy as np
from ..small_scripts import is_sweepvar


def parse_subs(varkeys, substitutions, sweeps=False):
    "Seperates subs into constants, sweeps linkedsweeps actually present."
    varkeys.update_keymap()
    constants, sweep, linkedsweep = {}, None, None
    if sweeps:
        sweep, linkedsweep = {}, {}
    if hasattr(substitutions, "keymap"):
        for var in varkeys.keymap:
            if dict.__contains__(substitutions, var):
                sub = dict.__getitem__(substitutions, var)
                keys = varkeys.keymap[var]
                append_sub(sub, keys, constants, sweep, linkedsweep)
    else:
        for var in substitutions:
            key = getattr(var, "key", var)
            if key in varkeys.keymap:
                sub, keys = substitutions[var], varkeys.keymap[key]
                append_sub(sub, keys, constants, sweep, linkedsweep)
    if sweeps:
        return constants, sweep, linkedsweep
    else:
        return constants


def append_sub(sub, keys, constants, sweep=None, linkedsweep=None):
    "Appends sub to constants, sweep, or linkedsweep."
    sweepsub = is_sweepvar(sub)
    if sweepsub and sweep is None and linkedsweep is None:
        return
    if sweepsub:
        _, sub = sub  # _ catches the "sweep" marker
    for key in keys:
        if not key.shape or not isinstance(sub, Iterable):
            value = sub
        else:
            sub = np.array(sub) if not hasattr(sub, "shape") else sub
            if key.shape == sub.shape:
                value = sub[key.idx]
                if is_sweepvar(value):
                    _, value = value
                    sweepsub = True
            elif sweepsub:
                try:
                    np.broadcast(sub, np.empty(key.shape))
                except ValueError:
                    raise ValueError("cannot sweep variable %s of shape %s"
                                     " with array of shape %s; array shape"
                                     " must either be %s or %s" %
                                     (key.str_without("model"), key.shape,
                                      sub.shape,
                                      key.shape, ("N",)+key.shape))
                idx = (slice(None),)+key.descr["idx"]
                value = sub[idx]
            else:
                raise ValueError("cannot substitute array of shape %s for"
                                 " variable %s of shape %s." %
                                 (sub.shape, key.str_without("model"),
                                  key.shape))

        if hasattr(value, "__call__") and not hasattr(value, "key"):
            linkedsweep[key] = value
        elif sweepsub:
            sweep[key] = value
        elif not isinstance(value, np.float) or not np.isnan(value):
            constants[key] = value
