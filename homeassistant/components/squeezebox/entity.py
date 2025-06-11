"""Base class for Squeezebox Sensor entities."""

from collections.abc import Awaitable, Callable, Coroutine
from functools import wraps
from typing import Any

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import (
    CONNECTION_NETWORK_MAC,
    DeviceInfo,
    format_mac,
)
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATUS_QUERY_UUID
from .coordinator import (
    LMSStatusDataUpdateCoordinator,
    SqueezeBoxPlayerUpdateCoordinator,
)


class SqueezeboxEntity(CoordinatorEntity[SqueezeBoxPlayerUpdateCoordinator]):
    """Base entity class for Squeezebox entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SqueezeBoxPlayerUpdateCoordinator) -> None:
        """Initialize the SqueezeBox entity."""
        super().__init__(coordinator)
        self._player = coordinator.player
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, format_mac(self._player.player_id))},
            name=self._player.name,
            connections={(CONNECTION_NETWORK_MAC, format_mac(self._player.player_id))},
            via_device=(DOMAIN, coordinator.server_uuid),
            model=self._player.model,
            manufacturer=self._player.creator,
        )


class LMSStatusEntity(CoordinatorEntity[LMSStatusDataUpdateCoordinator]):
    """Defines a base status sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LMSStatusDataUpdateCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize status sensor entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_translation_key = description.key.replace(" ", "_")
        self._attr_unique_id = (
            f"{coordinator.data[STATUS_QUERY_UUID]}_{description.key}"
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.data[STATUS_QUERY_UUID])},
        )


type _FuncType[**_P, _R] = Callable[_P, Awaitable[_R]]
type _ReturnFuncType[**_P, _R] = Callable[_P, Coroutine[Any, Any, _R]]


def catch_action_error[**_P, _R](
    action: str,
) -> Callable[[_FuncType[_P, _R]], _ReturnFuncType[_P, _R]]:
    """Return decorator that catches errors and raises HomeAssistantError."""

    def decorator(func: _FuncType[_P, _R]) -> _ReturnFuncType[_P, _R]:
        @wraps(func)
        async def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            try:
                return await func(*args, **kwargs)
            except Exception as ex:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="action_error",
                    translation_placeholders={"action": action, "error": str(ex)},
                ) from ex

        return wrapper

    return decorator
