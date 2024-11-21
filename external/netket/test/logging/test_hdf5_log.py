import pytest

import glob

import numpy as np
import jax
from jax.nn.initializers import normal
from jax import numpy as jnp

import netket as nk
import netket.experimental as nkx

from .. import common


@pytest.fixture()
def vstate(request):
    N = 8
    hi = nk.hilbert.Spin(1 / 2, N)

    ma = nk.models.RBM(
        alpha=1,
        param_dtype=float,
        hidden_bias_init=normal(),
        visible_bias_init=normal(),
    )

    return nk.vqs.MCState(
        nk.sampler.MetropolisLocal(hi),
        ma,
    )


@common.skipif_distributed
def test_hdf5log(vstate, tmp_path):
    # skip test if hdf5py not installed
    h5py = pytest.importorskip("h5py")

    path = str(tmp_path) + "/dir1/dir2"

    log = nkx.logging.HDF5Log(path + "/output")

    for i in range(30):
        log(i, {"Energy": jnp.array(1.0), "complex": jnp.array(1.0 + 1j)}, vstate)

    log.flush()
    del log

    files = glob.glob(path + "/*")
    assert len(files) >= 1

    f = h5py.File(files[0], "r")
    energy = np.array(f["data/Energy/value"])
    complex = np.array(f["data/complex/value"])
    params = np.array(f["variational_state/parameters/Dense/kernel"])
    iters = np.array(f["variational_state/iter"])
    assert energy.shape[0] == 30
    assert complex.shape[0] == 30
    assert params.shape[0] == 30
    assert iters.shape[0] == 30


@common.skipif_distributed
def test_lazy_init(tmp_path):
    # skip test if hdf5py not installed
    pytest.importorskip("h5py")

    path = str(tmp_path) + "/dir1"

    nkx.logging.HDF5Log(path)

    files = glob.glob(path + "/*")
    assert len(files) == 0


@common.onlyif_distributed
def test_write_only_on_master(vstate, tmp_path):
    # Check that the logger runs everywhere but serializes only on rank 0
    # skip test if tensorboardX not installed
    pytest.importorskip("h5py")

    if nk.config.netket_experimental_sharding:
        rank = jax.process_index()
    else:
        rank = nk.utils.mpi.rank

    path = str(tmp_path) + "/dir1/r{rank}"

    log = nkx.logging.HDF5Log(path + "/output")

    for i in range(30):
        log(i, {"Energy": jnp.array(1.0), "complex": jnp.array(1.0 + 1j)}, vstate)

    log.flush()
    del log

    files = glob.glob(path + "/*")
    if rank == 0:
        assert len(files) >= 1
    else:
        assert len(files) == 0
