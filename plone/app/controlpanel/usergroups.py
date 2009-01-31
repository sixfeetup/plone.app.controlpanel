from zope.interface import Interface
from zope.component import adapts
from zope.formlib.form import FormFields
from zope.interface import implements
from zope.schema import Bool, Tuple

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import ISiteRoot

from plone.app.controlpanel import PloneMessageFactory as _
from plone.app.controlpanel.form import ControlPanelForm
from plone.app.controlpanel.utils import ProxyFieldProperty
from plone.app.controlpanel.utils import SchemaAdapterBase

from plone.fieldsets.fieldsets import FormFieldsets

from joinpolicyschema import UserDataWidget, IJoinPolicySchema
from security import ISecuritySchema, SecurityControlPanelAdapter


class IUserGroupsSettingsSchema(Interface):

    many_groups = Bool(title=_(u'Many groups?'),
                       description=_(u"Determines if your Plone is optimized "
                           "for small or large sites. In environments with a "
                           "lot of groups it can be very slow or impossible "
                           "to build a list all groups. This option tunes the "
                           "user interface and behaviour of Plone for this "
                           "case by allowing you to search for groups instead "
                           "of listing all of them."),
                       default=False)

    many_users = Bool(title=_(u'Many users?'),
                      description=_(u"Determines if your Plone is optimized "
                          "for small or large sites. In environments with a "
                          "lot of users it can be very slow or impossible to "
                          "build a list all users. This option tunes the user "
                          "interface and behaviour of Plone for this case by "
                          "allowing you to search for users instead of "
                          "listing all of them."),
                      default=False)


class ICombinedSchema(IUserGroupsSettingsSchema, IJoinPolicySchema): #, ISecuritySchema):
    """Combined schema for the adapter lookup.
    """

class UserGroupsSettingsControlPanelAdapter(SchemaAdapterBase):

    adapts(ISiteRoot)
    implements(ICombinedSchema)

    def __init__(self, context):
        super(UserGroupsSettingsControlPanelAdapter, self).__init__(context)
        pprop = getToolByName(context, 'portal_properties')
        self.context = pprop.site_properties

    many_groups = ProxyFieldProperty(IUserGroupsSettingsSchema['many_groups'])
    many_users = ProxyFieldProperty(IUserGroupsSettingsSchema['many_users'])


    def set_joinfields(self, value):

        self.context._updateProperty('joinfields', value)


    def get_joinfields(self):

        return self.context.getProperty('joinfields')

    joinfields = property(get_joinfields, set_joinfields)

    

joinpolicyset = FormFieldsets(IJoinPolicySchema)
joinpolicyset.id = 'joinpolicy'
joinpolicyset.label = _(u'label_joinpolicy', default=u'Join policy')

usergroupssettingsset = FormFieldsets(IUserGroupsSettingsSchema)
usergroupssettingsset.id = 'usergroupssettings'
usergroupssettingsset.label = _(u'label_usergroupssettings', default=u'Usergroupssettings')

class UserGroupsSettingsControlPanel(ControlPanelForm):

    form_fields = FormFieldsets(usergroupssettingsset, joinpolicyset)

    form_fields['joinfields'].custom_widget = UserDataWidget

    label = _("User/Groups settings")
    description = _("User and groups settings for this site.")
    form_name = _("User/Groups settings")
