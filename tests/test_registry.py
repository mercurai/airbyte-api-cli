"""Tests for the plugin registry."""

import unittest

from airbyte_api_cli.core.registry import Registry, PluginInfo


class TestRegistry(unittest.TestCase):
    def setUp(self):
        # Reset singleton before each test
        Registry.reset()

    def test_instance_returns_singleton(self):
        r1 = Registry.instance()
        r2 = Registry.instance()
        self.assertIs(r1, r2)

    def test_register_plugin(self):
        registry = Registry.instance()

        def my_setup(subparsers, ctx):
            pass

        registry.register("sources", my_setup)
        plugin = registry.get_plugin("sources")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "sources")

    def test_get_missing_plugin_returns_none(self):
        registry = Registry.instance()
        self.assertIsNone(registry.get_plugin("nonexistent"))

    def test_all_plugins_returns_all(self):
        registry = Registry.instance()

        def fn_a(sp, ctx): pass
        def fn_b(sp, ctx): pass

        registry.register("sources", fn_a)
        registry.register("destinations", fn_b)
        plugins = registry.all_plugins()
        self.assertIn("sources", plugins)
        self.assertIn("destinations", plugins)
        self.assertEqual(len(plugins), 2)

    def test_register_overwrites_existing(self):
        registry = Registry.instance()

        def fn_old(sp, ctx): pass
        def fn_new(sp, ctx): pass

        registry.register("sources", fn_old)
        registry.register("sources", fn_new)
        plugin = registry.get_plugin("sources")
        self.assertIs(plugin.setup_fn, fn_new)

    def test_setup_subparsers_calls_all_setup_fns(self):
        registry = Registry.instance()
        called = []

        def fn_a(sp, ctx):
            called.append("a")

        def fn_b(sp, ctx):
            called.append("b")

        registry.register("plugin_a", fn_a)
        registry.register("plugin_b", fn_b)
        registry.setup_subparsers(None, {})
        self.assertIn("a", called)
        self.assertIn("b", called)

    def test_all_plugins_returns_copy(self):
        registry = Registry.instance()
        registry.register("sources", lambda sp, ctx: None)
        plugins = registry.all_plugins()
        plugins["injected"] = PluginInfo(name="injected", setup_fn=lambda sp, ctx: None)
        self.assertNotIn("injected", registry.all_plugins())


if __name__ == "__main__":
    unittest.main()
