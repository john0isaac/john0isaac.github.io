---
title: "Using ClientPool to make CacheLib memcached Backend Thread-Safe"
date: 2026-07-25
description: How ClientPool, partial, and nullcontext come together to make CacheLib's memcached backend thread-safe.
categories:
  - Python
tags:
  - CacheLib
  - Memcached
  - Threading
  - Context Managers
  - Open Source
comments: true
authors:
  - john0isaac
---

In [CacheLib #287](https://github.com/pallets-eco/cachelib/pull/287/changes), we needed to use `ClientPool` as
it's the most suitable way to make `CacheLib`'s `memcached` backend thread-safe
following examples from [`pylibmc` documentation](https://sendapatch.se/projects/pylibmc/pooling.html).

Below is code taken from [`pylibmc`](https://github.com/lericson/pylibmc/blob/b6e8452bc92232ce434d9d064a73606a94457f5e/src/pylibmc/pools.py#L11-L53)
library directly that shows the implementation of `ClientPool`.

There are two functions `fill` and `reserve`.<br>
`fill` is a normal function that clones the `memcached` client to multiple slots in a queue.
So every thread can reserve and use one slot at a time using `reserve` which is a context manager.<br>
`reserve` can operate in two modes a blocking and a non-blocking mode:

- In blocking mode if you try to access a reserved slot your code will be blocked (waiting) for that
slot to be available.
- In non-blocking mode if you try to access a reserved slot you will get a
[`queue.Empty`](https://docs.python.org/3/library/queue.html#queue.Empty) exception.

```{.py title="Snippet from pylibmc ClientPool implementation"}
# https://github.com/lericson/pylibmc/blob/b6e8452bc92232ce434d9d064a73606a94457f5e/src/pylibmc/pools.py#L11-L53
from queue import Queue
from contextlib import contextmanager

class ClientPool(Queue):
    """Client pooling helper.

    This is mostly useful in threaded environments, because a client isn't
    thread-safe at all. Instead, what you want to do is have each thread use
    its own client, but you don't want to reconnect these all the time.

    The solution is a pool, and this class is a helper for that.
    """

    def __init__(self, mc=None, n_slots=0):
        Queue.__init__(self, n_slots)
        if mc and n_slots:
            self.fill(mc, n_slots)

    @contextmanager
    def reserve(self, block=False):
        """Context manager for reserving a client from the pool.

        If *block* is given and the pool is exhausted, the pool waits for
        another thread to fill it before returning.
        """
        mc = self.get(block)
        try:
            yield mc
        finally:
            self.put(mc)

    def fill(self, mc, n_slots):
        """Fill *n_slots* of the pool with clones of *mc*."""
        for i in range(n_slots):
            self.put(mc.clone())

class MemcachedClientMock:
    def clone(self):
        return self

    def __call__(self, a, b):
        return a + b

mc = MemcachedClientMock()

pool = ClientPool(mc, n_slots=2)

# Using blocking reserve waits for a slot to be available
# Pyodide does not support threading, so the real code will not work in the browser.
# A fake example is shown below to demonstrate the usage of blocking reserve.
print("Using blocking reserve waits for a slot to be available:")
import time

with pool.reserve(block=False) as client1:
    print("Using 1st client")
    print(client1(1, 2))
    with pool.reserve(block=False) as client2:
        print("Using 2nd client")
        print(client2(2, 2))
        start = time.time()
        time.sleep(2)

    with pool.reserve(block=True) as client3:
        elapsed = time.time() - start
        print(f"Got a client after waiting {elapsed:.2f}s, as a real blocking caller would have")
        print(client3(3, 2))

print("Using non-blocking reserve throws error:")
with pool.reserve(block=False) as client1:
    print("Using 1st client")
    print(client1(1, 2))
    with pool.reserve(block=False) as client2:
        print("Using 2nd client")
        print(client2(2, 2))
        try:
            with pool.reserve(block=False) as client3:
                pass
        except Exception as e:
            print("Using 3rd client throws Queue.Empty error")
            raise e
```

Every time we use a client pool we need to send the `block=True` or `block=False` parameter and this is where
[`partial`](https://docs.python.org/3/library/functools.html#functools.partial) from
[`functools`](https://docs.python.org/3/library/functools.html) can be a useful thing to use.

```{.py title="Using partial to partially call a function"}
from queue import Queue
from contextlib import contextmanager
from functools import partial

class ClientPool(Queue):
    """Client pooling helper."""

    def __init__(self, mc=None, n_slots=0):
        Queue.__init__(self, n_slots)
        if mc and n_slots:
            self.fill(mc, n_slots)

    @contextmanager
    def reserve(self, block=False):
        """Context manager for reserving a client from the pool.

        If *block* is given and the pool is exhausted, the pool waits for
        another thread to fill it before returning.
        """
        mc = self.get(block)
        try:
            yield mc
        finally:
            self.put(mc)

    def fill(self, mc, n_slots):
        """Fill *n_slots* of the pool with clones of *mc*."""
        for i in range(n_slots):
            self.put(mc.clone())

class MemcachedClientMock:
    def clone(self):
        return self

    def __call__(self, a, b):
        return a + b

mc = MemcachedClientMock()

pool = ClientPool(mc, n_slots=2)

client_context = partial(pool.reserve, block=True)

with client_context() as client:
    print(client(1, 2))
```

Notice that we use `partial` to initialize fresh instances from the
context manager and not the result of `pool.reserve(block=True)` directly.
A function decorated with
[`@contextmanager`](https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager)
is single-use, so using it with `partial` means every call
builds a new context manager.

All of this relies on `reserve` being a context manager, but not every memcached library ships one,
so how would this be generalized to work with them?
We can fake a `contextmanager` behavior using
[`nullcontext`](https://docs.python.org/3/library/contextlib.html#contextlib.nullcontext).
Below is an example showing a normal function used as a context manager without the
need to decorate it with a `contextmanager` decorator.

```{.py title="Using nullcontext"}
from contextlib import nullcontext

def add(a, b):
    return a + b

add_context = nullcontext(add)

with add_context as add_func:
    print(f"Result: {add_func(1, 2)}")
```

Since `reserve` is a callable that returns a context manager we need to call it using the parenthesis `()`.<br>
And in other places these fake context managers will need to behave the same way
so we use `partial` to partially call them too with no args.

```{.py title="Using partial with nullcontext"}
from contextlib import nullcontext
from functools import partial

def add(a, b):
    return a + b

add_context = partial(nullcontext, add)

with add_context() as add_func:
    print(f"Result: {add_func(1, 2)}")
```

Put together, [`ClientPool`](https://sendapatch.se/projects/pylibmc/pooling.html) gives every thread its own client,
[`partial`](https://docs.python.org/3/library/functools.html#functools.partial)
pins the blocking mode so callers never repeat it, and
[`nullcontext`](https://docs.python.org/3/library/contextlib.html#contextlib.nullcontext)
lets libraries without a pool expose the same interface.<br>
The tradeoff is changing a single call site to use
`with self._client_context() as client:` that works for every supported memcached library.
