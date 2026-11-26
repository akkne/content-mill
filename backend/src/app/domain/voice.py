from dataclasses import dataclass

DEFAULT_SPEED = 1.1
DEFAULT_STYLE = 0.4


@dataclass(frozen=True)
class VoiceDelivery:
    speed: float = DEFAULT_SPEED
    style: float = DEFAULT_STYLE


DEFAULT_DELIVERY = VoiceDelivery()
