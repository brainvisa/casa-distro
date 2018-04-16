import sys

if sys.version_info[0] == 3:
    string_types = (str,)

    def iteritems(d, **kw):
        return iter(d.items(**kw))
else:
    string_types = basestring,

    def iteritems(d, **kw):
        return d.iteritems(**kw)
    