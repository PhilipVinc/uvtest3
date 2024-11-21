import pytest
import netket as nk
import numpy as np
from netket_pro._src.operator import singlequbit_gates as sg
from jax import numpy as jnp

import netket_pro as nkp

from ..common import skipif_mpi, skipif_sharding

pytestmark = [skipif_mpi, skipif_sharding]

N = 3
hi = nk.hilbert.Spin(0.5, N, inverted_ordering=False)

operators = {}

operators["Rx"] = nkp.operator.Rx(hi, 1, 0.23)
operators["Ry"] = nkp.operator.Ry(hi, 1, 0.43)
operators["Hadamard"] = nkp.operator.Hadamard(hi, 0)


@pytest.mark.parametrize(
    "operator",
    [pytest.param(val, id=f"operator={name}") for name, val in operators.items()],
)
def test_operator_dense_and_conversion(operator):
    op_dense = operator.to_dense()
    op_local_dense = operator.to_local_operator().to_dense()

    np.testing.assert_allclose(op_dense, op_local_dense)
    assert operator.hilbert == operator.to_local_operator().hilbert


def test_get_conns():
    hi_spin = nk.hilbert.Spin(s=0.5, N=3)
    hi_qubit = nk.hilbert.Qubit(N=3)

    local_state_spin = hi_spin.local_states
    local_state_qubit = hi_qubit.local_states

    sigma_4_qubit = hi_qubit.numbers_to_states(2)
    sigma_7_qubit = hi_qubit.numbers_to_states(7)
    sigma_4_spin = hi_spin.numbers_to_states(2)
    sigma_7_spin = hi_spin.numbers_to_states(7)

    sigma_qubit = jnp.array([sigma_4_qubit, sigma_7_qubit])
    sigma_spin = jnp.array([sigma_4_spin, sigma_7_spin])

    conns_rx_qubit, _ = sg.get_conns_and_mels_Rx(sigma_qubit, 0, 0, local_state_qubit)
    conns_ry_qubit, _ = sg.get_conns_and_mels_Ry(sigma_qubit, 0, 0, local_state_qubit)
    conns_h_qubit, _ = sg.get_conns_and_mels_Hadamard(sigma_qubit, 0, local_state_qubit)

    conns_rx_spin, _ = sg.get_conns_and_mels_Rx(sigma_spin, 0, 0, local_state_spin)
    conns_ry_spin, _ = sg.get_conns_and_mels_Ry(sigma_spin, 0, 0, local_state_spin)
    conns_h_spin, _ = sg.get_conns_and_mels_Hadamard(sigma_spin, 0, local_state_spin)

    values_check_qubit = jnp.array(
        [[[0.0, 1.0, 0.0], [1.0, 1.0, 0.0]], [[1.0, 1.0, 1.0], [0.0, 1.0, 1.0]]]
    )

    values_check_spin = jnp.array(
        [[[-1.0, 1.0, -1.0], [1.0, 1.0, -1.0]], [[1.0, 1.0, 1.0], [-1.0, 1.0, 1.0]]]
    )

    assert (conns_rx_qubit == values_check_qubit).all()
    assert (conns_ry_qubit == values_check_qubit).all()
    assert (conns_h_qubit == values_check_qubit).all()
    assert (conns_rx_spin == values_check_spin).all()
    assert (conns_ry_spin == values_check_spin).all()
    assert (conns_h_spin == values_check_spin).all()
