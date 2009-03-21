from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.controlpanel.form import ControlPanelView


class AddonControlPanel(ControlPanelView):

    template = ViewPageTemplateFile('addon.pt')

    def __call__(self):
        return self.template()
