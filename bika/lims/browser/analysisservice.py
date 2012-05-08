from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bika.lims import bikaMessageFactory as _
from bika.lims.content.analysisservice import getContainers
from bika.lims.browser.bika_listing import BikaListingView
from Products.CMFCore.utils import getToolByName
import json, plone
import plone.protect
from magnitude import mg, MagnitudeError
import re

### AJAX methods for AnalysisService context

# ajax Preservaition/Container widget filter
# in preservationwidget rows,we get st_uid, pres_uid and minvol.
# in Service Setup context, all we get is [pres_uid,]

class ajaxGetContainers(BrowserView):
    def __call__(self):
        plone.protect.CheckAuthenticator(self.request)
        uc = getToolByName(self, 'uid_catalog')
        st_uid = self.request.get('st_uid', [])
        st = st_uid and uc(UID=st_uid)[0].getObject() or None
        allow_blank = self.request.get('allow_blank', False) == 'true'
        pres_uid = json.loads(self.request.get('pres_uid', '[]'))
        minvol = self.request.get('minvol', '').split(" ")
        try:
            minvol = mg(float(minvol[0]), " ".join(minvol[1:]))
        except:
            minvol = mg(0)

        if not type(pres_uid) in (list, tuple):
            pres_uid = [pres_uid,]
        preservations = [p and uc(UID=p)[0].getObject() or '' for p in pres_uid]

        containers = getContainers(self.context,
                                   preservation = preservations and preservations or [],
                                   minvol = minvol,
                                   allow_blank = allow_blank)

        return json.dumps(containers)


class ajaxServicePopup(BrowserView):

    template = ViewPageTemplateFile("templates/analysisservice_popup.pt")

    def __init__(self, context, request):
        super(ajaxServicePopup, self).__init__(context, request)
        self.icon = "++resource++bika.lims.images/analysisservice_big.png"

    def __call__(self):
        plone.protect.CheckAuthenticator(self.request)
        bsc = getToolByName(self.context, 'bika_setup_catalog')

        service_title = self.request.get('service_title', '').strip()
        if not service_title:
            return ''

        brains = bsc(portal_type="AnalysisService", Title=service_title)
        if not brains:
            return ''

        self.service = brains[0].getObject()

        self.calc = self.service.getCalculation()

        self.partsetup = self.service.getPartitionSetup()

        # convert uids to comma-separated list of display titles
        for i,ps in enumerate(self.partsetup):

            self.partsetup[i]['separate'] = \
                ps.has_key('separate') and _('Yes') or _('No')

            if type(ps['sampletype']) == str:
                ps['sampletype'] = [ps['sampletype'],]
            sampletypes = []
            for st in ps['sampletype']:
                res = bsc(UID=st)
                sampletypes.append(res and res[0].Title or st)
            self.partsetup[i]['sampletype'] = ", ".join(sampletypes)

            if ps.has_key('container'):
                if type(ps['container']) == str:
                    ps['container'] = [ps['container'],]
                containers = [bsc(UID=c)[0].Title for c in ps['container']]
                self.partsetup[i]['container'] = ", ".join(containers)
            else:
                self.partsetup[i]['container'] = ''

            if ps.has_key('preservation'):
                if type(ps['preservation']) == str:
                    ps['preservation'] = [ps['preservation'],]
                preservations = [bsc(UID=p)[0].Title for p in ps['preservation']]
                self.partsetup[i]['preservation'] = ", ".join(preservations)
            else:
                self.partsetup[i]['container'] = ''

        return self.template()

