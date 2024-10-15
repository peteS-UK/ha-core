"""Squeezebox Services."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import cast

from pysqueezebox import Server
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import ATTR_COMMAND
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr

# from . import SqueezeboxConfigEntry
from .const import ATTR_DEVICE_ID, ATTR_RETURN_ITEMS, ATTR_SEARCH_STRING, DOMAIN
from .coordinator import LMSStatusDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


type QueryResult = "dict[str, int | str | QueryResult | list[QueryResult]]"


@dataclass
class SqueezeboxData:
    """SqueezeboxData data class."""

    coordinator: LMSStatusDataUpdateCoordinator
    server: Server


type SqueezeboxConfigEntry = ConfigEntry[SqueezeboxData]

SERVICE_SEARCH = "search"
SERVICE_SEARCH_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_COMMAND): cv.string,
        vol.Required(ATTR_RETURN_ITEMS): int,
        vol.Optional(ATTR_SEARCH_STRING): cv.string,
    }
)


def async_get_config_entry(
    hass: HomeAssistant, device_id: str
) -> SqueezeboxConfigEntry:
    """Get the Squeezebox config entry."""

    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    # config_entry_id = device.primary_config_entry
    if not (entry := hass.config_entries.async_get_entry(device.primary_config_entry)):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="integration_not_found",
            translation_placeholders={"target": DOMAIN},
        )
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="not_loaded",
            translation_placeholders={"target": entry.title},
        )
    return cast(SqueezeboxConfigEntry, entry)


def setup_services(hass: HomeAssistant) -> None:
    """Set up the services for the Mealie integration."""

    async def async_search(call: ServiceCall) -> ServiceResponse:
        """Search LMS."""
        entry = async_get_config_entry(hass, call.data[ATTR_DEVICE_ID])
        lms = entry.runtime_data.server
        command = call.data.get(ATTR_COMMAND)
        return_items = call.data.get(ATTR_RETURN_ITEMS)
        search_string = call.data.get(ATTR_SEARCH_STRING)

        _param = [command]

        match command:
            case "albums":
                result = cast(
                    QueryResult,
                    await lms.async_query(
                        command,
                        "0",
                        str(return_items),
                        "tags:laay",
                        "search:" + search_string if search_string is not None else "",
                    ),
                )
            case "favorites":
                result = cast(
                    QueryResult,
                    await lms.async_query(
                        command,
                        "items",
                        "0",
                        str(return_items),
                        "search:" + search_string if search_string is not None else "",
                    ),
                )
            case "artists":
                result = cast(
                    QueryResult,
                    await lms.async_query(
                        command,
                        "0",
                        str(return_items),
                        "search:" + search_string if search_string is not None else "",
                    ),
                )
            case "genres":
                result = cast(
                    QueryResult,
                    await lms.async_query(
                        command,
                        "0",
                        str(return_items),
                        "search:" + search_string if search_string is not None else "",
                    ),
                )
                result = cast(
                    QueryResult,
                    await lms.async_query(
                        command,
                        "0",
                        str(return_items),
                        "tags:aglQrTy",
                        "search:" + search_string if search_string is not None else "",
                    ),
                )
                result = cast(
                    QueryResult,
                    await lms.async_query(
                        command,
                        "0",
                        str(return_items),
                        "search:" + search_string if search_string is not None else "",
                    ),
                )
            case "players":
                result = cast(
                    QueryResult, await lms.async_query(command, "0", str(return_items))
                )
            case _:
                _LOGGER.debug("Invalid Search Service Command")
                result = None

        return {"squeezebox_search": result}

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEARCH,
        async_search,
        schema=SERVICE_SEARCH_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
