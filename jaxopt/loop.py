# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Loop utilities."""

import jax
import jax.numpy as jnp


def _while_loop_unrolled_jit(cond_fun, body_fun, init_val, maxiter):
  def _iter(val):
    next_val = body_fun(val)
    next_cond = cond_fun(next_val)
    return next_val, next_cond

  val = init_val
  cond = cond_fun(val)
  for _ in range(maxiter):
    # When condition is met, start doing noops.
    val, cond = jax.lax.cond(cond, _iter, lambda x: (x, False), val)
  return val


def _while_loop_unrolled_nojit(cond_fun, body_fun, init_val, maxiter):
  val = init_val
  for _ in range(maxiter):
    cond = cond_fun(val)
    if not cond:
      # When condition is met, break (not jittable).
      break
    val = body_fun(val)
  return val


def _while_loop_lax(cond_fun, body_fun, init_val, maxiter):
  def _cond_fun(_val):
    it, val = _val
    return jnp.logical_and(cond_fun(val), it <= maxiter - 1)

  def _body_fun(_val):
    it, val = _val
    val = body_fun(val)
    return it+1, val

  return jax.lax.while_loop(_cond_fun, _body_fun, (0, init_val))[1]


def while_loop(cond_fun, body_fun, init_val, maxiter, unroll=False, jit=False):
  """A while loop with a bounded number of iterations."""

  if unroll:
    if jit:
      fun = _while_loop_unrolled_jit
    else:
      fun = _while_loop_unrolled_nojit
  else:
    if jit:
      fun = _while_loop_lax
    else:
      raise ValueError("unroll=False and jit=False cannot be used together")

  if jit:
    fun = jax.jit(fun, static_argnums=(0, 1, 3))

  return fun(cond_fun, body_fun, init_val, maxiter)