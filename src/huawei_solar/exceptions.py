"""Exceptions from the Huawei Solar library."""

from typing import Any


class HuaweiSolarException(Exception):  # noqa: N818
    """Base class for Huawei Solar exceptions."""


class DeviceDetectionError(HuaweiSolarException):
    """Failed to detect the type of the connected device."""


class EncodeError(HuaweiSolarException):
    """Encoding failed."""


class TimeOfUsePeriodsException(HuaweiSolarException):
    """Validation of TOU periods failed."""


class PeakPeriodsValidationError(Exception):
    """Validation of Peak Periods failed."""


class ConnectionException(HuaweiSolarException):
    """Exception connecting to device."""


class ReadException(HuaweiSolarException):
    """Exception reading register from device."""

    def __init__(self, *args: Any, modbus_exception_code: int | None = None, **kwargs: Any) -> None:  # noqa: ANN401
        """Create ReadException."""
        super().__init__(*args, **kwargs)
        self.modbus_exception_code = modbus_exception_code


class DecodeError(ReadException):
    """Decoding failed."""


class FileCRCMismatchError(DecodeError):
    """The CRC reported by the device does not match the downloaded file.

    Carries the downloaded payload so that callers can decide whether to trust it anyway.
    """

    def __init__(self, *args: Any, file_type: int, file_data: bytes, **kwargs: Any) -> None:  # noqa: ANN401
        """Create FileCRCMismatchError."""
        super().__init__(*args, **kwargs)
        self.file_type = file_type
        self.file_data = file_data


class UnexpectedResponseContent(HuaweiSolarException):
    """The response from the device contained unexpected content."""


class ConnectionInterruptedException(HuaweiSolarException):
    """Connection to the inverter was interrupted."""


class WriteException(HuaweiSolarException):
    """Exception writing register to device."""

    def __init__(self, *args: Any, modbus_exception_code: int | None = None, **kwargs: Any) -> None:  # noqa: ANN401
        """Create WriteException."""
        super().__init__(*args, **kwargs)
        self.modbus_exception_code = modbus_exception_code


class InvalidCredentials(HuaweiSolarException):
    """Logging in on the inverter failed."""


class UnsupportedDeviceException(HuaweiSolarException):
    """No bridge class is available for this device."""
