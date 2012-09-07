import unittest
from plone.app.testing import setRoles
from zope.component import getAdapter
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName

from plone.app.controlpanel.testing import \
    PLONE_APP_CONTROLPANEL_INTEGRATION_TESTING

from plone.app.controlpanel.interfaces import ISkinsSchema


class SkinsControlPanelAdapterTest(unittest.TestCase):

    layer = PLONE_APP_CONTROLPANEL_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        ptool = getToolByName(self.portal, 'portal_properties')
        self.site_properties = ptool.site_properties
        self.portal_skins = getToolByName(self.portal, 'portal_skins')

    def test_adapter_lookup(self):
        self.assertTrue(getAdapter(self.portal, ISkinsSchema))

    def test_get_theme_setting(self):
        skins_settings = getAdapter(self.portal, ISkinsSchema)
        self.assertEquals(skins_settings.get_theme(), "Sunburst Theme")
        self.portal_skins.themeChanged = True
        self.portal_skins.default_skin = "Plone Default"
        self.assertEqual(skins_settings.get_theme(), "Plone Default")

    def test_set_theme_setting(self):
        skins_settings = getAdapter(self.portal, ISkinsSchema)
        self.assertEqual(skins_settings.get_theme(), "Sunburst Theme")

        skins_settings.set_theme("Plone Default")

        self.assertEqual(skins_settings.get_theme(), "Plone Default")

    def test_get_mark_special_links(self):
        pass

    def test_set_mark_special_links(self):
        pass

    def test_get_ext_links_open_new_window(self):
        pass

    def test_set_ext_links_open_new_window(self):
        pass

    def test_get_icon_visibility(self):
        pass

    def test_set_icon_visibility(self):
        pass

    def test_get_use_popups(self):
        pass

    def test_set_use_popups(self):
        pass


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
