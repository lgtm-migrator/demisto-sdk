from demisto_sdk.commands.content_graph.objects.content_item import ContentItem


class XSIAMReport(ContentItem):
    pass

    def summary(self):
        return self.dict(include=['name', 'description'])
