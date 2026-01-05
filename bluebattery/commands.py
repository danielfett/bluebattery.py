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
    ha_details: Optional[Dict] = None  # details for Home Assistant integration

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
    output_id: str  # note: may contain placeholders for output field values
    fields: List[BBValue]
    postprocess: Optional[Callable] = None
    preprocess: Optional[Callable] = None
    ha_name_postfix: Optional[str] = None  # optional postfix for HA entity names

    def format(self):
        return BYTE_ORDER + "".join(field.get_struct() for field in self.fields)

    def process(self, characteristic, value):

        non_ignore_fields = filter(
            lambda field: type(field) is not BBValueIgnore, self.fields
        )

        # field values, raw from the struct unpacking
        raw_values = zip(non_ignore_fields, struct.unpack_from(self.format(), value))

        if self.preprocess:
            raw_values = self.preprocess(raw_values)

        """
        Frames with multiple sub-frames may contain the same field name twice. Once
        the same field name has been observed twice, we emit a sub-frame result and
        continue with the rest of the frame.
        """
        output = {}

        for field, raw_value in raw_values:
            # existing field name indicates: begin of new sub-frame! emit old frame first
            if field.output_id in output:
                if self.postprocess:
                    self.postprocess(characteristic, output)
                yield (self, self.output_id.format(**output), output)
            # existing field value will be overwritten as necessary
            output[field.output_id] = field.value(raw_value)

        if self.postprocess:
            self.postprocess(characteristic, output)
        yield (self, self.output_id.format(**output), output)


@dataclass
class BBFrameTypeSwitch:
    index_byte: str
    frame_types: Dict[Tuple[int, ...], BBFrame]

    def process(self, characteristic, value):
        index_value = struct.unpack_from(BYTE_ORDER + self.index_byte, value)
        if index_value not in self.frame_types:
            raise Exception(f"Frame type not found: {index_value!r}")
        log.debug(f"Selected index: {index_value}.")

        yield from self.frame_types[index_value].process(characteristic, value)
