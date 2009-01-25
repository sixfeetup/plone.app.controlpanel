from plone.fieldsets.fieldsets import FormFieldsets

from zope.interface import Interface
from zope.component import adapts
from zope.interface import implements
from zope.schema import Choice
from zope.schema import Tuple

from Products.CMFCore.interfaces import ISiteRoot

from plone.app.controlpanel import PloneMessageFactory as _
from plone.app.controlpanel.form import ControlPanelForm
from plone.app.controlpanel.utils import SchemaAdapterBase
from plone.app.controlpanel.widgets import AllowedTypesWidget

# For Archetypes markup

from Products.Archetypes.mimetype_utils import getDefaultContentType, \
    setDefaultContentType, getAllowedContentTypes, getAllowableContentTypes, \
    setForbiddenContentTypes

#
# Archetypes markup types
#

class ITextMarkupSchema(Interface):

    default_type = Choice(title=_(u'Default format'),
        description=_(u"Select the default format of textfields for newly "
                       "created content objects."),
        default=u'text/html',
        missing_value=set(),
        vocabulary="plone.app.vocabularies.AllowableContentTypes",
        required=True)

    allowed_types = Tuple(title=_(u'Alternative formats'),
        description=_(u"Select which formats are available for users as "
                       "alternative to the default format. Note that if new "
                       "formats are installed, they will be enabled for text "
                       "fields by default unless explicitly turned off here "
                       "or by the relevant installer."),
        required=True,
        missing_value=set(),
        value_type=Choice(
            vocabulary="plone.app.vocabularies.AllowableContentTypes"))

#
# Combined schemata and fieldsets
#

class IMarkupSchema(ITextMarkupSchema):
    """Combined schema for the adapter lookup.
    """

class MarkupControlPanelAdapter(SchemaAdapterBase):

    adapts(ISiteRoot)
    implements(IMarkupSchema)

    def __init__(self, context):
        super(MarkupControlPanelAdapter, self).__init__(context)
        self.context = context
        self.toggle_mediawiki = False

    # Text markup settings

    def get_default_type(self):
        return getDefaultContentType(self.context)

    def set_default_type(self, value):
        setDefaultContentType(self.context, value)

    default_type = property(get_default_type, set_default_type)

    def get_allowed_types(self):
        return getAllowedContentTypes(self.context)

    def set_allowed_types(self, value):
        # The menu pretends to be a whitelist, but we are storing a blacklist
        # so that new types are available by default. So, we inverse the list.
        allowable_types = getAllowableContentTypes(self.context)
        forbidden_types = [t for t in allowable_types if t not in value]
        setForbiddenContentTypes(self.context, forbidden_types)

    allowed_types = property(get_allowed_types, set_allowed_types)


textset = FormFieldsets(ITextMarkupSchema)
textset.id = 'textmarkup'
textset.label = _(u'Text markup')

class MarkupControlPanel(ControlPanelForm):

    form_fields = FormFieldsets(textset)
    form_fields['allowed_types'].custom_widget = AllowedTypesWidget

    label = _("Markup settings")
    description = _("Lets you control what markup is available when editing "
                    "content.")
    form_name = _("Markup settings")
