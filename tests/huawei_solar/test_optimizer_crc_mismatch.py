"""Tests for accepting optimizer file 0x44 payloads whose device CRC does not match.

The fixtures are two consecutive reads of file 0x44 from a SUN2000-10KTL-M1 with 32 optimizers.
Both payloads are complete and decode cleanly, but the CRC the inverter returned in CompleteUpload
does not match them (see wlcrs/huawei-solar-lib#39).
"""

from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

import pytest
from huawei_solar.exceptions import DecodeError, FileCRCMismatchError
from huawei_solar.files import OptimizerRealTimeDataFile, OptimizerSystemInformationDataFile
from huawei_solar.modbus_client import AsyncHuaweiSolarClient
from huawei_solar.modbus_pdu import StartFileUpload, UploadFileFrame

from huawei_solar import register_names as rn
from huawei_solar.device import SUN2000Device
from huawei_solar.register_definitions import Result

FIXTURES = Path(__file__).parent / "fixtures"
PAYLOAD = (FIXTURES / "optimizer_file_0x44_crc_mismatch_1.bin").read_bytes()
NB_OPTIMIZERS = 32


def _mismatch(file_data: bytes, file_type: int = OptimizerRealTimeDataFile.FILE_TYPE) -> FileCRCMismatchError:
    return FileCRCMismatchError("CRC mismatch", file_type=file_type, file_data=file_data)


@pytest.fixture
def device(sun2000_device: SUN2000Device, monkeypatch: pytest.MonkeyPatch) -> SUN2000Device:
    """SUN2000 device whose register reads report 32 optimizers."""
    values: dict[rn.RegisterName, Any] = {rn.SYSTEM_TIME_RAW: 1_794_000_000, rn.NB_OPTIMIZERS: NB_OPTIMIZERS}

    async def fake_get(name: rn.RegisterName) -> Result[Any]:
        return Result(values[name], None)

    monkeypatch.setattr(sun2000_device, "get", fake_get)
    return sun2000_device


def _read_file_raising(error: Exception) -> Callable[..., Coroutine[Any, Any, bytes]]:
    async def read_file(*_args: object, **_kwargs: object) -> bytes:
        raise error

    return read_file


async def test_get_file_raises_crc_mismatch_with_payload(
    huawei_solar: AsyncHuaweiSolarClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    frame_length = 246
    frames = [PAYLOAD[i : i + frame_length] for i in range(0, len(PAYLOAD), frame_length)]
    responses: list[object] = [
        StartFileUpload(file_length=len(PAYLOAD), data_frame_length=frame_length, customised_data=b""),
        *(UploadFileFrame(frame_no=n, frame_data=f) for n, f in enumerate(frames)),
        0x0B97,
    ]

    async def fake_execute(_pdu: object) -> object:
        return responses.pop(0)

    monkeypatch.setattr(huawei_solar, "execute", fake_execute)

    with pytest.raises(FileCRCMismatchError) as exc_info:
        await huawei_solar.get_file(OptimizerRealTimeDataFile.FILE_TYPE)

    assert exc_info.value.file_type == OptimizerRealTimeDataFile.FILE_TYPE
    assert exc_info.value.file_data == PAYLOAD
    assert isinstance(exc_info.value, DecodeError)


async def test_optimizer_data_accepted_despite_crc_mismatch(
    device: SUN2000Device, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(device, "read_file", _read_file_raising(_mismatch(PAYLOAD)))

    data = await device.get_latest_optimizer_history_data()

    assert sorted(data) == list(range(1, NB_OPTIMIZERS + 1))


async def test_optimizer_data_rejected_when_count_differs(
    device: SUN2000Device, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(device, "read_file", _read_file_raising(_mismatch(PAYLOAD)))

    async def fake_get(name: rn.RegisterName) -> Result[Any]:
        return Result({rn.SYSTEM_TIME_RAW: 1_794_000_000, rn.NB_OPTIMIZERS: NB_OPTIMIZERS + 1}[name], None)

    monkeypatch.setattr(device, "get", fake_get)

    with pytest.raises(FileCRCMismatchError):
        await device.get_latest_optimizer_history_data()


async def test_optimizer_data_rejected_when_truncated(device: SUN2000Device, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(device, "read_file", _read_file_raising(_mismatch(PAYLOAD[:-100])))

    with pytest.raises(FileCRCMismatchError):
        await device.get_latest_optimizer_history_data()


async def test_system_information_file_keeps_strict_crc_check(
    device: SUN2000Device, monkeypatch: pytest.MonkeyPatch
) -> None:
    error = _mismatch(b"\x00" * 64, file_type=OptimizerSystemInformationDataFile.FILE_TYPE)
    monkeypatch.setattr(device, "read_file", _read_file_raising(error))

    with pytest.raises(FileCRCMismatchError):
        await device.get_optimizer_system_information_data()
