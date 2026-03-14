"""Plugin auto-discovery. Imports all plugin packages to trigger registration."""

from airbyte_api_cli.plugins import applications  # noqa: F401
from airbyte_api_cli.plugins import config_cmd  # noqa: F401
from airbyte_api_cli.plugins import connections  # noqa: F401
from airbyte_api_cli.plugins import destinations  # noqa: F401
from airbyte_api_cli.plugins import health  # noqa: F401
from airbyte_api_cli.plugins import jobs  # noqa: F401
from airbyte_api_cli.plugins import sources  # noqa: F401
from airbyte_api_cli.plugins import tags  # noqa: F401
from airbyte_api_cli.plugins import workspaces  # noqa: F401
from airbyte_api_cli.plugins import streams  # noqa: F401
from airbyte_api_cli.plugins import permissions  # noqa: F401
from airbyte_api_cli.plugins import organizations  # noqa: F401
from airbyte_api_cli.plugins import users  # noqa: F401
from airbyte_api_cli.plugins import source_definitions  # noqa: F401
from airbyte_api_cli.plugins import destination_definitions  # noqa: F401
from airbyte_api_cli.plugins import declarative_source_definitions  # noqa: F401
from airbyte_api_cli.plugins import builder_projects  # noqa: F401
from airbyte_api_cli.plugins import check_connection  # noqa: F401
from airbyte_api_cli.plugins import discover_schema  # noqa: F401
from airbyte_api_cli.plugins import state  # noqa: F401
from airbyte_api_cli.plugins import attempt_info  # noqa: F401
from airbyte_api_cli.plugins import definition_specifications  # noqa: F401
from airbyte_api_cli.plugins import web_backend  # noqa: F401
from airbyte_api_cli.plugins import operations  # noqa: F401
from airbyte_api_cli.plugins import notifications  # noqa: F401
