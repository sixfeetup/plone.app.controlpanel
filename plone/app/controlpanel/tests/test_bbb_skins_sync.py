import unittest
from zope.component import queryUtility
from plone.registry.interfaces import IRegistry

from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName

from plone.app.controlpanel.interfaces import ISkinsSchema

from plone.app.controlpanel.testing import \
    PLONE_APP_CONTROLPANEL_INTEGRATION_TESTING


class SyncPloneAppRegistryToSkinsPropertiesTest(unittest.TestCase):

    layer = PLONE_APP_CONTROLPANEL_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        ptool = getToolByName(self.portal, 'portal_properties')
        self.site_properties = ptool.site_properties
        registry = queryUtility(IRegistry)
        self.settings = registry.forInterface(ISkinsSchema)
        self.portal_skins = getToolByName(self.portal, 'portal_skins')

    def test_theme_property(self):
        self.assertEquals(self.portal_skins.default_skin, "Sunburst Theme")
        self.assertEquals(self.settings.theme, "Sunburst Theme")
        self.settings.theme = "Plone Default"
        self.assertEquals(self.portal_skins.default_skin, "Plone Default")

    def test_sync_mark_special_links_property(self):
        self.assertEquals(
            self.site_properties.mark_special_links,
            "false")
        self.assertEquals(self.settings.mark_special_links, False)
        self.settings.mark_special_links = True
        self.assertEquals(
            self.site_properties.mark_special_links,
            True)

    def test_sync_external_links_open_new_window_property(self):
        self.assertEquals(
            self.site_properties.external_links_open_new_window,
            "false")
        self.assertEquals(self.settings.ext_links_open_new_window, False)
        self.settings.ext_links_open_new_window = True
        self.assertEquals(
            self.site_properties.external_links_open_new_window,
            "true")

    def test_sync_icon_visibility_property(self):
        self.assertEquals(self.site_properties.icon_visibility, "enabled")
        self.assertEquals(self.settings.icon_visibility, "enabled")
        self.settings.icon_visibility = "disabled"
        self.assertEquals(self.site_properties.icon_visibility, "disabled")


class SyncSkinsPropertiesToPloneAppRegistryTest(unittest.TestCase):

    layer = PLONE_APP_CONTROLPANEL_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        ptool = getToolByName(self.portal, 'portal_properties')
        self.site_properties = ptool.site_properties
        registry = queryUtility(IRegistry)
        self.settings = registry.forInterface(ISkinsSchema)
        self.portal_skins = getToolByName(self.portal, 'portal_skins')

    def test_sync_theme_property(self):
        self.assertEquals(self.portal_skins.default_skin, "Sunburst Theme")
        self.assertEquals(self.settings.theme, "Sunburst Theme")
        self.portal_skins.theme = "Plone Default"
        self.assertEquals(self.settings.theme, "Plone Default")

    def test_sync_mark_special_links_property(self):
        self.assertEquals(self.site_properties.mark_special_links, 'false')
        self.assertEquals(self.settings.mark_special_links, False)
        self.site_properties.mark_special_links = True
        self.assertEquals(self.settings.mark_special_links, True)

    def test_sync_external_links_open_new_window_property(self):
        self.assertEquals(
            self.site_properties.external_links_open_new_window, 'false')
        self.assertEquals(self.settings.ext_links_open_new_window, False)
        self.site_properties.external_links_open_new_window = True
        self.assertEquals(self.settings.ext_links_open_new_window, True)

    def test_sync_icon_visibility_property(self):
        self.assertEquals(
            self.site_properties.external_links_open_new_window, 'false')
        self.assertEquals(self.settings.ext_links_open_new_window, False)
        self.site_properties.external_links_open_new_window = True
        self.assertEquals(self.settings.ext_links_open_new_window, True)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
