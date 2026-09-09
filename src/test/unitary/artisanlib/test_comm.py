"""Unit tests for artisanlib.comm after the Kaleido-only strip."""

from unittest.mock import Mock, patch

from artisanlib.comm import serialport


def test_devicefunctionlist_keep_set() -> None:
    with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
        'artisanlib.comm.platform'
    ) as mock_platform:
        mock_platform.system.return_value = 'Linux'
        ser = serialport(Mock())
        assert len(ser.devicefunctionlist) == 207
        keep = {
            18: ser.NONE,
            22: ser.piddutycycle,
            25: ser.virtual,
            50: ser.DUMMY,
            90: ser.slider_01,
            91: ser.slider_23,
            138: ser.Kaleido_BTET,
            139: ser.Kaleido_SVAT,
            140: ser.Kaleido_DrumAH,
            141: ser.Kaleido_HeaterFan,
            177: ser.pidPtermIterm,
            178: ser.pidDtermError,
        }
        for idx, fn in keep.items():
            assert ser.devicefunctionlist[idx].__func__ is fn.__func__
        assert ser.devicefunctionlist[0].__func__ is ser.DUMMY.__func__
        assert ser.devicefunctionlist[53].__func__ is ser.DUMMY.__func__


def test_dummy_returns_zeros() -> None:
    with patch('serial.Serial'), patch('artisanlib.comm.QSemaphore'), patch(
        'artisanlib.comm.platform'
    ) as mock_platform:
        mock_platform.system.return_value = 'Linux'
        aw = Mock()
        aw.qmc.timeclock.elapsedMilli.return_value = 1.5
        ser = serialport(aw)
        tx, a, b = ser.DUMMY()
        assert tx == 1.5
        assert a == 0
        assert b == 0
