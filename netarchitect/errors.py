class NetArchitectError(Exception):
    """Base class so the CLI can catch everything cleanly."""

class PhysicalDistanceViolationError(NetArchitectError): pass
class AddressSpaceExhaustedError(NetArchitectError): pass
class InvalidParameterError(NetArchitectError): pass