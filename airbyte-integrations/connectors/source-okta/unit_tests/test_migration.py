#
# Copyright (c) 2024 Airbyte, Inc., all rights reserved.
#

import json
from typing import Any, Mapping
import logging
from enum import Enum

from airbyte_cdk.models import OrchestratorType, Type
from airbyte_cdk.sources import Source
from source_okta.config_migration import OktaConfigMigration
from source_okta.source import SourceOkta

CMD = "check"
SOURCE: Source = SourceOkta()

logger = logging.getLogger("airbyte")


def load_config(config_path: str) -> Mapping[str, Any]:
    with open(config_path, "r") as config:
        return json.load(config)
    
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value  # Encode enums as their values
        return super().default(obj)


class TestMigrateConfig:
    test_not_migrated_config_path = "unit_tests/migration_configs/not_migrated_config.json"
    test_migrated_config_path = "unit_tests/migration_configs/migrated_config.json"
    test_migrated_config_env_path = "unit_tests/migration_configs/migrated_config_env.json"

    def test_migrate_config(self, capsys):
        config = load_config(self.test_not_migrated_config_path)
        assert "domain" not in config
        migration_instance = OktaConfigMigration()
        migration_instance.migrate([CMD, "--config", self.test_not_migrated_config_path], SOURCE)
        captured = capsys.readouterr()
        control_msg = json.loads(captured.out.strip())
        assert control_msg["type"] == Type.CONTROL.value
        assert control_msg["control"]["type"] == OrchestratorType.CONNECTOR_CONFIG.value
        migrated_config = control_msg["control"]["connectorConfig"]["config"]
        assert migrated_config["domain"] == "myorg"
        assert migrated_config["credentials"]["auth_type"] == "api_token"

    def test_should_not_migrate(self):
        config = load_config(self.test_migrated_config_path)
        assert config["domain"]
        migration_instance = OktaConfigMigration()
        assert not migration_instance.should_migrate(config)

    def test_should_not_migrate_env(self):
        config = load_config(self.test_migrated_config_env_path)
        assert config["domain"]
        assert config["environment_domain"]
        migration_instance = OktaConfigMigration()
        assert not migration_instance.should_migrate(config)
