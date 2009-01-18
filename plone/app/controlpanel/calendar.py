from zope.interface import Interface
from zope.component import adapts
from zope.formlib.form import FormFields
from zope.interface import implements
from zope.schema import Choice
from zope.schema import Int
from zope.schema import Tuple

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot

from plone.app.controlpanel import PloneMessageFactory as _
from plone.app.controlpanel.form import ControlPanelForm
from plone.app.controlpanel.utils import ProxyFieldProperty
from plone.app.controlpanel.utils import SchemaAdapterBase
from plone.app.controlpanel.widgets import MultiCheckBoxVocabularyWidget
from plone.app.controlpanel.widgets import WeekdayWidget


class ICalendarSchema(Interface):

    firstweekday = Int(title=_(u'First day of week in the calendar'),
                       default=0,
                       required=True)

    calendar_states = Tuple(title=_(u'Workflow states to show in the calendar'),
                            required=True,
                            missing_value=set(),
                            value_type=Choice(
                                vocabulary="plone.app.vocabularies.WorkflowStates"))


class CalendarControlPanelAdapter(SchemaAdapterBase):
    adapts(IPloneSiteRoot)
    implements(ICalendarSchema)

    def __init__(self, context):
        super(CalendarControlPanelAdapter, self).__init__(context)
        self.context = getToolByName(context, 'portal_calendar')

    firstweekday = ProxyFieldProperty(ICalendarSchema['firstweekday'])
    calendar_states = ProxyFieldProperty(ICalendarSchema['calendar_states'])


class CalendarControlPanel(ControlPanelForm):

    form_fields = FormFields(ICalendarSchema)
    form_fields['firstweekday'].custom_widget = WeekdayWidget
    form_fields['calendar_states'].custom_widget = MultiCheckBoxVocabularyWidget

    label = _("Calendar settings")
    description = None
    form_name = _("Calendar settings")
