class NetArchitectError(Exception):
    """Base class for all project errors."""

class PhysicalDistanceViolationError(NetArchitectError):
    """Copper requested beyond 100 m."""

class AddressSpaceExhaustedError(NetArchitectError):
    """Host requests do not fit inside the root block."""

class InvalidParameterError(NetArchitectError):
    """Bad or missing input parameter."""

