import logging
import struct
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple, Union

BYTE_ORDER = ">"  # > big-endian, < little-endian


log = logging.getLogger("Commands")


@dataclass
class BBValue:
    """
    Represents a value within a bluetooth bytestream (reading or writing).

    The byte representation is defined in python's struct format.

    Additionally implements ¾ as a special struct character for 24-bit signed
    integers; works only on the leftmost place in the string.
    """

    struct: str
    output_id: str
    conversion_fn: Optional[Callable] = None

    def value(self, raw_value: Union[bytes, int, float]) -> Union[int, float, str]:
        """Converts a raw_value resulting from unpacking a struct into a value usable for an application.

        Args:
            raw_value (Union[bytes, int, float]): Result of struct.unpack

        Returns:
            Union[int, float, str]: Parsed value
        """
        if self.struct == "¾":
            assert isinstance(raw_value, bytes)
            raw_value_unsigned = struct.unpack(">I", b"\x00" + raw_value)[0]
            raw_value = (
                raw_value_unsigned
                if not (raw_value_unsigned & 0x800000)
                else raw_value_unsigned - 0x1000000
            )
        if not self.conversion_fn:
            assert not isinstance(raw_value, bytes)
            return raw_value
        else:
            return self.conversion_fn(raw_value)

    def get_struct(self):
        if not self.struct == "¾":
            return self.struct
        return "3s"


class BBValueIgnore(BBValue):
    def __init__(self, byte_count: int = 1):
        self.struct = f"{byte_count}x"
        self.output_id = ""

    def value(self, raw_value):
        return None


@dataclass
class BBFrame:
    output_id: str
    fields: List[BBValue]

    def format(self):
        return BYTE_ORDER + "".join(field.get_struct() for field in self.fields)

    def process(self, value):
        non_ignore_fields = filter(
            lambda field: type(field) is not BBValueIgnore, self.fields
        )
        return (
            self.output_id,
            {
                field.output_id: field.value(raw_value)
                for field, raw_value in zip(
                    non_ignore_fields, struct.unpack_from(self.format(), value)
                )
            },
        )


@dataclass
class BBFrameTypeSwitch:
    index_byte: str
    frame_types: Dict[Tuple[int, ...], BBFrame]

    def process(self, value):
        index_value = struct.unpack_from(BYTE_ORDER + self.index_byte, value)
        if index_value not in self.frame_types:
            raise Exception(f"Frame type not found: {index_value!r}")
        log.debug(f"Selected index: {index_value}.")

        return self.frame_types[index_value].process(value)
