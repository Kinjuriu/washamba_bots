"""God's Mode: Hacked Stores 0.1.0 — Farming Score V2 plus shop overlay."""

from base_agent import agent as _parent_agent
from shop_overlay import GodModeShopOverlay


_CONTROLLER = GodModeShopOverlay(_parent_agent)


def agent(observation, configuration=None):
    return _CONTROLLER(observation, configuration)


agent.telemetry = _CONTROLLER.telemetry
